from app.config import settings
from app.services.workspace_service import create_guest_workspace
from app.services.ingestion_service import simulate_manual_event


def test_cross_workspace_isolation(client, db_session):
    # Create workspace A
    ws_a = create_guest_workspace(db_session, name="Workspace A")
    # Create workspace B
    ws_b = create_guest_workspace(db_session, name="Workspace B")

    # Add event to Workspace A
    res = simulate_manual_event(db_session, ws_a.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "user_a",
        "action": "create_admin",
        "target": "admin_a",
        "status": "success",
        "source_ip": "10.0.0.1",
        "approved": True,
    })
    event_id_a = res.event_id

    # Switch client session to Workspace B
    client.cookies.set(settings.SESSION_COOKIE_NAME, ws_b.session_token)
    client.cookies.set(settings.CSRF_COOKIE_NAME, ws_b.csrf_token)
    client.headers[settings.CSRF_HEADER_NAME] = ws_b.csrf_token

    # 1. Workspace B events query must return 0 items
    resp_events = client.get("/api/v1/events")
    assert resp_events.status_code == 200
    assert resp_events.json()["total"] == 0
    assert len(resp_events.json()["items"]) == 0

    # 2. Workspace B alerts query must return 0 items
    resp_alerts = client.get("/api/v1/alerts")
    assert resp_alerts.status_code == 200
    assert resp_alerts.json()["total"] == 0

    # 3. Direct access to Workspace A's event ID must return 404
    resp_detail = client.get(f"/api/v1/events/{event_id_a}")
    assert resp_detail.status_code == 404


def test_csrf_protection_on_state_changes(client, db_session):
    ws = create_guest_workspace(db_session, name="CSRF Test Workspace")
    client.cookies.set(settings.SESSION_COOKIE_NAME, ws.session_token)
    client.cookies.set(settings.CSRF_COOKIE_NAME, ws.csrf_token)

    # State changing request WITHOUT CSRF header
    client.headers.pop(settings.CSRF_HEADER_NAME, None)

    resp = client.post("/api/v1/rules/reanalyze")
    assert resp.status_code == 403
    assert "CSRF" in resp.json()["detail"]

    # Now with valid CSRF header
    client.headers[settings.CSRF_HEADER_NAME] = ws.csrf_token
    resp_valid = client.post("/api/v1/rules/reanalyze")
    assert resp_valid.status_code == 200
