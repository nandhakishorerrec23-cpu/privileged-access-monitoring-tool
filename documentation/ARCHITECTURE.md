# Sentinel — System Architecture & Data Flow

## 1. High-Level Architecture Overview

**Sentinel** is an enterprise-grade privileged access monitoring (PAM) detection and audit system built to satisfy Cybersecurity Problem Statement **T2-PS4**. It processes administrative activity logs, enforces canonical normalization, applies 10 deterministic security heuristics, prevents duplicate log ingestion, and provides an explainable investigation workflow with persistent audit trails.

```
+-----------------------------------------------------------------------------------+
|                              REACT TYPESCRIPT SPA                                 |
|  - Overview Dashboard (KPIs, Recharts Timelines, Severity Distributions)          |
|  - Activity Logs (Server Pagination, Multi-Filter, Untrusted Command Inspector)    |
|  - Alerts & Investigations (Dossier, Correlated Events, Triage Form, Audit Trail)  |
|  - Ingestion & Simulation (Atomic Upload Dropzone, Schema Validator, Simulator)   |
|  - Detection Rules (Heuristics Matrix, Threshold Tuner, Reanalysis Trigger)       |
|  - Audit Reports (Executive Printable HTML, Archival JSON, Sanitized CSV)          |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (Vite Proxy in dev,
                                           | Single-Origin in production)
                                           v
+-----------------------------------------------------------------------------------+
|                            FASTAPI BACKEND RUNTIME                                |
|  - Dependency Injection (Session Token, CSRF Guard, DB Connection Pool)           |
|  - Ingestion Engine (UTF-8/BOM Decoding, Row Validation, Deduplication)          |
|  - Cryptographic Fingerprinting (SHA-256 of Canonical Attributes)                |
|  - Deterministic Detection Engine (Rules R01 - R10, Rolling Windows, Suppression) |
|  - Reanalysis Pipeline (Idempotent Recalculation, Active/Inactive Deactivation)    |
|  - Sanitized Exporters (Spreadsheet Formula Injection Neutralization)             |
+------------------------------------------+----------------------------------------+
                                           | SQLAlchemy 2.0 (Sync Engine)
                                           v
+-----------------------------------------------------------------------------------+
|                             SQLITE PERSISTENCE ENGINE                             |
|  - workspaces (Guest sessions, Token hashes, Expiry timestamps)                   |
|  - activity_events (Fingerprint indices, Canonical log schema)                    |
|  - import_batches (Batch statistics, atomic ingestion metadata)                   |
|  - rule_configs (Workspace thresholds, rule versions, enabled flags)              |
|  - alerts (Stable Alert IDs, dedup keys, review statuses, active indicators)      |
|  - alert_event_links (Many-to-many event-to-alert relationships)                  |
|  - alert_review_history (Immutable audit trail of analyst decisions & notes)       |
|  - analysis_runs (Execution telemetry and deactivation metrics)                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Ingestion & Canonical Schema Pipeline

All administrative activity ingested via CSV upload, JSON array, or manual simulation passes through an identical validation pipeline:

### Canonical Schema

| Field | Type | Description | Validation Rule |
| :--- | :--- | :--- | :--- |
| `timestamp` | ISO 8601 DateTime | When event occurred | Must have explicit timezone (`Z` or `+HH:MM`) |
| `actor` | String | Account performing action | Non-empty string (1–120 chars) |
| `action` | String | Normalized administrative verb | Must match 1 of 15 canonical actions |
| `target` | String | Affected user, role, service, or resource | Non-empty string (1–120 chars) |
| `status` | String | Execution outcome | Exactly `success` or `failed` |
| `source_ip` | String | Origin IP address | Valid IPv4 or IPv6 format |
| `actor_role` | String (optional) | Role of actor at execution time | Max 50 chars |
| `target_role` | String (optional) | Target role assigned | Max 50 chars |
| `previous_role`| String (optional) | Prior role before transition | Max 50 chars |
| `command` | Text (optional) | Recorded shell/CLI command text | Untrusted string; never executed |
| `approved` | Boolean (optional) | Change authorization evidence | `True`, `False`, or `None` (Unknown) |
| `approval_reference` | String (optional) | Ticket or change request ID | Max 100 chars |
| `details` | Text (optional) | Context or reason text | Free text string |

### Normalized Actions Enforced:
`login`, `logout`, `create_user`, `create_admin`, `change_privilege`, `delete_user`, `reset_password`, `reset_admin_password`, `disable_account`, `enable_account`, `clear_logs`, `disable_security`, `export_sensitive`, `update_config`, `execute_command`.

### Cryptographic Fingerprinting & Deduplication:
Each canonical event is hashed into a SHA-256 fingerprint:
```python
sha256(
    f"{timestamp.isoformat()}|{actor.lower()}|{action}|{target.lower()}|"
    f"{status}|{source_ip}|{actor_role or ''}|{target_role or ''}|"
    f"{previous_role or ''}|{command or ''}|{approved}|{approval_reference or ''}|"
    f"{details or ''}".encode('utf-8')
).hexdigest()
```
Duplicate events within the same workspace are identified and skipped during ingestion, ensuring idempotency.

---

## 3. Public Demo & Workspace Isolation

To make Sentinel publicly evaluable without third-party credentials or cross-visitor contamination:
1. **Opaque Guest Workspaces:** On first access, an isolated guest workspace is generated with a random 32-byte session token and CSRF token.
2. **HttpOnly Cookie Storage:** The session token is transmitted solely via an `HttpOnly`, `SameSite=Lax` cookie (`sentinel_session`).
3. **CSRF Header Protection:** State-changing requests (`POST`, `PUT`, `DELETE`) require the `X-CSRF-Token` header matching the session.
4. **Tenant Isolation:** All database queries and operations enforce `workspace_id == current_workspace.id`. Knowing another record's ID returns HTTP 404.
5. **Session Expiry & Lifecycle:** Sessions expire after 24 hours. A background cleanup query purges expired sessions.

---

## 4. Formula Injection & Export Sanitization

To neutralize spreadsheet formula injection vulnerabilities:
- CSV cell values beginning with `= `, `+`, `-`, `@`, `\t`, or `\r` have a single apostrophe (`'`) prepended.
- HTML reports enforce entity escaping via `html.escape` and print media styles for archival PDF generation.
