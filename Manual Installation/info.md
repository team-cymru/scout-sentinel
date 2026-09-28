Download the 3.1.2 ZIP File in the [Installation Package Folder](https://github.com/team-cymru/scout-sentinel/tree/main/Manual%20Installation/Installation%20Package) to manually deploy the Scout Sentinel Integration.
<br>
<br>
Refer to our [Documentation](https://github.com/team-cymru/scout-sentinel/tree/main/Documentation) for both manual installation steps and installation via the Azure Marketplace.

## Upgrading to 3.1.2

Version 3.1.2 moves the `TeamCymruScoutLiveInvestigation` and `TeamCymruScoutEnrichIncident` playbooks from the retired HTTP Data Collector API to the [Logs Ingestion API](https://learn.microsoft.com/azure/azure-monitor/logs/logs-ingestion-api-overview). The deployment template creates the data collection endpoint, data collection rule, destination tables and role assignment the playbooks need, so a new installation requires no extra setup.

**Existing workspaces only.** Tables created by an earlier version are *classic* tables. Convert them once per workspace before the updated playbooks run, otherwise ingestion fails:

```bash
resourceGroup="<resource-group>"
workspace="<workspace-name>"

# List the classic tables still present in the workspace
az monitor log-analytics workspace table list \
  --resource-group "$resourceGroup" --workspace-name "$workspace" \
  --query "[?schema.tableSubType=='Classic'].{Name:name}" -o table

# Convert each one, using the table name exactly as returned above
# (it already includes the _CL suffix; do not append _CL again)
az monitor log-analytics workspace table migrate \
  --resource-group "$resourceGroup" --workspace-name "$workspace" \
  --table-name "<TableName>"
```

> **The conversion cannot be undone.** It is a one-way operation per table.

Each playbook's README in the [Azure Sentinel repository](https://github.com/Azure/Azure-Sentinel/tree/master/Solutions/Team%20Cymru%20Scout/Playbooks) lists the tables it writes.
