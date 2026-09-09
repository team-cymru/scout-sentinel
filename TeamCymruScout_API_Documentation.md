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
5. [Pagination](#pagination)
6. [Incremental Pull](#incremental-pull)
7. [Error Responses](#error-responses)
8. [CCF API Poller Connector Configuration](#ccf-api-poller-connector-configuration)

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
| Incremental pull | Optional `start_date` / `end_date` parameters (YYYY-MM-DD). When omitted, the API defaults to a 30-day observation window. |
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

The Scout API has four primary endpoints. The existing Sentinel connector polls these
on a schedule: IP and Domain data daily at midnight UTC, Account Usage data hourly.

### GET /api/scout/usage

Returns account usage statistics including remaining search balance.

**URL:** `GET /api/scout/usage`

**Query Parameters:** None required.

#### Response -- 200 OK

```json
{
  "used_queries": 150,
  "remaining_queries": 850,
  "query_limit": 1000,
  "foundation_api_usage": {
    "used_queries": 50,
    "remaining_queries": 450,
    "query_limit": 500
  },
  "ai_insights_usage": {
    "used_queries": 10,
    "remaining_queries": 90,
    "query_limit": 100
  }
}
```

**Events JSON Path:** `$` (the root object is the single record; wrap in array for ingestion)

---

### GET /api/scout/search

Executes an advanced search query using the Scout Query Language. Returns IPs matching
the query criteria along with enrichment data.

**URL:** `GET /api/scout/search`

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | **Yes** | A Scout Query Language expression (e.g., `ip=93.184.216.34` or `pdns.domain="*.example.com"`). |
| `start_date` | string (YYYY-MM-DD) | No | Start of observation window. Defaults to 30 days ago if omitted. |
| `end_date` | string (YYYY-MM-DD) | No | End of observation window. Defaults to today if omitted. |

#### Request Example

```http
GET /api/scout/search?query=example.com HTTP/1.1
Host: scout.cymru.com
Authorization: Token: your-api-key-here
```

#### Response -- 200 OK

```json
{
  "query": "example.com",
  "start_date": "2026-08-10",
  "end_date": "2026-09-09",
  "ips": [
    {
      "ip": "93.184.216.34",
      "country_codes": ["US"],
      "as_info": {},
      "tags": [],
      "event_count": 42,
      "summary": {},
      "comms_enrichment": {}
    }
  ]
}
```

**Events JSON Path:** `$.ips[*]`

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
| `start_date` | string (YYYY-MM-DD) | No | Start of observation window. Defaults to 30 days ago if omitted. |
| `end_date` | string (YYYY-MM-DD) | No | End of observation window. Defaults to today if omitted. |

#### Request Example

```http
GET /api/scout/ip/93.184.216.34/details HTTP/1.1
Host: scout.cymru.com
Authorization: Token: your-api-key-here
```

#### Response -- 200 OK

The response contains detailed data organized by section:

```json
{
  "ip": "93.184.216.34",
  "start_date": "2026-08-10",
  "end_date": "2026-09-09",
  "request_id": "req-abc123",
  "sections": ["summary", "communications", "pdns", "open_ports", "x509", "fingerprints", "whois"],
  "identity": {
    "asn": 15133,
    "as_name": "EDGECAST",
    "net_name": "EDGECAST-NETBLK-01",
    "org_name": "Edgecast Inc.",
    "tags": [],
    "reverse_hostnames": []
  },
  "whois": {
    "asn": 15133,
    "modified": "2012-06-22",
    "cidr": "93.184.216.0/24",
    "as_name": "EDGECAST",
    "bgp_asn": 15133,
    "bgp_asn_name": "EDGECAST",
    "net_name": "EDGECAST-NETBLK-01",
    "net_handle": "NET-93-184-216-0-1",
    "description": "",
    "cc": "US",
    "city": "",
    "address": ""
  },
  "communications": {
    "event_count": 100,
    "peers": [
      { "ip": "1.2.3.4", "event_count": 10 }
    ]
  },
  "pdns": {
    "event_count": 50,
    "pdns": [
      { "domain": "example.com", "type": "A", "event_count": 25 }
    ]
  },
  "fingerprints": {
    "event_count": 5,
    "fingerprints": [
      { "hash": "abc123", "fingerprints_type": "jarm", "port": 443 }
    ]
  },
  "open_ports": {
    "event_count": 10,
    "unique_ports": 3,
    "open_ports": [
      { "port": 443, "service": "https", "banner": "" }
    ]
  },
  "x509": {
    "event_count": 2,
    "x509": [
      { "subject": "CN=example.com", "issuer": "CN=DigiCert" }
    ]
  },
  "summary": {
    "tags": [],
    "reverse_hostnames": [],
    "whois": {},
    "total": 167,
    "geo_ip_cc": "US",
    "bgp_asn": 15133,
    "bgp_asname": "EDGECAST",
    "insights": {},
    "pdns": { "top_pdns": [] },
    "open_ports": { "top_open_ports": [] },
    "certs": { "top_certs": [] },
    "fingerprints": { "top_fingerprints": [] },
    "tag_timeline": {}
  }
}
```

**Events JSON Path:** `$` (the root object is the single record; the existing connector wraps it in `[ip_data]` before ingestion)

**Sub-record paths** (for splitting into separate tables, as the existing connector does):
- Communications peers: `$.communications.peers[*]`
- PDNS records: `$.pdns.pdns[*]`
- Fingerprints: `$.fingerprints.fingerprints[*]`
- Open ports: `$.open_ports.open_ports[*]`
- X.509 certificates: `$.x509.x509[*]`
- Summary PDNS: `$.summary.pdns.top_pdns[*]`
- Summary open ports: `$.summary.open_ports.top_open_ports[*]`
- Summary certs: `$.summary.certs.top_certs[*]`
- Summary fingerprints: `$.summary.fingerprints.top_fingerprints[*]`

---

### GET /api/scout/ip/foundation

Returns foundation-level IP data for one or more IP addresses.

**URL:** `GET /api/scout/ip/foundation`

#### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ips` | string | **Yes** | Comma-separated list of IP addresses (max 10 per request). |
| `start_date` | string (YYYY-MM-DD) | No | Start of observation window. Defaults to 30 days ago if omitted. |
| `end_date` | string (YYYY-MM-DD) | No | End of observation window. Defaults to today if omitted. |

#### Request Example

```http
GET /api/scout/ip/foundation?ips=93.184.216.34,104.18.213.12 HTTP/1.1
Host: scout.cymru.com
Authorization: Token: your-api-key-here
```

#### Response -- 200 OK

```json
{
  "data": [
    {
      "ip": "93.184.216.34",
      "country_code": "US",
      "as_info": {
        "asn": 15133,
        "as_name": "EDGECAST"
      },
      "tags": [
        { "id": "cdn", "name": "CDN" }
      ],
      "insights": {
        "overall_rating": "no_rating",
        "insights": []
      }
    }
  ]
}
```

**Events JSON Path:** `$.data[*]`

---

## Search Types and Fields

The Scout search endpoint (`/api/scout/search`) supports a query language with the following selectors:

| Selector | Wildcard | Description | Examples |
|---|---|---|---|
| `asn` | No | Search by ASN | `123`, `123,456` |
| `cc` | No | Search by country code | `US`, `US,DE` |
| `ip` | No | Search by IP or CIDR | `93.184.216.34`, `93.184.216.0/24` |
| `tag` | No | Search by tags | `scanner`, `cloud,router` |
| `comms.ip` | No | Communication peer IP | `93.184.216.34` |
| `comms.port` | No | Communication port | `80`, `80,8080` |
| `comms.proto` | No | Communication protocol | `6`, `6,7` |
| `comms.count` | No | Communication event count | `1`, `100` |
| `openports.port` | No | Open port number | `443,80` |
| `openports.banner` | Yes | Banner text | `nginx`, `*Referrer-Policy*` |
| `openports.service` | No | Service name | `http`, `ssh` |
| `pdns.domain` | Yes | Domain name | `google.com`, `*.jquery.com` |
| `pdns.nameserver` | No | DNS nameserver | `ns1.example.com` |
| `pdns.registrar` | Yes | Domain registrar | `Dynadot LLC` |
| `pdns.count` | No | PDNS event count | `1`, `100` |
| `x509.subject.cn` | Yes | Certificate subject CN | `sni.cloudflaressl.com` |
| `x509.issuer` | Yes | Certificate issuer | `DigiCert Inc` |
| `x509.sha256` | No | Certificate SHA256 | `8b396e40...` |
| `fingerprints.hash` | No | Fingerprint hash | `eb1d94daa7e0...` |
| `fingerprints.type` | No | Fingerprint type | `jarm`, `ja3s`, `ja3`, `hassh` |
| `meta.asn` | No | ASN across all search types | `123` |
| `meta.cc` | No | Country code across all types | `US` |
| `meta.tag` | No | Tags across all search types | `scanner` |

**Operators:** All selectors support `=` and `!=`. Count selectors additionally support `<`, `<=`, `>`, `>=`.

**Wildcards:** Supported on indicated fields using `*` character.

---

## Pagination

The Scout API does **not** implement pagination. All results for a given request are
returned in a single response. No pagination configuration is needed in the CCF connector.

---

## Incremental Pull

The Scout API supports optional `start_date` and `end_date` query parameters on all
data endpoints. These control the observation window for returned data.

| Property | Value |
|---|---|
| Start time parameter | `start_date` |
| End time parameter | `end_date` |
| Date format | `YYYY-MM-DD` (date only, no time component) |
| Default behavior (when omitted) | API returns data for the last 30 days |

**Existing connector behavior:** The current Azure Function connector omits both
`start_date` and `end_date`, relying on the API's 30-day default window. It polls
daily at midnight UTC (for IP/Domain data) and hourly (for Account Usage data).
There is no deduplication — each poll re-fetches the full 30-day window.

**CCF recommendation:** Match the existing behavior by omitting `startTimeAttributeName`
and `endTimeAttributeName` from the CCF request config. The CCF Poller will call the
endpoint without date parameters, and the API will return its default 30-day window.

---

## Error Responses

| HTTP Status | Description |
|---|---|
| `400 Bad Request` | Invalid query parameter or malformed request. |
| `401 Unauthorized` | Missing or incorrect authentication credentials. |
| `403 Forbidden` | Authorization error (insufficient permissions). |
| `404 Not Found` | Resource not found. |
| `429 Too Many Requests` | Rate limit exceeded (monthly search balance exhausted). |
| `500 Internal Server Error` | Server-side error. |
| `503 Service Unavailable` | Service temporarily unavailable. |

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

The existing connector polls three separate endpoints. The CCF migration may require
multiple `RestApiPoller` connection rules:

#### IP/Domain Data (daily polling)

| CCF Setting | Value |
|---|---|
| HTTP Method | `GET` |
| API Endpoint | `https://scout.cymru.com/api/scout/search` (or `/api/scout/ip/foundation`) |
| Query Window In Min | `1440` (24 hours, matching existing daily schedule) |
| Retry Count | `3` |
| Timeout In Seconds | `180` |

> **Note:** No `startTimeAttributeName` or `endTimeAttributeName` is configured.
> This matches the existing connector behavior: the API defaults to a 30-day
> observation window when date parameters are omitted.

#### Account Usage Data (hourly polling)

| CCF Setting | Value |
|---|---|
| HTTP Method | `GET` |
| API Endpoint | `https://scout.cymru.com/api/scout/usage` |
| Query Window In Min | `60` (1 hour, matching existing hourly schedule) |
| Retry Count | `3` |
| Timeout In Seconds | `60` |

### Response Parsing

| Endpoint | Events JSON Path | Format |
|---|---|---|
| `/api/scout/ip/foundation` | `$.data[*]` | `json` |
| `/api/scout/search` | `$.ips[*]` | `json` |
| `/api/scout/ip/{ip}/details` | `$` | `json` |
| `/api/scout/usage` | `$` | `json` |

### Pagination Configuration

No pagination configuration is needed. Omit the `paging` section entirely.

### Rate Limiting

The Scout API uses monthly search balance metering. Each API call decrements the balance.

| CCF Setting | Suggested Value |
|---|---|
| Rate Limit QPS | `1` (conservative; adjust based on account limits) |
| Retry Count | `3` |
| Timeout In Seconds | `180` |
