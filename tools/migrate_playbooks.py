"""
Migrate Logic App playbook ARM templates from the deprecated
Azure Log Analytics Data Collector API to the Logs Ingestion API.

For each playbook:
1. Add DCE/DCR parameters for the Logs Ingestion API
2. Enable managed identity on the Logic App
3. Replace Azureloganalyticsdatacollector ApiConnection actions with Http actions
4. Remove the deprecated connection variable, resource, and parameter wiring
5. Update metadata and post-deployment instructions
"""

import json
import copy
import sys
import os


def migrate_playbook(template):
    t = copy.deepcopy(template)

    add_ingestion_parameters(t)
    remove_datacollector_variable(t)
    migrate_logic_app_resource(t)
    remove_datacollector_connection_resource(t)
    update_metadata(t)

    return t


def add_ingestion_parameters(t):
    params = t.setdefault("parameters", {})
    params["DataCollectionEndpoint"] = {
        "type": "string",
        "minLength": 1,
        "metadata": {
            "description": "The Data Collection Endpoint URI for the Logs Ingestion API (e.g. https://my-dce.eastus-1.ingest.monitor.azure.com)."
        }
    }
    params["DcrImmutableId"] = {
        "type": "string",
        "minLength": 1,
        "metadata": {
            "description": "The immutable ID of the Data Collection Rule (e.g. dcr-abc123def456)."
        }
    }


def remove_datacollector_variable(t):
    variables = t.get("variables", {})
    keys_to_remove = [
        k for k in variables
        if "loganalyticsdatacollector" in k.lower()
    ]
    for k in keys_to_remove:
        del variables[k]


def migrate_logic_app_resource(t):
    for resource in t.get("resources", []):
        if resource.get("type") == "Microsoft.Logic/workflows":
            enable_managed_identity(resource)
            migrate_definition(resource)
            remove_datacollector_from_connection_params(resource)


def enable_managed_identity(resource):
    resource["identity"] = {"type": "SystemAssigned"}


def migrate_definition(resource):
    definition = resource.get("properties", {}).get("definition", {})
    actions = definition.get("actions", {})

    add_ingestion_params_to_definition(definition)

    walk_and_migrate_actions(actions)


def add_ingestion_params_to_definition(definition):
    params = definition.get("parameters", {})
    params["dataCollectionEndpoint"] = {
        "defaultValue": "",
        "type": "String"
    }
    params["dcrImmutableId"] = {
        "defaultValue": "",
        "type": "String"
    }


def walk_and_migrate_actions(actions):
    if not isinstance(actions, dict):
        return

    keys = list(actions.keys())
    for key in keys:
        action = actions[key]
        if is_datacollector_action(action):
            actions[key] = convert_to_http_action(action)
        else:
            for sub_key in ("actions", "else"):
                sub = action.get(sub_key)
                if isinstance(sub, dict) and not is_logic_action(sub):
                    walk_and_migrate_actions(sub)
                elif isinstance(sub, dict) and "actions" in sub:
                    walk_and_migrate_actions(sub.get("actions", {}))

            if "cases" in action:
                for case_val in action["cases"].values():
                    walk_and_migrate_actions(case_val.get("actions", {}))

            if "foreach" in action or "type" in action:
                sub_actions = action.get("actions")
                if isinstance(sub_actions, dict):
                    walk_and_migrate_actions(sub_actions)


def is_logic_action(obj):
    return isinstance(obj, dict) and "type" in obj and "inputs" in obj


def is_datacollector_action(action):
    if not isinstance(action, dict):
        return False
    if action.get("type") != "ApiConnection":
        return False
    inputs = action.get("inputs", {})
    host = inputs.get("host", {})
    conn = host.get("connection", {})
    conn_name = conn.get("name", "")
    return "azureloganalyticsdatacollector" in conn_name.lower()


