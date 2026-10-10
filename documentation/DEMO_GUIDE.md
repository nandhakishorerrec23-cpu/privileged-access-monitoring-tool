# Sentinel — 5-Minute Demonstration Script

Use this structured walkthrough for faculty evaluations, project reviews, or live cybersecurity demonstrations.

---

## ⏱️ Minute 1: Introduction & Guest Workspace Isolation

1. **Open the browser:** Navigate to `http://localhost:8000` (or the deployed public URL).
2. **Explain the product identity:**
   - Product Name: **Sentinel — Privileged Access Monitoring Tool** (T2-PS4).
   - Core Problem: Monitoring elevated administrative actions to catch malicious account creation, privilege escalation, log erasure, and defense evasion before damages occur.
3. **Point out Guest Session Isolation:**
   - In the sidebar footer, point out the **Guest Workspace** session indicator.
   - Explain: *"Every visitor receives an isolated workspace backed by an HttpOnly, SameSite=Lax cookie and CSRF token verification. No visitors share uploaded data or alerts."*

---

## ⏱️ Minute 2: Seeding Demo Data & Operations Dashboard

1. **Load demo dataset:**
   - Click the **"Load 95+ Demo Events"** button in the sidebar or top header.
   - Observe the success banner: *95+ synthetic events ingested, 0 rejected, and alerts generated.*
2. **Review the Overview Dashboard:**
   - Highlight the database-backed KPIs: Total Events, Total Active Alerts, Critical Alerts, Open Investigations, and Distinct Administrators.
   - Point out the **Severity Distribution Donut Chart** (Red Critical, Amber High, Blue Medium).
   - Point out the **Activity Telemetry Timeline** showing chronological events vs alerts over multiple days.
   - Show the **Most Frequently Flagged Privileged Actors** table.

---

## ⏱️ Minute 3: Investigating Security Alerts & SOC Triage

1. **Navigate to "Alerts & Investigations":**
   - Point out how each alert has a stable ID, rule code (R01–R10), severity, and status.
   - Filter by **Severity: Critical**.
2. **Open an Alert Dossier:**
   - Click on the **R03 Audit Logs Cleared** alert (`ALT-...`).
   - Examine the **Detection Reasoning** (explainable heuristic text).
   - Inspect the **Extracted Evidence Telemetry** (parsed JSON showing command `rm -rf /var/log/audit/*` and origin IP).
   - Show the **Correlated Ingested Event**.
3. **Perform Analyst Triage:**
   - In the triage box, change the status to **"Investigating"**.
   - Type an analyst note: *"Confirmed with system admin; investigating potential compromised SSH session from 198.51.100.99."*
   - Click **"Save Review Decision"**.
   - Point out the persistent **Review History Audit Trail** recording the timestamp, analyst name, and prior status.
   - Refresh the page to demonstrate that SQLite persisted the review decision.

---

## ⏱️ Minute 4: Ingestion Pipeline, Schema Validation & Atomic Rollback

1. **Navigate to "Import & Simulation":**
   - Click on **"Sample CSV"** to demonstrate download capability.
   - Click on **"Test Invalid CSV"** to download the intentionally corrupted sample.
2. **Demonstrate Atomic Rollback Safeguard:**
   - Upload the invalid CSV file.
   - Show the **Row-by-Row Schema Diagnostics** table displaying exact row numbers, field names, and error explanations (e.g. invalid IP address, unrecognized action).
   - Emphasize the security control: *"Because row errors exist, Sentinel refuses to commit a partial batch. The entire batch is atomically rejected to prevent database corruption."*
3. **Demonstrate Manual Simulation:**
   - Switch to the **Manual Event Simulator** tab.
   - Fill in an event (or keep defaults) and click **"Simulate & Run Detection"**.
   - Show the immediate detection pipeline execution and alert notification.

---

## ⏱️ Minute 5: Rule Customization, Reanalysis & Audit Export

1. **Navigate to "Detection Rules":**
   - Review the R01–R10 matrix.
   - Click **"Edit"** on **R08 (After-Hours Activity)**. Change the business window or timezone.
   - Click **"Reanalyze Workspace Logs"**.
   - Observe the execution report: *Events analyzed, alerts created/deactivated, zero duplicate alerts created.*
2. **Navigate to "Audit Reports":**
   - Show the live filter counters (Events in Scope, Critical Alerts in Scope).
   - Click **"Print / Save as PDF"** to display the clean executive report with print styling and investigation disclaimer.
   - Mention the **CSV Formula Injection Safeguard**: all exported cells with `=`, `+`, `-`, or `@` are sanitized with leading apostrophes to protect analysts against spreadsheet exploits.
3. **Conclusion:** Summarize that Sentinel provides complete, explainable, and tamper-resistant privileged access monitoring.
