import datetime
import json
import logging
import os
from typing import Any, Iterable, List
from urllib.parse import quote

import azure.functions as func
import requests
from azure.identity import DefaultAzureCredential


app = func.FunctionApp()


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required configuration: {name}")
    return value


def scout_headers() -> dict:
    return {
        "Authorization": f"Token: {get_env('SCOUT_API_KEY')}",
        "Accept": "application/json",
    }


def scout_get(path: str, params: dict | None = None) -> Any:
    base_url = get_env("SCOUT_BASE_URL", "https://scout.cymru.com/api").rstrip("/")
    url = f"{base_url}{path}"
    response = requests.get(url, headers=scout_headers(), params=params or {}, timeout=120)
    logging.info("Scout API request: %s status=%s", url, response.status_code)
    if response.status_code >= 400:
        raise RuntimeError(f"Scout API request failed: {response.status_code} - {response.text}")
    return response.json()


def dcr_token() -> str:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://monitor.azure.com/.default")
    return token.token


def ingest_custom_table(table_name: str, records: List[dict]) -> None:
    if not records:
        logging.info("No records to ingest for %s", table_name)
        return

    dce_uri = get_env("DCE_URI")
    dcr_id = get_env("DCR_IMMUTABLE_ID")
    stream_name = f"Custom-{table_name}_CL"
    url = f"{dce_uri.rstrip('/')}/dataCollectionRules/{dcr_id}/streams/{stream_name}?api-version=2023-01-01"

    payload = []
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for record in records:
        row = dict(record)
        row.setdefault("TimeGenerated", now)
        payload.append(row)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {dcr_token()}",
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=180)
    logging.info("Ingested %s records to %s status=%s", len(payload), table_name, response.status_code)
    if response.status_code >= 400:
        raise RuntimeError(f"Log Analytics ingestion failed: {response.status_code} - {response.text}")


def strip_none(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [strip_none(v) for v in obj]
    return obj


def normalize_usage(response: dict) -> List[dict]:
    row = dict(response)
    row["TimeGenerated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return [strip_none(row)]


def normalize_search(response: dict, query: str) -> List[dict]:
    rows: List[dict] = []
    for item in response.get("ips", []):
        row = dict(item)
        row["query"] = query
        row["start_date"] = response.get("start_date")
        row["end_date"] = response.get("end_date")
        row["TimeGenerated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append(strip_none(row))
    return rows


def normalize_ip_details(details: dict) -> List[dict]:
    row = dict(details)
    row["TimeGenerated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return [strip_none(row)]


def normalize_foundation(response: dict) -> List[dict]:
    rows: List[dict] = []
    for item in response.get("data", []):
        row = dict(item)
        row["TimeGenerated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append(strip_none(row))
    return rows


@app.schedule(schedule="0 * * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def scout_poll(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.info("Scanner timer is past due; continuing.")

    query = get_env("SCOUT_QUERY", "ip=93.184.216.34")
    lookback_days = int(get_env("SCOUT_LOOKBACK_DAYS", "30"))
    max_ip_details = int(get_env("MAX_IP_DETAILS_PER_RUN", "10"))

    end_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    usage_response = scout_get("/scout/usage")
    ingest_custom_table("TeamCymruScoutUsage", normalize_usage(usage_response))

    search_response = scout_get(
        "/scout/search",
        params={
            "query": query,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
    search_rows = normalize_search(search_response, query)
    ingest_custom_table("TeamCymruScoutSearch", search_rows)

    detail_rows: List[dict] = []
    foundation_ips: List[str] = []
    for item in search_response.get("ips", [])[:max_ip_details]:
        ip_value = item.get("ip")
        if not ip_value:
            continue
        foundation_ips.append(ip_value)
        details = scout_get(f"/scout/ip/{quote(ip_value, safe='')}/details", params={
            "start_date": start_date,
            "end_date": end_date,
        })
        detail_rows.extend(normalize_ip_details(details))

    ingest_custom_table("TeamCymruScoutIPDetails", detail_rows)

    if foundation_ips:
        foundation_response = scout_get("/scout/ip/foundation", params={
            "ips": ",".join(foundation_ips),
            "start_date": start_date,
            "end_date": end_date,
        })
        ingest_custom_table("TeamCymruScoutFoundation", normalize_foundation(foundation_response))

    logging.info("Team Cymru Scout poll completed successfully.")
