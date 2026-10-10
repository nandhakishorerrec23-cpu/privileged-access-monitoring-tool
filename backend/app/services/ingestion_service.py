import csv
import io
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.models import ActivityEvent, ImportBatch
from app.schemas.event import EventBase, NORMALIZED_ACTIONS
from app.schemas.import_schemas import (
    RowValidationError,
    ImportPreviewResponse,
    ImportCommitResponse,
    ManualSimulateResponse,
)
from app.services.detection_engine import run_detection_pipeline


def compute_event_fingerprint(event_data: Dict[str, Any]) -> str:
    """
    Computes a deterministic SHA-256 fingerprint from normalized canonical fields.
    """
    ts = event_data.get("timestamp")
    if isinstance(ts, datetime):
        ts_str = ts.astimezone(timezone.utc).isoformat()
    else:
        ts_str = str(ts or "").strip()

    actor = str(event_data.get("actor") or "").strip().lower()
    action = str(event_data.get("action") or "").strip().lower()
    target = str(event_data.get("target") or "").strip().lower()
    status = str(event_data.get("status") or "").strip().lower()
    source_ip = str(event_data.get("source_ip") or "").strip().lower()
    actor_role = str(event_data.get("actor_role") or "").strip().lower()
    target_role = str(event_data.get("target_role") or "").strip().lower()
    prev_role = str(event_data.get("previous_role") or "").strip().lower()
    cmd = str(event_data.get("command") or "").strip()
    
    appr = event_data.get("approved")
    appr_str = "none" if appr is None else str(bool(appr)).lower()
    
    appr_ref = str(event_data.get("approval_reference") or "").strip().lower()
    details = str(event_data.get("details") or "").strip().lower()

    payload = f"{ts_str}|{actor}|{action}|{target}|{status}|{source_ip}|{actor_role}|{target_role}|{prev_role}|{cmd}|{appr_str}|{appr_ref}|{details}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_boolean_field(val: Any) -> Optional[bool]:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("true", "1", "yes", "t", "y"):
        return True
    if s in ("false", "0", "no", "f", "n"):
        return False
    if s in ("", "null", "none", "unknown"):
        return None
    raise ValueError(f"Invalid boolean value: '{val}'. Expected true, false, or empty.")


CANONICAL_KEY_ALIASES = {
    "timestamp": "timestamp",
    "timestamp (utc)": "timestamp",
    "timestamp(utc)": "timestamp",
    "trigger_time": "timestamp",
    "time": "timestamp",
    "datetime": "timestamp",
    "date_time": "timestamp",
    "@timestamp": "timestamp",
    "event_time": "timestamp",
    "event_timestamp": "timestamp",

    "actor": "actor",
    "actor_name": "actor",
    "user": "actor",
    "username": "actor",
    "admin": "actor",
    "account": "actor",

    "action": "action",
    "event_action": "action",
    "operation": "action",
    "activity": "action",

    "target": "target",
    "target_name": "target",
    "resource": "target",
    "target_user": "target",
    "target_account": "target",

    "status": "status",
    "result": "status",
    "outcome": "status",

    "source_ip": "source_ip",
    "source ip": "source_ip",
    "sourceip": "source_ip",
    "ip": "source_ip",
    "ip_address": "source_ip",
    "client_ip": "source_ip",
    "src_ip": "source_ip",

    "actor_role": "actor_role",
    "actor role": "actor_role",
    "actorrole": "actor_role",

    "target_role": "target_role",
    "target role": "target_role",
    "targetrole": "target_role",

    "previous_role": "previous_role",
    "previous role": "previous_role",
    "previousrole": "previous_role",
    "prev_role": "previous_role",

    "approved": "approved",
    "is_approved": "approved",

    "approval_reference": "approval_reference",
    "approval reference": "approval_reference",
    "approval_ref": "approval_reference",
    "approvalref": "approval_reference",

    "command": "command",
    "command_line": "command",
    "cmd": "command",

    "details": "details",
    "detail": "details",
    "description": "details",
    "notes": "details",
}


