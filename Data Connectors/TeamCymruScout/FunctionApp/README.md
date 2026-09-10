# Team Cymru Scout Azure Function Connector

This function app is a Microsoft Sentinel API poller for the Team Cymru Scout API. It pulls account usage, search records, IP detail enrichment, and foundation lookups and posts the results to custom Log Analytics tables using the Log Ingestion API with managed identity.

## Required app settings

- `SCOUT_BASE_URL` – default `https://scout.cymru.com/api`
- `SCOUT_API_KEY` – Team Cymru Scout API key
- `SCOUT_QUERY` – Scout query language expression such as `ip=93.184.216.34`
- `SCOUT_LOOKBACK_DAYS` – default `30`
- `DCE_URI` – Data Collection Endpoint URI, for example `https://mydce.eastus-1.ingest.monitor.azure.com`
- `DCR_IMMUTABLE_ID` – immutable ID of the DCR attached to the custom tables
- `MAX_IP_DETAILS_PER_RUN` – default `10`

## Tables created by the connector

- `TeamCymruScoutUsage_CL`
- `TeamCymruScoutSearch_CL`
- `TeamCymruScoutIPDetails_CL`
- `TeamCymruScoutFoundation_CL`

## Runtime schedule

The default timer trigger runs hourly. The schedule is configurable in `function_app.py`.
