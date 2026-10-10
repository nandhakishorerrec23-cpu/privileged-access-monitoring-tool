import json
from datetime import datetime, timezone
import pytest
from app.models import ActivityEvent, Alert, AlertReviewHistory
from app.services.ingestion_service import simulate_manual_event
from app.services.detection_engine import run_detection_pipeline


def test_rule_r01_create_admin(authenticated_client, db_session):
    client, ws = authenticated_client

    # Successful create_admin -> High alert
    evt_success = {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "sec_admin",
        "action": "create_admin",
        "target": "new_super_user",
        "status": "success",
        "source_ip": "192.0.2.10",
        "actor_role": "admin",
        "target_role": "admin",
        "approved": True,
    }
    res = simulate_manual_event(db_session, ws.id, evt_success)
    assert res.alerts_generated >= 1

    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R01").all()
    assert len(alerts) == 1
    assert alerts[0].severity == "High"
    assert "new_super_user" in alerts[0].reason

    # Failed create_admin -> Must NOT trigger R01
    evt_failed = {
        "timestamp": "2026-10-10T10:05:00Z",
        "actor": "attacker",
        "action": "create_admin",
        "target": "backdoor_admin",
        "status": "failed",
        "source_ip": "198.51.100.99",
        "actor_role": "guest",
        "approved": False,
    }
    simulate_manual_event(db_session, ws.id, evt_failed)
    alerts_after = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R01").all()
    assert len(alerts_after) == 1  # Still 1, failed event did not generate R01


def test_rule_r02_privilege_escalation_and_downgrade(authenticated_client, db_session):
    client, ws = authenticated_client

    # 1. Successful escalation: lower role to superuser -> Critical alert
    evt_esc = {
        "timestamp": "2026-10-10T10:10:00Z",
        "actor": "admin_one",
        "action": "change_privilege",
        "target": "john_analyst",
        "status": "success",
        "source_ip": "10.0.0.5",
        "previous_role": "analyst",
        "target_role": "superuser",
        "approved": True,
    }
    simulate_manual_event(db_session, ws.id, evt_esc)
    r2_alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R02").all()
    assert len(r2_alerts) == 1
    assert r2_alerts[0].severity == "Critical"
    assert "john_analyst" in r2_alerts[0].reason

    # 2. Known downgrade: admin to viewer -> Must NOT trigger escalation!
    evt_downgrade = {
        "timestamp": "2026-10-10T10:15:00Z",
        "actor": "admin_one",
        "action": "change_privilege",
        "target": "contractor_mike",
        "status": "success",
        "source_ip": "10.0.0.5",
        "previous_role": "admin",
        "target_role": "viewer",
        "approved": True,
    }
    simulate_manual_event(db_session, ws.id, evt_downgrade)
    r2_alerts_after = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R02").all()
    assert len(r2_alerts_after) == 1  # No alert for downgrade!

    # 3. Missing role fields -> Produces High "Requires Review" alert
    evt_missing_role = {
        "timestamp": "2026-10-10T10:20:00Z",
        "actor": "admin_one",
        "action": "change_privilege",
        "target": "svc_daemon",
        "status": "success",
        "source_ip": "10.0.0.5",
        "previous_role": None,
        "target_role": None,
        "approved": True,
    }
    simulate_manual_event(db_session, ws.id, evt_missing_role)
    r2_all = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R02").all()
    assert len(r2_all) == 2
    missing_alert = [a for a in r2_all if "omitted" in a.reason or "review" in a.reason.lower()][0]
    assert missing_alert.severity == "High"


def test_rule_r03_clear_logs(authenticated_client, db_session):
    client, ws = authenticated_client

    # Failed clear_logs -> No alert
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "probe",
        "action": "clear_logs",
        "target": "audit_log",
        "status": "failed",
        "source_ip": "10.0.0.1",
    })
    assert db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R03").count() == 0

    # Successful clear_logs -> Critical alert
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:01:00Z",
        "actor": "bad_actor",
        "action": "clear_logs",
        "target": "audit_log",
        "status": "success",
        "source_ip": "10.0.0.1",
    })
    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R03").all()
    assert len(alerts) == 1
    assert alerts[0].severity == "Critical"


def test_rule_r04_disable_security(authenticated_client, db_session):
    client, ws = authenticated_client

    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "hacker",
        "action": "disable_security",
        "target": "antivirus_agent",
        "status": "success",
        "source_ip": "10.0.0.9",
    })
    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R04").all()
    assert len(alerts) == 1
    assert alerts[0].severity == "Critical"


def test_rule_r05_delete_user(authenticated_client, db_session):
    client, ws = authenticated_client

    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "hr_admin",
        "action": "delete_user",
        "target": "fired_user",
        "status": "success",
        "source_ip": "10.0.0.2",
    })
    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R05").all()
    assert len(alerts) == 1
    assert alerts[0].severity == "High"


def test_rule_r06_reset_admin_password(authenticated_client, db_session):
    client, ws = authenticated_client

    # Ordinary user password reset -> No R06
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "admin",
        "action": "reset_password",
        "target": "intern",
        "status": "success",
        "source_ip": "10.0.0.2",
    })
    assert db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R06").count() == 0

    # Admin password reset -> High alert
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:01:00Z",
        "actor": "admin",
        "action": "reset_admin_password",
        "target": "root",
        "status": "success",
        "source_ip": "10.0.0.2",
    })
    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R06").all()
    assert len(alerts) == 1
    assert alerts[0].severity == "High"


