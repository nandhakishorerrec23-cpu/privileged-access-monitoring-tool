from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class RowValidationError(BaseModel):
    row_number: int
    field: Optional[str] = None
    message: str
    raw_data: Optional[Dict[str, Any]] = None

class ImportPreviewResponse(BaseModel):
    filename: str
    file_format: str
    total_rows: int
    valid_rows_count: int
    error_count: int
    duplicate_count: int
    new_rows_count: int
    errors: List[RowValidationError]
    sample_preview: List[Dict[str, Any]]  # first up to 10 rows
    preview_token: Optional[str] = None

class ImportCommitResponse(BaseModel):
    batch_id: str
    filename: str
    total_rows: int
    imported_count: int
    duplicate_count: int
    rejected_count: int
    alerts_generated: int
    message: str

class ManualSimulateResponse(BaseModel):
    event_id: str
    fingerprint: str
    is_duplicate: bool
    alerts_generated: int
    message: str
