import json
import pytest
from app.models import ActivityEvent, ImportBatch
from app.services.ingestion_service import (
    preview_import_file,
    commit_import_file,
)


def test_valid_json_ingestion(authenticated_client, db_session):
    client, ws = authenticated_client

    events = [
        {
            "timestamp": "2026-10-10T10:00:00Z",
            "actor": "alex_admin",
            "action": "login",
            "target": "sso_portal",
            "status": "success",
            "source_ip": "10.0.10.15",
            "actor_role": "admin",
            "approved": True,
        },
        {
            "timestamp": "2026-10-10T10:05:00Z",
            "actor": "alex_admin",
            "action": "update_config",
            "target": "nginx",
            "status": "success",
            "source_ip": "10.0.10.15",
            "command": "nginx -s reload",
            "approved": True,
        },
    ]
    json_bytes = json.dumps(events).encode("utf-8")

    # Preview
    preview = preview_import_file(json_bytes, "test.json", db_session, ws.id)
    assert preview.total_rows == 2
    assert preview.valid_rows_count == 2
    assert preview.error_count == 0
    assert preview.duplicate_count == 0

    # Commit
    res = commit_import_file(json_bytes, "test.json", db_session, ws.id)
    assert res.imported_count == 2
    assert res.duplicate_count == 0

    db_events = db_session.query(ActivityEvent).filter(ActivityEvent.workspace_id == ws.id).all()
    assert len(db_events) == 2


def test_duplicate_prevention(authenticated_client, db_session):
    client, ws = authenticated_client

    events = [
        {
            "timestamp": "2026-10-10T10:00:00Z",
            "actor": "alex_admin",
            "action": "login",
            "target": "sso_portal",
            "status": "success",
            "source_ip": "10.0.10.15",
            "approved": True,
        }
    ]
    content = json.dumps(events).encode("utf-8")

    # First commit
    res1 = commit_import_file(content, "batch1.json", db_session, ws.id)
    assert res1.imported_count == 1
    assert res1.duplicate_count == 0

    # Second commit with exact same event
    res2 = commit_import_file(content, "batch2.json", db_session, ws.id)
    assert res2.imported_count == 0
    assert res2.duplicate_count == 1

    # Total in DB must still be 1
    total = db_session.query(ActivityEvent).filter(ActivityEvent.workspace_id == ws.id).count()
    assert total == 1


def test_atomic_rollback_on_batch_error(authenticated_client, db_session):
    client, ws = authenticated_client

    # A batch with 2 valid rows and 1 invalid row
    csv_content = """timestamp,actor,action,target,status,source_ip
2026-10-10T10:00:00Z,admin1,login,portal,success,10.0.0.1
invalid-timestamp-no-tz,admin2,login,portal,success,10.0.0.2
2026-10-10T10:10:00Z,admin3,login,portal,success,10.0.0.3
"""
    csv_bytes = csv_content.encode("utf-8")

    preview = preview_import_file(csv_bytes, "test_mixed.csv", db_session, ws.id)
    assert preview.error_count == 1
    assert preview.errors[0].row_number == 2
    assert "timestamp" in preview.errors[0].field.lower()

    # Attempting to commit must raise ValueError and save NOTHING
    with pytest.raises(ValueError) as excinfo:
        commit_import_file(csv_bytes, "test_mixed.csv", db_session, ws.id)

    assert "rejected" in str(excinfo.value).lower()

    # Verify zero events were persisted (atomic import requirement)
    assert db_session.query(ActivityEvent).filter(ActivityEvent.workspace_id == ws.id).count() == 0


def test_invalid_action_and_ip_validation(authenticated_client, db_session):
    client, ws = authenticated_client

    # Row 1: invalid normalized action
    # Row 2: invalid IP address
    csv_content = """timestamp,actor,action,target,status,source_ip
2026-10-10T10:00:00Z,admin1,fake_unsupported_action,portal,success,10.0.0.1
2026-10-10T10:05:00Z,admin2,login,portal,success,999.888.777.666
"""
    preview = preview_import_file(csv_content.encode("utf-8"), "invalid.csv", db_session, ws.id)
    assert preview.error_count == 2
    assert preview.errors[0].row_number == 1
    assert "action" in preview.errors[0].field.lower()
    assert preview.errors[1].row_number == 2
    assert "source_ip" in preview.errors[1].field.lower()


def test_upload_file_size_limit(authenticated_client, db_session):
    client, ws = authenticated_client

    # 6 MB payload exceeds 5 MB limit
    huge_payload = b"A" * (6 * 1024 * 1024)
    with pytest.raises(ValueError) as exc:
        preview_import_file(huge_payload, "huge.csv", db_session, ws.id)
    assert "exceeds maximum allowed limit" in str(exc.value)