def test_rule_r07_export_sensitive(authenticated_client, db_session):
    client, ws = authenticated_client

    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "db_admin",
        "action": "export_sensitive",
        "target": "credit_cards_db",
        "status": "success",
        "source_ip": "10.0.0.2",
    })
    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R07").all()
    assert len(alerts) == 1
    assert alerts[0].severity == "High"


def test_rule_r08_after_hours_activity(authenticated_client, db_session):
    client, ws = authenticated_client

    # Daytime admin activity (12:00 UTC, inside 08:00 - 18:00) -> No R08
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T12:00:00Z",
        "actor": "alex_admin",
        "action": "update_config",
        "target": "firewall",
        "status": "success",
        "source_ip": "10.0.0.2",
    })
    assert db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R08").count() == 0

    # After-hours ordinary login (02:00 UTC) -> Excluded! No R08
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T02:00:00Z",
        "actor": "alex_admin",
        "action": "login",
        "target": "vpn",
        "status": "success",
        "source_ip": "10.0.0.2",
    })
    assert db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R08").count() == 0

    # After-hours admin change (02:30 UTC, update_config) -> Triggers Medium R08
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T02:30:00Z",
        "actor": "alex_admin",
        "action": "update_config",
        "target": "firewall",
        "status": "success",
        "source_ip": "10.0.0.2",
    })
    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R08").all()
    assert len(alerts) == 1
    assert alerts[0].severity == "Medium"


def test_rule_r09_failed_login_burst_and_suppression(authenticated_client, db_session):
    client, ws = authenticated_client

    actor = "brute_forcer"
    ip = "198.51.100.77"

    # 4 failed logins within 5 minutes -> Below threshold of 5, No R09 alert
    for i in range(4):
        simulate_manual_event(db_session, ws.id, {
            "timestamp": f"2026-10-10T10:0{i}:00Z",
            "actor": actor,
            "action": "login",
            "target": "ssh",
            "status": "failed",
            "source_ip": ip,
        })
    assert db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R09").count() == 0

    # 5th failed login within the 10 min window -> Reaches threshold, triggers R09!
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:05:00Z",
        "actor": actor,
        "action": "login",
        "target": "ssh",
        "status": "failed",
        "source_ip": ip,
    })
    r9_alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R09").all()
    assert len(r9_alerts) == 1
    assert r9_alerts[0].severity == "High"

    # 6th and 7th failed logins within suppression window -> Correlated, NO duplicate alert!
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:06:00Z",
        "actor": actor,
        "action": "login",
        "target": "ssh",
        "status": "failed",
        "source_ip": ip,
    })
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:07:00Z",
        "actor": actor,
        "action": "login",
        "target": "ssh",
        "status": "failed",
        "source_ip": ip,
    })
    r9_alerts_after = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R09").all()
    assert len(r9_alerts_after) == 1  # Still exactly 1 alert, no duplicate explosion!


def test_rule_r10_explicitly_unapproved_operation(authenticated_client, db_session):
    client, ws = authenticated_client

    # 1. approved=None (missing approval metadata) -> Must NOT trigger R10 (unknown != false)
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "alex_admin",
        "action": "create_admin",
        "target": "new_admin_1",
        "status": "success",
        "source_ip": "10.0.0.1",
        "approved": None,
    })
    assert db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R10").count() == 0

    # 2. approved=True -> Must NOT trigger R10
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:05:00Z",
        "actor": "alex_admin",
        "action": "create_admin",
        "target": "new_admin_2",
        "status": "success",
        "source_ip": "10.0.0.1",
        "approved": True,
    })
    assert db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R10").count() == 0

    # 3. approved=False -> Triggers Critical R10!
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:10:00Z",
        "actor": "alex_admin",
        "action": "create_admin",
        "target": "unapproved_admin",
        "status": "success",
        "source_ip": "10.0.0.1",
        "approved": False,
        "approval_reference": "REJECTED-TKT",
    })
    r10_alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R10").all()
    assert len(r10_alerts) == 1
    assert r10_alerts[0].severity == "Critical"
    assert "approved=false" in r10_alerts[0].reason


def test_reanalysis_idempotency_and_preservation(authenticated_client, db_session):
    client, ws = authenticated_client

    # Add an event triggering R01
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "admin_one",
        "action": "create_admin",
        "target": "test_admin",
        "status": "success",
        "source_ip": "10.0.0.1",
        "approved": True,
    })
    alerts = db_session.query(Alert).filter(Alert.workspace_id == ws.id, Alert.rule_code == "R01").all()
    assert len(alerts) == 1
    alert_id = alerts[0].id

    # Analyst changes review status and adds note
    alert = alerts[0]
    alert.review_status = "Investigating"
    hist = AlertReviewHistory(
        alert_id=alert.id,
        workspace_id=ws.id,
        previous_status="Open",
        new_status="Investigating",
        note="Investigating why this admin account was created",
        author="Alice Analyst",
    )
    db_session.add(hist)
    db_session.commit()

    # Run reanalysis
    run = run_detection_pipeline(db_session, ws.id, trigger_type="reanalyze")
    assert run.alerts_created == 0  # No duplicate alerts created!

    # Verify existing alert preserved status and history note
    db_session.refresh(alert)
    assert alert.review_status == "Investigating"
    assert alert.is_active == True
    history = db_session.query(AlertReviewHistory).filter(AlertReviewHistory.alert_id == alert_id).all()
    assert len(history) == 1
    assert history[0].note == "Investigating why this admin account was created"