def normalize_raw_keys(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes dictionary keys from CSV or JSON to canonical field names,
    stripping UTF-8 BOM, extra whitespace, case differences, and formula injection prefixes.
    """
    normalized: Dict[str, Any] = {}
    for k, v in raw.items():
        if k is None:
            continue
        cleaned_k = str(k).strip().lower()
        if cleaned_k.startswith("\ufeff"):
            cleaned_k = cleaned_k.lstrip("\ufeff").strip()
        canonical_k = CANONICAL_KEY_ALIASES.get(cleaned_k, cleaned_k)

        # Neutralize spreadsheet formula injection leading quote if present
        cleaned_v = v
        if isinstance(cleaned_v, str) and cleaned_v.startswith("'") and len(cleaned_v) > 1:
            if cleaned_v[1] in ("=", "+", "-", "@", "\t", "\r", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
                cleaned_v = cleaned_v[1:]

        normalized[canonical_k] = cleaned_v
    return normalized


def parse_raw_row(raw: Dict[str, Any], row_num: int) -> Tuple[Optional[Dict[str, Any]], Optional[RowValidationError]]:
    """
    Validates a raw dictionary against the canonical schema.
    Returns (cleaned_dict, None) on success or (None, RowValidationError) on error.
    """
    raw = normalize_raw_keys(raw)
    clean: Dict[str, Any] = {}

    # Check required fields
    required = ["timestamp", "actor", "action", "target", "status", "source_ip"]
    for req in required:
        if req not in raw or raw[req] is None or str(raw[req]).strip() == "":
            return None, RowValidationError(
                row_number=row_num,
                field=req,
                message=f"Missing required canonical field '{req}'.",
                raw_data=raw,
            )

    # Validate boolean
    try:
        clean["approved"] = parse_boolean_field(raw.get("approved"))
    except ValueError as ve:
        return None, RowValidationError(
            row_number=row_num,
            field="approved",
            message=str(ve),
            raw_data=raw,
        )

    # Copy optional string fields
    clean["actor"] = str(raw["actor"]).strip()
    clean["action"] = str(raw["action"]).strip()
    clean["target"] = str(raw["target"]).strip()
    clean["status"] = str(raw["status"]).strip()
    clean["source_ip"] = str(raw["source_ip"]).strip()
    clean["actor_role"] = str(raw.get("actor_role") or "").strip() or None
    clean["target_role"] = str(raw.get("target_role") or "").strip() or None
    clean["previous_role"] = str(raw.get("previous_role") or "").strip() or None
    clean["command"] = str(raw.get("command") or "").strip() or None
    clean["approval_reference"] = str(raw.get("approval_reference") or "").strip() or None
    clean["details"] = str(raw.get("details") or "").strip() or None

    # Parse and validate timestamp
    raw_ts = raw.get("timestamp")
    if isinstance(raw_ts, datetime):
        ts_obj = raw_ts
    else:
        ts_str = str(raw_ts).strip().strip("'\"")
        try:
            # Handle ISO formats
            if ts_str.endswith("Z") or ts_str.endswith("z"):
                ts_str = ts_str[:-1] + "+00:00"
            ts_obj = datetime.fromisoformat(ts_str)
        except Exception:
            return None, RowValidationError(
                row_number=row_num,
                field="timestamp",
                message=f"Invalid ISO 8601 timestamp: '{raw_ts}'. Must include timezone, e.g. 2026-10-10T14:30:00Z.",
                raw_data=raw,
            )

    if ts_obj.tzinfo is None:
        return None, RowValidationError(
            row_number=row_num,
            field="timestamp",
            message=f"Timestamp '{raw_ts}' is missing required timezone information.",
            raw_data=raw,
        )
    clean["timestamp"] = ts_obj.astimezone(timezone.utc)

    # Validate using Pydantic model
    try:
        validated = EventBase(**clean)
        return validated.model_dump(), None
    except ValidationError as e:
        first_err = e.errors()[0]
        field_name = str(first_err["loc"][0]) if first_err["loc"] else "unknown"
        return None, RowValidationError(
            row_number=row_num,
            field=field_name,
            message=first_err["msg"],
            raw_data=raw,
        )


def parse_and_validate_file_content(
    content_bytes: bytes,
    filename: str,
    db: Session,
    workspace_id: str,
) -> Tuple[List[Dict[str, Any]], List[RowValidationError], int, int]:
    """
    Parses CSV or JSON file content, validates each row, and checks duplicates against workspace.
    Returns: (valid_rows, errors, duplicate_count, new_count)
    """
    # Size check
    if len(content_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(f"File size ({len(content_bytes) / 1024 / 1024:.2f} MB) exceeds maximum allowed limit of 5 MB.")

    is_json = filename.lower().endswith(".json")
    is_csv = filename.lower().endswith(".csv")
    if not is_json and not is_csv:
        raise ValueError("Unsupported file format. Only .csv and .json files are accepted.")

    # Decode handling UTF-8 and UTF-8 BOM
    try:
        text_content = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("File encoding error: File must be valid UTF-8 or UTF-8 BOM encoded.")

    raw_rows: List[Dict[str, Any]] = []

    if is_json:
        try:
            parsed_json = json.loads(text_content)
            if not isinstance(parsed_json, list):
                raise ValueError("JSON file root must be a JSON array (list of event objects).")
            raw_rows = parsed_json
        except json.JSONDecodeError as jde:
            raise ValueError(f"Malformed JSON syntax: {jde.msg} at line {jde.lineno}, column {jde.colno}.")
    else:
        # CSV parsing
        f = io.StringIO(text_content)
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV file is empty or missing headers.")
        for row in reader:
            raw_rows.append(row)

    if len(raw_rows) > settings.MAX_UPLOAD_ROWS:
        raise ValueError(f"File contains {len(raw_rows)} rows, exceeding maximum allowed limit of {settings.MAX_UPLOAD_ROWS} rows.")

    if len(raw_rows) == 0:
        raise ValueError("File contains no records to ingest.")

    # Existing fingerprints in workspace
    existing_fp_stmt = select(ActivityEvent.fingerprint).where(ActivityEvent.workspace_id == workspace_id)
    existing_fps = set(db.execute(existing_fp_stmt).scalars().all())

    valid_rows: List[Dict[str, Any]] = []
    errors: List[RowValidationError] = []
    seen_in_batch_fps = set()
    duplicate_count = 0

    for idx, raw in enumerate(raw_rows, start=1):
        cleaned, err = parse_raw_row(raw, idx)
        if err:
            errors.append(err)
        else:
            fp = compute_event_fingerprint(cleaned)
            cleaned["fingerprint"] = fp
            
            if fp in existing_fps or fp in seen_in_batch_fps:
                duplicate_count += 1
                cleaned["is_duplicate"] = True
            else:
                seen_in_batch_fps.add(fp)
                cleaned["is_duplicate"] = False
            
            valid_rows.append(cleaned)

    new_count = len([r for r in valid_rows if not r.get("is_duplicate")])
    return valid_rows, errors, duplicate_count, new_count


def preview_import_file(
    content_bytes: bytes,
    filename: str,
    db: Session,
    workspace_id: str,
) -> ImportPreviewResponse:
    valid_rows, errors, duplicate_count, new_count = parse_and_validate_file_content(
        content_bytes, filename, db, workspace_id
    )
    
    file_fmt = "json" if filename.lower().endswith(".json") else "csv"
    
    sample_preview = []
    for r in valid_rows[:10]:
        preview_item = dict(r)
        if isinstance(preview_item.get("timestamp"), datetime):
            preview_item["timestamp"] = preview_item["timestamp"].isoformat()
        sample_preview.append(preview_item)

    return ImportPreviewResponse(
        filename=filename,
        file_format=file_fmt,
        total_rows=len(valid_rows) + len(errors),
        valid_rows_count=len(valid_rows),
        error_count=len(errors),
        duplicate_count=duplicate_count,
        new_rows_count=new_count,
        errors=errors[:100],  # Return up to first 100 errors
        sample_preview=sample_preview,
    )


def commit_import_file(
    content_bytes: bytes,
    filename: str,
    db: Session,
    workspace_id: str,
) -> ImportCommitResponse:
    valid_rows, errors, duplicate_count, new_count = parse_and_validate_file_content(
        content_bytes, filename, db, workspace_id
    )

    if errors:
        raise ValueError(f"Import rejected: Batch contains {len(errors)} validation errors. Fix row errors before committing.")

    file_fmt = "json" if filename.lower().endswith(".json") else "csv"
    now = datetime.now(timezone.utc)

    # Create Batch
    batch = ImportBatch(
        workspace_id=workspace_id,
        filename=filename,
        file_format=file_fmt,
        total_rows=len(valid_rows),
        imported_count=new_count,
        duplicate_count=duplicate_count,
        rejected_count=0,
        created_at=now,
    )
    db.add(batch)
    db.flush()

    new_events = []
    for r in valid_rows:
        if r.get("is_duplicate"):
            continue

        evt = ActivityEvent(
            workspace_id=workspace_id,
            batch_id=batch.id,
            fingerprint=r["fingerprint"],
            timestamp=r["timestamp"],
            actor=r["actor"],
            action=r["action"],
            target=r["target"],
            status=r["status"],
            source_ip=r["source_ip"],
            actor_role=r.get("actor_role"),
            target_role=r.get("target_role"),
            previous_role=r.get("previous_role"),
            command=r.get("command"),
            approved=r.get("approved"),
            approval_reference=r.get("approval_reference"),
            details=r.get("details"),
            created_at=now,
        )
        db.add(evt)
        new_events.append(evt)

    db.commit()

    # Run detection pipeline
    analysis = run_detection_pipeline(db, workspace_id, trigger_type="ingest")

    return ImportCommitResponse(
        batch_id=batch.id,
        filename=filename,
        total_rows=len(valid_rows),
        imported_count=new_count,
        duplicate_count=duplicate_count,
        rejected_count=0,
        alerts_generated=analysis.alerts_created,
        message=f"Successfully processed {len(valid_rows)} records. {new_count} new events imported, {duplicate_count} duplicates skipped. {analysis.alerts_created} new alerts generated.",
    )


def simulate_manual_event(
    db: Session,
    workspace_id: str,
    event_data: Dict[str, Any],
) -> ManualSimulateResponse:
    cleaned, err = parse_raw_row(event_data, 1)
    if err:
        raise ValueError(f"Simulation error: {err.message} (field: {err.field})")

    fp = compute_event_fingerprint(cleaned)
    now = datetime.now(timezone.utc)

    # Check duplicate
    stmt = select(ActivityEvent).where(
        ActivityEvent.workspace_id == workspace_id,
        ActivityEvent.fingerprint == fp
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        return ManualSimulateResponse(
            event_id=existing.id,
            fingerprint=fp,
            is_duplicate=True,
            alerts_generated=0,
            message="Event with identical canonical fingerprint already exists in this workspace. No duplicate created.",
        )

    # Create batch for manual simulation
    batch = ImportBatch(
        workspace_id=workspace_id,
        filename="Manual Event Simulation",
        file_format="manual",
        total_rows=1,
        imported_count=1,
        duplicate_count=0,
        rejected_count=0,
        created_at=now,
    )
    db.add(batch)
    db.flush()

    evt = ActivityEvent(
        workspace_id=workspace_id,
        batch_id=batch.id,
        fingerprint=fp,
        timestamp=cleaned["timestamp"],
        actor=cleaned["actor"],
        action=cleaned["action"],
        target=cleaned["target"],
        status=cleaned["status"],
        source_ip=cleaned["source_ip"],
        actor_role=cleaned.get("actor_role"),
        target_role=cleaned.get("target_role"),
        previous_role=cleaned.get("previous_role"),
        command=cleaned.get("command"),
        approved=cleaned.get("approved"),
        approval_reference=cleaned.get("approval_reference"),
        details=cleaned.get("details"),
        created_at=now,
    )
    db.add(evt)
    db.commit()

    analysis = run_detection_pipeline(db, workspace_id, trigger_type="simulate")

    return ManualSimulateResponse(
        event_id=evt.id,
        fingerprint=fp,
        is_duplicate=False,
        alerts_generated=analysis.alerts_created,
        message=f"Event simulated successfully. Fingerprint: {fp[:12]}... Generated {analysis.alerts_created} alerts.",
    )
