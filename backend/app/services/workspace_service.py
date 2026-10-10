import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.config import settings
from app.models import Workspace, RuleConfig, ActivityEvent, Alert, ImportBatch

DEFAULT_RULES = [
    {
        "rule_code": "R01",
        "name": "Administrator Account Created",
        "description": "Flags any successful administrator account creation event (create_admin). New administrative accounts represent significant expansion of privileged attack surface.",
        "severity": "High",
        "is_enabled": True,
        "config": {},
    },
    {
        "rule_code": "R02",
        "name": "Privilege Escalation Detected",
        "description": "Identifies when a lower role is promoted to administrative privileges (admin, root, superuser). If role details are omitted, generates a review alert instead of asserting proven escalation. Explicit downgrades are excluded.",
        "severity": "Critical",
        "is_enabled": True,
        "config": {
            "elevated_roles": ["admin", "root", "superuser", "administrator", "global_admin"]
        },
    },
    {
        "rule_code": "R03",
        "name": "Audit Logs Cleared",
        "description": "Critical alert when audit or security logs are cleared. Log erasure is a hallmark defense evasion tactic by compromised privileged accounts.",
        "severity": "Critical",
        "is_enabled": True,
        "config": {},
    },
    {
        "rule_code": "R04",
        "name": "Security Monitoring Disabled",
        "description": "Flags deliberate attempts to disable security controls, telemetry agents, or monitoring mechanisms.",
        "severity": "Critical",
        "is_enabled": True,
        "config": {},
    },
    {
        "rule_code": "R05",
        "name": "Account Deleted",
        "description": "Detects deletion of user or system accounts by administrators, which may disrupt operations or conceal unauthorized actions.",
        "severity": "High",
        "is_enabled": True,
        "config": {},
    },
    {
        "rule_code": "R06",
        "name": "Administrator Password Reset",
        "description": "Detects direct administrative password resets targeting privileged accounts, which could signify account takeover.",
        "severity": "High",
        "is_enabled": True,
        "config": {},
    },
    {
        "rule_code": "R07",
        "name": "Sensitive Data Export",
        "description": "Monitors bulk or sensitive data export operations executed by privileged users.",
        "severity": "High",
        "is_enabled": True,
        "config": {},
    },
    {
        "rule_code": "R08",
        "name": "After-Hours Administrative Activity",
        "description": "Flags administrative modifications performed outside defined business hours. Routine logins/logouts are excluded. Configurable timezone and business windows supported.",
        "severity": "Medium",
        "is_enabled": True,
        "config": {
            "business_start": "08:00",
            "business_end": "18:00",
            "timezone": "UTC"
        },
    },
    {
        "rule_code": "R09",
        "name": "Repeated Failed Logins (Brute Force / Credential Stuffing)",
        "description": "Alerts when an actor and source IP exceed five failed login attempts within a rolling 10-minute window based on event timestamps, with alert burst suppression.",
        "severity": "High",
        "is_enabled": True,
        "config": {
            "threshold": 5,
            "window_minutes": 10,
            "suppression_window_minutes": 10
        },
    },
    {
        "rule_code": "R10",
        "name": "Explicitly Unapproved Privilege Operation",
        "description": "Triggers critical alert when create_admin or change_privilege occurs with log evidence explicitly stating approved=false. Missing approval data is treated as unknown rather than unauthorized.",
        "severity": "Critical",
        "is_enabled": True,
        "config": {},
    },
]


def init_workspace_rules(db: Session, workspace_id: str):
    """Seed the default 10 detection rules for a new workspace."""
    now = datetime.now(timezone.utc)
    for rule in DEFAULT_RULES:
        rc = RuleConfig(
            workspace_id=workspace_id,
            rule_code=rule["rule_code"],
            name=rule["name"],
            description=rule["description"],
            severity=rule["severity"],
            is_enabled=rule["is_enabled"],
            config_json=json.dumps(rule["config"]),
            version=1,
            updated_at=now,
        )
        db.add(rc)
    db.flush()


def create_guest_workspace(db: Session, name: str = "Demo Guest Workspace") -> Workspace:
    """Create a new isolated guest workspace with secure tokens."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.SESSION_EXPIRE_HOURS)
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_hex(32)

    workspace = Workspace(
        session_token=session_token,
        csrf_token=csrf_token,
        name=name,
        is_demo=True,
        created_at=now,
        last_active_at=now,
        expires_at=expires_at,
    )
    db.add(workspace)
    db.flush()

    init_workspace_rules(db, workspace.id)
    db.commit()
    db.refresh(workspace)
    return workspace


def make_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_workspace_by_token(db: Session, token: str) -> Optional[Workspace]:
    """Retrieve workspace by session token if not expired."""
    if not token:
        return None
    stmt = select(Workspace).where(Workspace.session_token == token)
    workspace = db.execute(stmt).scalar_one_or_none()
    if not workspace:
        return None
    
    now = datetime.now(timezone.utc)
    expires = make_aware(workspace.expires_at)
    # Check expiry
    if expires and expires < now:
        return None

    # Update last_active_at
    workspace.last_active_at = now
    db.commit()
    return workspace


def cleanup_expired_workspaces(db: Session) -> int:
    """Remove expired demo sessions and cascaded records."""
    now = datetime.now(timezone.utc)
    stmt = delete(Workspace).where(Workspace.expires_at < now)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount
