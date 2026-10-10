# Sentinel — Privileged Access Monitoring Tool

> **T2-PS4: Privileged Access Monitoring Tool**  
> **Product Name:** Sentinel  
> **Subtitle:** Privileged Access Monitoring Tool  

![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB?logo=react&logoColor=black)
![Tailwind](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC?logo=tailwind-css&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite%20with%20SQLAlchemy-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Deployment-Docker%20%2B%20Compose-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-pytest-brightgreen?logo=pytest&logoColor=white)

---

## 1. Executive Abstract & Objectives

Administrator accounts have elevated permissions to manage users, modify security configurations, and access sensitive resources. Organizations require a robust system that processes real or simulated administrative activity logs, enforces canonical normalization, applies deterministic security rules, detects risky actions and unauthorized privilege changes, generates explainable alerts, and exports verified audit reports.

**Sentinel** is a full-stack cybersecurity operations platform designed to satisfy Problem Statement **T2-PS4**. It delivers:
- **Canonical Normalization Engine:** Validates ISO 8601 timestamps with timezones, IPv4/IPv6 addresses, 15 normalized administrative actions, and cryptographic SHA-256 event fingerprints to eliminate duplicates.
- **Explainable Detection Pipeline:** Evaluates 10 deterministic security heuristics (R01 to R10), including privilege escalations, audit log deletions, security agent tampering, out-of-hours operations, and credential-stuffing bursts with alert suppression.
- **Isolated Guest Workspaces:** Allows immediate public evaluation without third-party credentials. Every visitor gets an isolated workspace bounded by HttpOnly session cookies and CSRF verification.
- **Analyst Investigation Dossier:** Tracks alert triage lifecycles (`Open`, `Investigating`, `Resolved`, `False Positive`) with persistent analyst notes and status audit history.
- **Audit Reports & Compliance Exports:** Generates executive printable HTML/PDF reports, archival JSON audit packages, and CSV datasets sanitized against spreadsheet formula injection.

---

## 2. Technology Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts, TanStack Query v5.
- **Backend:** Python 3.11, FastAPI, Pydantic v2, Pandas, SQLAlchemy 2.0 (synchronous engine with thread safety).
- **Persistence:** SQLite with relational schema, foreign key cascades, and composite indices.
- **Testing:** `pytest`, `pytest-asyncio`, `httpx`, `TestClient`.
- **Deployment:** Multi-stage Docker container (Node 20 build stage + Python 3.11 runtime) serving frontend assets directly alongside FastAPI on port 8000.

---

## 3. Core Features & Functional Sections

| Section | Capabilities |
| :--- | :--- |
| **A. Overview** | Database-backed KPI metrics, severity distribution donut, time-series activity chart (events vs alerts), most frequently flagged actors, recent critical alerts. |
| **B. Activity Logs** | Server-side paginated table, multi-field search (actor, target, IP, command), action/actor/status filters, sortable columns, CSV export, and Event Detail Drawer. |
| **C. Alerts & Investigations** | Filterable alert list, triage lifecycle dropdown, investigation dossier with explainable reasons, JSON evidence, correlated events, analyst notes, and status change audit trail. |
| **D. Import & Simulation** | Drag-and-drop CSV/JSON upload, pre-commit schema diagnostics with row-by-row error reporting, atomic rollback, and manual event simulation form. |
| **E. Detection Rules** | R01–R10 heuristic matrix, editable business hours and failure thresholds, enabled/disabled toggles, and idempotent log reanalysis. |
| **F. Audit Reports** | Executive printable HTML reports with print styling, archival JSON packages, and formula-injection-neutralized CSV exports. |
| **G. Project Guide** | Architecture documentation, schema specs, rules matrix, 5-minute demonstration script, and guest session security model. |

---

## 4. Detection Rules Matrix (R01 – R10)

| Rule ID | Rule Name | Default Severity | Trigger Condition |
| :--- | :--- | :--- | :--- |
| **R01** | Administrator Account Created | High | Successful `create_admin` event. |
| **R02** | Privilege Escalation Detected | Critical / High | Successful `change_privilege` elevating to admin/root/superuser. Produces High review alert if roles are missing. Known downgrades are excluded. |
| **R03** | Audit Logs Cleared | Critical | Successful `clear_logs` event. |
| **R04** | Security Monitoring Disabled | Critical | Successful `disable_security` event. |
| **R05** | Account Deleted | High | Successful `delete_user` event. |
| **R06** | Administrator Password Reset | High | Successful `reset_admin_password` event. Ordinary user resets are excluded. |
| **R07** | Sensitive Data Export | High | Successful `export_sensitive` event. |
| **R08** | After-Hours Activity | Medium | Successful admin action outside business hours (default `08:00–18:00 UTC`). Excludes ordinary `login`/`logout`. |
| **R09** | Repeated Failed Logins | High | $\ge 5$ failed logins for same actor and IP within a rolling 10-minute window. Features alert burst suppression. |
| **R10** | Explicitly Unapproved Operation | Critical | Successful `create_admin` or `change_privilege` with `approved=false`. Missing approval data is treated as unknown. |

---

## 5. Local Development Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git

### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
FastAPI interactive docs will be available at: `http://localhost:8000/docs`

### Frontend Setup
```bash
# In a separate terminal, navigate to frontend
cd frontend

# Install Node modules
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser. All `/api` requests are proxied to `http://localhost:8000`.

---

## 6. Production Docker Deployment

Sentinel is optimized for single-origin container deployments:

```bash
# Build and start container in the background
docker compose up --build -d

# Check health and status
docker compose ps

# Follow container logs
docker compose logs -f

# Access Sentinel in your browser
http://localhost:8000
```

> **SQLite Storage Notice:** The database is saved on a persistent named volume mounted to `/data/sentinel.db`. An ephemeral filesystem loses database state upon container destruction. SQLite is intended for a single-instance deployment prototype.

---

## 7. Running Backend Tests

Run the comprehensive pytest suite covering all 10 rules, threshold boundaries, atomic rollbacks, CSV formula sanitization, and workspace isolation:

```bash
# From workspace root or backend directory:
pytest tests/backend/ -v
```

---

## 8. Five-Minute Demonstration Walkthrough

1. **Access Web App:** Open `http://localhost:8000` or `http://localhost:5173`.
2. **Seed Synthetic Data:** Click **"Load 95+ Demo Events"** in the sidebar. Observe that 95+ events are ingested and alerts are generated.
3. **Overview Dashboard:** Examine the KPI cards, Severity Distribution donut chart, and Chronological Activity Timeline.
4. **Activity Logs:** Search for an IP (`198.51.100.99`) or action (`clear_logs`), click a row to view the Event Detail Drawer with linked alert IDs.
5. **Alerts & Investigations:** Filter by `Severity: Critical`. Open **R03 Audit Logs Cleared**, inspect the JSON evidence, change review status to `Investigating`, enter an analyst note, and click **Save Review Decision**. Verify the persistent review history timeline.
6. **Import & Atomic Rollback:** In **Import & Simulation**, download the "Test Invalid CSV" sample and upload it. Observe the row-by-row error diagnostics and atomic rejection notice.
7. **Rule Tuning & Reanalysis:** In **Detection Rules**, edit the R08 business hours window and click **Reanalyze Workspace Logs**. Notice how matching alerts preserve analyst notes while non-matching alerts are safely marked inactive.
8. **Export Audit Reports:** In **Audit Reports**, click **"Print / Save as PDF"** to view the clean printable executive audit report with formula injection sanitization.

---

## 9. Security Guarantees & Defensive Measures

- **No Remote Code Execution:** Recorded commands in event logs are treated as untrusted text strings and strictly rendered in non-executable monospace blocks.
- **CSV Formula Injection Sanitization:** Cell values starting with `=`, `+`, `-`, `@`, `\t`, or `\r` have a leading apostrophe (`'`) prepended during export.
- **Tenant Isolation:** Workspace authorization is enforced on every query. Accessing records from another workspace returns HTTP 404.
- **State-Changing CSRF Tokens:** POST/PUT/DELETE requests enforce valid `X-CSRF-Token` headers.
- **Explainable Detections:** The UI frames detections as potential operational risks to be investigated rather than claiming definitive mathematical certainty.
