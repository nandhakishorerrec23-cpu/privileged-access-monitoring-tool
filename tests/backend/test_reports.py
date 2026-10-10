from app.schemas.report import ReportFilterParams
from app.services.ingestion_service import simulate_manual_event
from app.services.report_service import (
    sanitize_csv_cell,
    generate_events_csv,
    generate_alerts_csv,
    generate_audit_json,
    generate_printable_html_report,
)


def test_csv_formula_injection_sanitization():
    # Dangerous spreadsheet prefixes: =, +, -, @, \t, \r
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-5+2") == "'-5+2"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("normal_text") == "normal_text"
    assert sanitize_csv_cell(None) == ""


def test_reports_generation_and_html_escaping(authenticated_client, db_session):
    client, ws = authenticated_client

    # Add event with potentially dangerous characters
    simulate_manual_event(db_session, ws.id, {
        "timestamp": "2026-10-10T10:00:00Z",
        "actor": "<script>alert('xss')</script>",
        "action": "create_admin",
        "target": "target_user",
        "status": "success",
        "source_ip": "10.0.0.1",
        "command": "=cmd|' /C calc'!A0",
        "approved": True,
    })

    filters = ReportFilterParams()

    # 1. Events CSV
    csv_events = generate_events_csv(db_session, ws.id, filters)
    assert "'=cmd|' /C calc'!A0" in csv_events

    # 2. Alerts CSV
    csv_alerts = generate_alerts_csv(db_session, ws.id, filters)
    assert "ALT-" in csv_alerts

    # 3. JSON Audit Report
    audit_json = generate_audit_json(db_session, ws.id, filters)
    assert audit_json["report_id"].startswith("REP-JSON-")
    assert audit_json["summary"]["total_events_in_scope"] == 1
    assert audit_json["summary"]["high_alerts"] == 1

    # 4. Printable HTML Report
    html_rep = generate_printable_html_report(db_session, ws.id, filters)
    assert "<!DOCTYPE html>" in html_rep
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_rep or "&lt;script&gt;" in html_rep
    assert "<script>alert" not in html_rep  # Script tag must be escaped!
    assert "Print / Save as PDF" in html_rep
