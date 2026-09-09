# Team Cymru Scout API -- CCF Connector Reference Documentation

> **Purpose:** This document describes the Team Cymru Pure Signal Scout API for use with the
> **Microsoft Sentinel Codeless Connector Framework (CCF)** API Poller.
> It is structured for consumption by the **Sentinel CCF Connector Builder Agent**.

---

## Table of Contents

1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
   - [GET /api/scout/usage](#get-apiscoutusage)
   - [GET /api/scout/search](#get-apiscoutsearch)
   - [GET /api/scout/ip/{ip}/details](#get-apiscoutipipdetails)
   - [GET /api/scout/ip/foundation](#get-apiscoutipfoundation)
5. [Data Schema](#data-schema)
6. [Pagination](#pagination)
7. [Incremental Pull (Date-Based Filtering)](#incremental-pull-date-based-filtering)
8. [Error Responses](#error-responses)
9. [CCF API Poller Connector Configuration](#ccf-api-poller-connector-configuration)

---

## Overview

The **Team Cymru Scout API** is a threat intelligence lookup and enrichment API. It provides
real-time intelligence on IP addresses and domains, including communications data, open ports,
passive DNS (PDNS), X.509 certificates, fingerprints, and whois information.

| Property | Value |
|---|---|
| Data format | JSON |
| Authentication | API Key (header) or HTTP Basic Auth |
| Pagination | None (single response per request) |
| Incremental pull | `start_date` / `end_date` query parameters (YYYY-MM-DD) |
| Rate limiting | Monthly search balance; searches are metered |

---

## Base URL

```
https://scout.cymru.com/api
```

> **Note:** The base URL may vary by deployment. The exact URL is provided during account setup.

---

## Authentication

The Scout API supports two authentication methods:

### API Key Authentication

| Header | Required | Description |
|---|---|---|
| `Authorization` | **Yes** | Format: `Token: <api_key>` where `<api_key>` is the API key provisioned during account setup. |

#### Example

```http
GET /api/scout/ip/93.184.216.34/details HTTP/1.1
Host: scout.cymru.com
Authorization: Token: your-api-key-here
```

### HTTP Basic Authentication

| Field | Required | Description |
|---|---|---|
| Username | **Yes** | The username provisioned during account setup. |
| Password | **Yes** | The password provisioned during account setup. |

#### CCF Authentication Configuration

For CCF connector development, use the **APIKey** auth type:

| CCF Setting | Value |
|---|---|
| Auth Type | `APIKey` |
| API Key Header Name | `Authorization` |
| API Key Identifier | `Token:` |
| API Key Value | *(the key provisioned at account setup)* |

---

## Endpoints

### GET /api/scout/usage

Returns account usage statistics including remaining search balance.

**URL:** `GET /api/scout/usage`

#### Response -- 200 OK

<!-- TODO: Document the exact response schema for /api/scout/usage -->
<!-- This endpoint returns account usage data including monthly search balance -->

```json
{
  "query_count": 150,
  "query_limit": 1000,
  "period_start": "2026-09-01",
  "period_end": "2026-09-30"
}
```

> **Note:** The above response schema is approximate. Verify the exact field names and
> structure against a live API response.

---

### GET /api/scout/search

Executes an advanced search query using the Scout Query Language. Returns a multi-view
result set of IPs matching the query criteria.

**URL:** `GET /api/scout/search`

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | **Yes** | A Scout Query Language expression. See [Search Types and Fields](#search-types-and-fields) below. |
| `start_date` | string (YYYY-MM-DD) | No | Return only data observed on or after this date. Used for incremental/delta pulls. |
| `end_date` | string (YYYY-MM-DD) | No | Return only data observed on or before this date. |

<!-- TODO: Verify the exact parameter names for date filtering on the search endpoint. -->
<!-- The parameter names may differ from start_date/end_date. Check the live API. -->

#### Request Example

```http
GET /api/scout/search?query=ip=93.184.216.34&start_date=2026-09-01&end_date=2026-09-09 HTTP/1.1
Host: scout.cymru.com
Authorization: Token: your-api-key-here
```

#### Response -- 200 OK

<!-- TODO: Document the exact response schema for /api/scout/search -->
<!-- The response contains a list of IP results matching the query criteria -->

```json
{
  "data": [
    {
      "ip": "93.184.216.34",
      "as_name": "EDGECAST",
      "asn": 15133,
      "cc": "US",
      "tags": ["cdn"],
      "start_date": "2026-09-01",
      "end_date": "2026-09-09"
    }
  ],
  "query": "ip=93.184.216.34",
  "status": "success"
}
```

> **Note:** The above response schema is approximate. Verify the exact field names,
> structure, and nesting against a live API response.

---

### GET /api/scout/ip/{ip}/details

Returns detailed information for a specific IP address, including communications,
PDNS, open ports, X.509 certificates, fingerprints, and whois data.

**URL:** `GET /api/scout/ip/{ip}/details`

#### Path Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ip` | string (IPv4) | **Yes** | The IP address to query. |

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `start_date` | string (YYYY-MM-DD) | No | Start of observation window. |
| `end_date` | string (YYYY-MM-DD) | No | End of observation window. |

<!-- TODO: Verify the exact parameter names for date filtering on the details endpoint. -->

#### Response -- 200 OK

The response contains detailed data organized by section:

```json
{
  "ip": "93.184.216.34",
  "start_date": "2026-09-01",
  "end_date": "2026-09-09",
  "request_id": "req-abc123",
  "sections": ["summary", "communications", "pdns", "open_ports", "x509", "fingerprints", "whois"],
  "summary": {
    "tags": [],
    "pdns": { "top_pdns": [] },
    "open_ports": { "top_open_ports": [] },
    "certs": { "top_certs": [] },
    "fingerprints": { "top_fingerprints": [] }
  },
  "communications": {
    "peers": []
  },
  "pdns": {
    "pdns": []
  },
  "open_ports": {
    "open_ports": []
  },
  "x509": {
    "x509": []
  },
  "fingerprints": {
    "fingerprints": []
  },
  "whois": {}
}
```

> **Note:** The above response schema is derived from the existing connector source code.
> Verify the exact structure against a live API response.

---

### GET /api/scout/ip/foundation

Returns foundation-level IP data for one or more IP addresses.

**URL:** `GET /api/scout/ip/foundation`

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ips` | string | **Yes** | Comma-separated list of IP addresses (max 10 per request). |
| `start_date` | string (YYYY-MM-DD) | No | Start of observation window. |
| `end_date` | string (YYYY-MM-DD) | No | End of observation window. |

<!-- TODO: Verify the exact parameter names and limits for the foundation endpoint. -->

#### Request Example

```http
GET /api/scout/ip/foundation?ips=93.184.216.34,104.18.213.12&start_date=2026-09-01&end_date=2026-09-09 HTTP/1.1
Host: scout.cymru.com
Authorization: Token: your-api-key-here
```

#### Response -- 200 OK

```json
{
  "data": [
    {
      "ip": "93.184.216.34",
      "as_name": "EDGECAST",
      "asn": 15133,
      "cc": "US",
      "tags": ["cdn"],
      "tags_id": [],
      "tags_name": []
    }
  ]
}
```

> **Note:** The above response schema is approximate. Verify against a live API response.

---

## Search Types and Fields

The Scout search endpoint supports the following query selectors:

| Selector | Wildcard | Description |
|---|---|---|
| `asn` | No | Search by ASN |
| `cc` | No | Search by country code |
| `ip` | No | Search by IP address or CIDR |
| `tag` | No | Search by tags |
| `comms.ip` | No | Search by communication peer IP |
| `comms.port` | No | Search by communication port |
| `comms.proto` | No | Search by communication protocol |
| `comms.tag` | No | Search by communication peer tag |
| `openports.port` | No | Search by open port |
| `openports.banner` | Yes | Search by banner text |
| `openports.service` | No | Search by service name |
| `pdns.domain` | Yes | Search by domain name |
| `pdns.nameserver` | No | Search by DNS nameserver |
| `pdns.registrar` | Yes | Search by domain registrar |
| `x509.subject.cn` | Yes | Search by certificate subject common name |
| `x509.issuer` | Yes | Search by certificate issuer |
| `fingerprints.hash` | No | Search by fingerprint hash |
| `fingerprints.type` | No | Search by fingerprint type (jarm, ja3s, ja3, etc.) |

> **Note:** This is a subset of the full query language. See the Scout documentation
> for the complete list of selectors and operators (`=`, `!=`, `<`, `>`, `<=`, `>=`).

---

## Pagination

The Scout API does **not** implement pagination. All results for a given request are
returned in a single response.

---

## Incremental Pull (Date-Based Filtering)

The Scout API supports date-based filtering via `start_date` and `end_date` query parameters.

| Property | Value |
|---|---|
| Start time parameter | `start_date` |
| End time parameter | `end_date` |
| Date format | `YYYY-MM-DD` (date only, no time component) |

To perform incremental ingestion:
1. On the initial pull, omit `start_date` and `end_date` (or set to the desired observation window).
2. On subsequent polls, set `start_date` to the date of the last successful poll.
3. Set `end_date` to the current date.

<!-- TODO: Verify that start_date and end_date are the exact parameter names accepted -->
<!-- by all endpoints. Also verify the exact behavior when these parameters are omitted. -->

---

## Error Responses

| HTTP Status | Description |
|---|---|
| `400 Bad Request` | Invalid query parameter or malformed request. |
| `401 Unauthorized` | Missing or incorrect authentication credentials. |
| `403 Forbidden` | Authorization error (insufficient permissions). |
| `404 Not Found` | Resource not found. |
| `429 Too Many Requests` | Rate limit exceeded. |
| `500 Internal Server Error` | Server-side error. |

---

## CCF API Poller Connector Configuration

> This section provides the primary reference for building a **Microsoft Sentinel CCF**
> connector that polls the Scout API.

### Authentication Configuration

| CCF Setting | Value |
|---|---|
| Auth Type | `APIKey` |
| API Key Header Name | `Authorization` |
| API Key Identifier | `Token:` |
| API Key Value | *(the key provisioned at account setup)* |

### Request Configuration

| CCF Setting | Value |
|---|---|
| HTTP Method | `GET` |
| Base URL | `https://scout.cymru.com` |
| Query Time Format | `yyyy-MM-dd` |
| Start Time Attribute Name | `start_date` |
| End Time Attribute Name | `end_date` |
| Query Window In Min | `1440` (24 hours, since the API uses date-only granularity) |

<!-- TODO: The queryWindowInMin should match the date-only granularity of the API. -->
<!-- Since the API uses YYYY-MM-DD format, a 1440-minute (24-hour) window makes sense. -->
<!-- Verify this is the correct approach for the Scout API's polling behavior. -->

### Response Parsing

| CCF Setting | Value |
|---|---|
| Events JSON Path | `$.data[*]` |
| Response Format | `json` |

<!-- TODO: Verify the exact JSON path for the events array in each endpoint's response. -->

### Pagination Configuration

No pagination configuration is needed. Omit the `paging` section from the CCF connector config.

### Rate Limiting

The Scout API uses monthly search balance metering. Each API call decrements the balance.
Configure the CCF polling interval to respect the account's monthly query limit.

| CCF Setting | Suggested Value |
|---|---|
| Rate Limit QPS | `1` (conservative; adjust based on account limits) |
| Retry Count | `3` |
| Timeout In Seconds | `180` |

---

## Open Questions (TODO)

The following items need verification against a live Scout API instance before the CCF
Connector Builder Agent can generate production-ready config files:

1. **Exact parameter names:** Confirm that `start_date` and `end_date` are the correct
   query parameter names for all endpoints.

2. **Response schemas:** The response JSON structures in this document are approximate,
   derived from the existing Python connector source code. They need to be verified
   against actual API responses.

3. **Search endpoint for polling:** Determine which endpoint is best suited for periodic
   CCF polling. Options:
   - `/api/scout/ip/foundation` — requires a list of IPs as input
   - `/api/scout/ip/{ip}/details` — requires a single IP as input
   - `/api/scout/search` — accepts query language, may be most flexible for polling

4. **Events JSON path:** Confirm the exact JSON path to the events/records array in each
   endpoint's response (e.g., `$.data[*]`, `$.data`, `$`).

5. **Query window behavior:** Verify how the API behaves when `start_date` equals
   `end_date` (same-day query) and when date parameters are omitted entirely.

6. **Multiple connection rules:** The existing Azure Function connector has 3 separate
   collectors (IP, Domain, Account Usage). Determine whether the CCF migration needs
   multiple `RestApiPoller` connection rules or a single one.
