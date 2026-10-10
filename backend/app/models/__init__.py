import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_token = Column(String(64), unique=True, index=True, nullable=False)
    csrf_token = Column(String(64), nullable=False)
    name = Column(String(100), default="Demo Guest Workspace")
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    last_active_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    batches = relationship("ImportBatch", back_populates="workspace", cascade="all, delete-orphan")
    events = relationship("ActivityEvent", back_populates="workspace", cascade="all, delete-orphan")
    rules = relationship("RuleConfig", back_populates="workspace", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="workspace", cascade="all, delete-orphan")
    reviews = relationship("AlertReviewHistory", back_populates="workspace", cascade="all, delete-orphan")
    runs = relationship("AnalysisRun", back_populates="workspace", cascade="all, delete-orphan")


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(20), nullable=False)  # csv, json, manual
    total_rows = Column(Integer, default=0)
    imported_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    workspace = relationship("Workspace", back_populates="batches")
    events = relationship("ActivityEvent", back_populates="batch")


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    batch_id = Column(String(36), ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True)
    fingerprint = Column(String(64), index=True, nullable=False)

    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    actor = Column(String(120), index=True, nullable=False)
    action = Column(String(50), index=True, nullable=False)
    target = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False)  # 'success', 'failed'
    source_ip = Column(String(45), nullable=False)

    actor_role = Column(String(50), nullable=True)
    target_role = Column(String(50), nullable=True)
    previous_role = Column(String(50), nullable=True)
    command = Column(Text, nullable=True)
    approved = Column(Boolean, nullable=True)  # True, False, None (unknown)
    approval_reference = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)

    workspace = relationship("Workspace", back_populates="events")
    batch = relationship("ImportBatch", back_populates="events")
    alert_links = relationship("AlertEventLink", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("workspace_id", "fingerprint", name="uq_workspace_event_fingerprint"),
        Index("ix_workspace_actor_timestamp", "workspace_id", "actor", "timestamp"),
        Index("ix_workspace_action_timestamp", "workspace_id", "action", "timestamp"),
    )


class RuleConfig(Base):
    __tablename__ = "rule_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    rule_code = Column(String(10), nullable=False)  # R01 .. R10
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # Critical, High, Medium, Low
    is_enabled = Column(Boolean, default=True, nullable=False)
    config_json = Column(Text, default="{}", nullable=False)  # JSON string
    version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now)

    workspace = relationship("Workspace", back_populates="rules")

    __table_args__ = (
        UniqueConstraint("workspace_id", "rule_code", name="uq_workspace_rule_code"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    rule_code = Column(String(10), index=True, nullable=False)
    rule_version = Column(Integer, default=1, nullable=False)
    severity = Column(String(20), index=True, nullable=False)  # Critical, High, Medium, Low
    trigger_time = Column(DateTime(timezone=True), index=True, nullable=False)

    actor = Column(String(120), index=True, nullable=False)
    target = Column(String(120), nullable=False)
    source_ip = Column(String(45), nullable=False)

    reason = Column(Text, nullable=False)
    evidence_json = Column(Text, default="{}", nullable=False)
    recommended_action = Column(Text, nullable=False)

    # Review lifecycle
    review_status = Column(String(30), default="Open", index=True, nullable=False)  # Open, Investigating, Resolved, False Positive
    
    # Active detection status (separate from review_status)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    deactivation_reason = Column(Text, nullable=True)

    # Dedup key for reanalysis matching: workspace_id + rule_code + primary_fingerprint
    dedup_key = Column(String(128), index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    workspace = relationship("Workspace", back_populates="alerts")
    event_links = relationship("AlertEventLink", back_populates="alert", cascade="all, delete-orphan")
    reviews = relationship("AlertReviewHistory", back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workspace_alert_dedup", "workspace_id", "dedup_key"),
        Index("ix_workspace_review_status", "workspace_id", "review_status"),
    )


class AlertEventLink(Base):
    __tablename__ = "alert_event_links"

    alert_id = Column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True)
    event_id = Column(String(36), ForeignKey("activity_events.id", ondelete="CASCADE"), primary_key=True)

    alert = relationship("Alert", back_populates="event_links")
    event = relationship("ActivityEvent", back_populates="alert_links")


class AlertReviewHistory(Base):
    __tablename__ = "alert_review_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    previous_status = Column(String(30), nullable=False)
    new_status = Column(String(30), nullable=False)
    note = Column(Text, nullable=False)
    author = Column(String(100), default="Security Analyst", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    alert = relationship("Alert", back_populates="reviews")
    workspace = relationship("Workspace", back_populates="reviews")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    trigger_type = Column(String(30), nullable=False)  # ingest, reanalyze, rule_update
    events_analyzed = Column(Integer, default=0)
    alerts_created = Column(Integer, default=0)
    alerts_deactivated = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    workspace = relationship("Workspace", back_populates="runs")