def convert_to_http_action(action):
    inputs = action.get("inputs", {})
    body_expr = inputs.get("body", "")
    log_type = inputs.get("headers", {}).get("Log-Type", "")

    stream_expr = build_stream_expression(log_type)

    new_action = {
        "type": "Http",
        "inputs": {
            "method": "POST",
            "uri": "@{concat("
                    "parameters('dataCollectionEndpoint'), "
                    "'/dataCollectionRules/', "
                    "parameters('dcrImmutableId'), "
                    f"'/streams/{stream_expr}"
                    "?api-version=2023-01-01')}",
            "body": ensure_array_body(body_expr),
            "headers": {
                "Content-Type": "application/json"
            },
            "authentication": {
                "type": "ManagedServiceIdentity",
                "audience": "https://monitor.azure.com"
            }
        }
    }

    if "runAfter" in action:
        new_action["runAfter"] = action["runAfter"]
    if "description" in action:
        new_action["description"] = action["description"]

    return new_action


def build_stream_expression(log_type_expr):
    if log_type_expr.startswith("@variables("):
        var_ref = log_type_expr.replace("@", "")
        return f"Custom-@{{{var_ref}}}_CL"
    elif log_type_expr.startswith("@"):
        return f"Custom-{log_type_expr}_CL"
    else:
        return f"Custom-{log_type_expr}_CL"


def ensure_array_body(body_expr):
    if not body_expr:
        return body_expr
    return f"@{{if(equals(first(string({strip_at(body_expr)})), '['), {strip_at(body_expr)}, createArray({strip_at(body_expr)}))}}"


def strip_at(expr):
    if isinstance(expr, str) and expr.startswith("@{") and expr.endswith("}"):
        return expr[2:-1]
    if isinstance(expr, str) and expr.startswith("@"):
        return expr[1:]
    return expr


def remove_datacollector_from_connection_params(resource):
    props = resource.get("properties", {})

    connections_val = props.get("parameters", {}).get("$connections", {}).get("value", {})
    keys_to_remove = [
        k for k in connections_val
        if "loganalyticsdatacollector" in k.lower()
    ]
    for k in keys_to_remove:
        del connections_val[k]

    props["parameters"] = props.get("parameters", {})
    props["parameters"]["dataCollectionEndpoint"] = {
        "value": "[parameters('DataCollectionEndpoint')]"
    }
    props["parameters"]["dcrImmutableId"] = {
        "value": "[parameters('DcrImmutableId')]"
    }


def remove_datacollector_connection_resource(t):
    resources = t.get("resources", [])
    t["resources"] = [
        r for r in resources
        if not (
            r.get("type") == "Microsoft.Web/connections"
            and "loganalyticsdatacollector" in r.get("name", "").lower()
        )
    ]


def update_metadata(t):
    metadata = t.get("metadata", {})

    new_post_deploy = [
        "**a. Configure Data Collection Resources**",
        "1. Create a Data Collection Endpoint (DCE) in your Azure subscription.",
        "2. Create a Data Collection Rule (DCR) with custom table streams for each table used by this playbook.",
        "3. Assign the 'Monitoring Metrics Publisher' role to the Logic App's managed identity on the DCR.",
        "",
        "**b. Authorize connections**",
        "Once deployment is complete, authorize each remaining connection.",
        "1. Go to your logic app -> API connections -> Select the azuremonitorlogs connection resource",
        "2. Go to General -> Edit API connection",
        "3. Click Authorize",
        "4. Sign in",
        "5. Click Save",
        "6. Repeat steps for other connections (Sentinel, Outlook if applicable)"
    ]
    metadata["postDeployment"] = new_post_deploy

    prereqs = metadata.get("prerequisites", [])
    prereqs.append(
        "A Data Collection Endpoint (DCE) and Data Collection Rule (DCR) "
        "configured for the Logs Ingestion API. See: "
        "https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-ingestion-api-overview"
    )
    metadata["prerequisites"] = prereqs


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.json> <output.json>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r") as f:
        template = json.load(f)

    migrated = migrate_playbook(template)

    with open(output_path, "w") as f:
        json.dump(migrated, f, indent=4)

    print(f"Migrated: {input_path} -> {output_path}")


if __name__ == "__main__":
    main()
