import os
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_workspace
from app.config import settings
from app.database import get_db
from app.models import Workspace
from app.schemas.event import EventCreate
from app.schemas.import_schemas import (
    ImportPreviewResponse,
    ImportCommitResponse,
    ManualSimulateResponse,
)
from app.services.ingestion_service import (
    preview_import_file,
    commit_import_file,
    simulate_manual_event,
)
from app.services.sample_data_service import seed_sample_dataset_into_workspace

router = APIRouter(prefix="/ingest", tags=["Log Ingestion & Simulation"])


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_upload(
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    """
    Validates CSV or JSON file content and provides atomic preview.
    Displays row numbers and explanations for errors without saving anything to DB.
    """
    filename = file.filename or "upload.csv"
    try:
        content_bytes = await file.read()
        preview = preview_import_file(content_bytes, filename, db, workspace.id)
        return preview
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File preview processing failed: {str(e)}")


@router.post("/commit", response_model=ImportCommitResponse)
async def commit_upload(
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    """
    Atomically commits validated CSV or JSON events into the active guest workspace.
    If any row fails validation, the entire batch is rejected without saving.
    Runs detection engine and returns detailed ingestion results.
    """
    filename = file.filename or "upload.csv"
    try:
        content_bytes = await file.read()
        commit_res = commit_import_file(content_bytes, filename, db, workspace.id)
        return commit_res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File ingestion failed: {str(e)}")


@router.post("/sample", response_model=Dict[str, Any])
def load_sample_dataset(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    """
    Loads the comprehensive deterministic synthetic demo dataset into the active guest workspace.
    Idempotent: Re-calling skips existing fingerprints.
    """
    result = seed_sample_dataset_into_workspace(db, workspace.id)
    return result


@router.post("/simulate", response_model=ManualSimulateResponse)
def simulate_event(
    event_payload: EventCreate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    """
    Simulates a single administrative activity event using the same canonical schema,
    validation, persistence, and detection pipeline as bulk file imports.
    """
    try:
        data_dict = event_payload.model_dump()
        response = simulate_manual_event(db, workspace.id, data_dict)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation failed: {str(e)}")


@router.get("/samples/download/{file_format}")
def download_sample_template(file_format: str):
    """
    Downloads downloadable sample CSV or JSON files.
    """
    fmt = file_format.lower().strip()
    sample_dir = settings.ROOT_DIR / "sample-data"

    if fmt == "csv":
        filepath = sample_dir / "sentinel_synthetic_events.csv"
        media_type = "text/csv"
        filename = "sentinel_sample_events.csv"
    elif fmt == "json":
        filepath = sample_dir / "sentinel_synthetic_events.json"
        media_type = "application/json"
        filename = "sentinel_sample_events.json"
    elif fmt == "invalid-csv":
        filepath = sample_dir / "invalid_events_sample.csv"
        media_type = "text/csv"
        filename = "sentinel_invalid_events_sample.csv"
    else:
        raise HTTPException(status_code=400, detail="Invalid format requested. Choose 'csv' or 'json'.")

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Sample file {filepath.name} not found.")

    with open(filepath, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
