from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator

VALID_SEVERITIES = {"Critical", "High", "Medium", "Low"}
VALID_REVIEW_STATUSES = {"Open", "Investigating", "Resolved", "False Positive"}

class ReviewHistoryRead(BaseModel):
    id: str
    alert_id: str
    previous_status: str
    new_status: str
    note: str
    author: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at")
    @classmethod
    def validate_created_at_tz(cls, v: datetime) -> datetime:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AlertReviewUpdate(BaseModel):
    review_status: str
    note: str = Field(..., min_length=2, max_length=2000)
    author: Optional[str] = Field("Security Analyst", max_length=100)


class AlertRead(BaseModel):
    id: str
    workspace_id: str
    rule_code: str
    rule_version: int
    severity: str
    trigger_time: datetime
    actor: str
    target: str
    source_ip: str
    reason: str
    evidence_json: str
    recommended_action: str
    review_status: str
    is_active: bool
    deactivation_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    event_ids: List[str] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("trigger_time", "created_at", "updated_at")
    @classmethod
    def validate_alert_tz(cls, v: datetime) -> datetime:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AlertDetail(AlertRead):
    parsed_evidence: Optional[Dict[str, Any]] = None
    correlated_events: List[Any] = []
    reviews: List[ReviewHistoryRead] = []


class AlertListResponse(BaseModel):
    items: List[AlertRead]
    total: int
    page: int
    page_size: int
    total_pages: int
