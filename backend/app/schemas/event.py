from datetime import datetime, timezone
from ipaddress import ip_address
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

NORMALIZED_ACTIONS = {
    "login",
    "logout",
    "create_user",
    "create_admin",
    "change_privilege",
    "delete_user",
    "reset_password",
    "reset_admin_password",
    "disable_account",
    "enable_account",
    "clear_logs",
    "disable_security",
    "export_sensitive",
    "update_config",
    "execute_command",
}

class EventBase(BaseModel):
    timestamp: datetime
    actor: str = Field(..., min_length=1, max_length=120)
    action: str
    target: str = Field(..., min_length=1, max_length=120)
    status: str
    source_ip: str
    actor_role: Optional[str] = Field(None, max_length=50)
    target_role: Optional[str] = Field(None, max_length=50)
    previous_role: Optional[str] = Field(None, max_length=50)
    command: Optional[str] = None
    approved: Optional[bool] = None
    approval_reference: Optional[str] = Field(None, max_length=100)
    details: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in NORMALIZED_ACTIONS:
            raise ValueError(f"Action '{v}' is not recognized. Must be one of: {', '.join(sorted(NORMALIZED_ACTIONS))}")
        return clean

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in {"success", "failed"}:
            raise ValueError("Status must be either 'success' or 'failed'")
        return clean

    @field_validator("source_ip")
    @classmethod
    def validate_source_ip(cls, v: str) -> str:
        clean = v.strip()
        try:
            ip_address(clean)
        except ValueError:
            raise ValueError(f"'{clean}' is not a valid IPv4 or IPv6 address")
        return clean

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_tz(cls, v: datetime) -> datetime:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    id: str
    workspace_id: str
    batch_id: Optional[str]
    fingerprint: str
    created_at: datetime
    alert_ids: List[str] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at")
    @classmethod
    def validate_created_at_tz(cls, v: datetime) -> datetime:
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class EventListResponse(BaseModel):
    items: List[EventRead]
    total: int
    page: int
    page_size: int
    total_pages: int
