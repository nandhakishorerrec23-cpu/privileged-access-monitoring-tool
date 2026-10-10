# Sentinel — Detection Rules Specification Matrix

This document formally specifies the 10 detection rules implemented in the Sentinel detection engine (`backend/app/services/detection_engine.py`).

---

### R01 — Administrator Account Created
- **Severity:** High
- **Trigger Condition:** `status == "success"` AND `action == "create_admin"`
- **Rationale:** Addition of administrative identities directly expands privileged attack surfaces.
- **Evidence Gathered:** Target account, actor, assigned role, source IP, command, and timestamp.
- **Recommended Action:** Validate the account creation against authorized onboarding tickets in the PAM/IAM governance system.

---

### R02 — Privilege Escalation
- **Severity:** Critical (for confirmed escalation) / High (for missing role metadata)
- **Trigger Condition:** `status == "success"` AND `action == "change_privilege"`
- **Detailed Evaluation Logic:**
  1. **Confirmed Escalation:** If `target_role` is in configured elevated roles (`["admin", "root", "superuser", "administrator", "global_admin"]`) and `previous_role` was lower or omitted:
     - Generates **Critical** alert: *"Privilege escalation detected: Target elevated from role '{previous_role}' to '{target_role}' by '{actor}'."*
  2. **Known Downgrade:** If `previous_role` was elevated and `target_role` is non-elevated (e.g. viewer, user):
     - **MUST NOT** alert as escalation! (Excluded by design).
  3. **Missing Role Information:** If neither role field is supplied:
     - Produces a **High** review alert: *"Privilege change requires review: Role transition details omitted in event log."*

---

### R03 — Audit Logs Cleared
- **Severity:** Critical
- **Trigger Condition:** `status == "success"` AND `action == "clear_logs"`
- **Rationale:** Log clearing is an urgent defense evasion tactic executed by compromised privileged accounts or malware to obscure forensic analysis.
- **Recommended Action:** Immediately isolate origin endpoint IP, alert SOC incident response, and recover mirror logs from write-once / immutable storage.

---

### R04 — Security Monitoring Disabled
- **Severity:** Critical
- **Trigger Condition:** `status == "success"` AND `action == "disable_security"`
- **Rationale:** Deliberate disabling or tampering with EDR agents, telemetry collectors, or host firewalls.
- **Recommended Action:** Re-enable monitoring agent remotely, verify process integrity, and inspect host for unauthorized persistence mechanisms.

---

### R05 — Account Deleted
- **Severity:** High
- **Trigger Condition:** `status == "success"` AND `action == "delete_user"`
- **Rationale:** Administrative account deprovisioning must align with documented HR and IAM change controls.
- **Recommended Action:** Confirm offboarding request ticket with directory lifecycle management and audit recent activity by deleted account.

---

### R06 — Administrator Password Reset
- **Severity:** High
- **Trigger Condition:** `status == "success"` AND `action == "reset_admin_password"`
- **Rationale:** Direct password rotation on privileged accounts can indicate credential hijacking. Ordinary `reset_password` events are excluded.
- **Recommended Action:** Contact account owner out-of-band to confirm rotation justification and verify MFA enrollment.

---

### R07 — Sensitive Data Export
- **Severity:** High
- **Trigger Condition:** `status == "success"` AND `action == "export_sensitive"`
- **Rationale:** Bulk extraction of sensitive data or databases poses high data exfiltration risk.
- **Recommended Action:** Verify business justification, data classification scope, and DLP approval reference.

---

### R08 — After-Hours Administrative Activity
- **Severity:** Medium
- **Trigger Condition:** `status == "success"` AND administrative action performed outside configured business hours (Default: `08:00–18:00 UTC`).
- **Exclusions & Edge Cases:**
  - Ordinary `login` and `logout` events are explicitly excluded.
  - Supports configurable timezones (e.g. `UTC`, `America/New_York`, `Asia/Kolkata`).
  - Supports overnight business shifts (e.g. `20:00` to `04:00`).
- **Recommended Action:** Cross-reference emergency change management authorization ticket and on-call rotation schedule.

---

### R09 — Repeated Failed Logins (Brute Force / Credential Stuffing)
- **Severity:** High
- **Trigger Condition:** $\ge 5$ failed login attempts for the same `actor` and `source_ip` within a rolling 10-minute window.
- **Correlation & Suppression Logic:**
  - Events are sorted chronologically by `timestamp` before correlation.
  - When the 5th failure is observed, an alert is triggered.
  - **Burst Suppression:** Subsequent failed logins occurring within the suppression window (default 10 minutes) are correlated to the active alert without generating redundant alert notifications.

---

### R10 — Explicitly Unapproved Privilege Operation
- **Severity:** Critical
- **Trigger Condition:** `status == "success"` AND `action in ("create_admin", "change_privilege")` AND `approved == false`.
- **Nuance:**
  - `approved == None` (missing data) is treated as **unknown**, NOT explicitly unauthorized.
  - Only explicit log evidence indicating denied approval triggers this critical alert.
