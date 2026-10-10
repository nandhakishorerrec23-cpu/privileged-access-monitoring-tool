import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc, asc

from app.api.deps import get_current_workspace
from app.database import get_db
from app.models import Workspace, Alert, AlertEventLink, ActivityEvent, AlertReviewHistory
from app.schemas.alert import (
    AlertRead,
    AlertDetail,
    AlertListResponse,
    AlertReviewUpdate,
    ReviewHistoryRead,
    VALID_REVIEW_STATUSES,
)
from app.schemas.event import EventRead

router = APIRouter(prefix="/alerts", tags=["Alerts & Investigations"])

SORTABLE_ALERT_COLS = {
    "trigger_time": Alert.trigger_time,
    "severity": Alert.severity,
    "rule_code": Alert.rule_code,
    "review_status": Alert.review_status,
    "actor": Alert.actor,
}


@router.get("", response_model=AlertListResponse)
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    severity: Optional[str] = Query(None),
    rule_code: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("trigger_time"),
    sort_order: str = Query("desc"),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    ws_id = workspace.id
    conds = [Alert.workspace_id == ws_id]

    if severity:
        conds.append(Alert.severity == severity.strip())
    if rule_code:
        conds.append(Alert.rule_code == rule_code.strip().upper())
    if actor:
        conds.append(Alert.actor == actor.strip())
    if review_status:
        conds.append(Alert.review_status == review_status.strip())
    if is_active is not None:
        conds.append(Alert.is_active == is_active)
    if date_from:
        conds.append(Alert.trigger_time >= date_from)
    if date_to:
        conds.append(Alert.trigger_time <= date_to)

    total = db.execute(select(func.count(Alert.id)).where(and_(*conds))).scalar_one() or 0

    sort_col = SORTABLE_ALERT_COLS.get(sort_by, Alert.trigger_time)
    order_clause = desc(sort_col) if sort_order.lower() == "desc" else asc(sort_col)

    offset = (page - 1) * page_size
    stmt = (
        select(Alert)
        .where(and_(*conds))
        .order_by(order_clause)
        .offset(offset)
        .limit(page_size)
    )
    alerts = db.execute(stmt).scalars().all()

    # Get linked event IDs
    alert_ids = [a.id for a in alerts]
    links_stmt = select(AlertEventLink.alert_id, AlertEventLink.event_id).where(
        AlertEventLink.alert_id.in_(alert_ids)
    )
    links = db.execute(links_stmt).all()
    alt_to_events: dict[str, list[str]] = {}
    for aid, eid in links:
        if aid not in alt_to_events:
            alt_to_events[aid] = []
        alt_to_events[aid].append(eid)

    items = []
    for a in alerts:
        item = AlertRead.model_validate(a)
        item.event_ids = alt_to_events.get(a.id, [])
        items.append(item)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return AlertListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert_detail(
    alert_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    stmt = select(Alert).where(
        Alert.id == alert_id,
        Alert.workspace_id == workspace.id
    )
    alert = db.execute(stmt).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found in active workspace.")

    # Correlated events
    events_stmt = (
        select(ActivityEvent)
        .join(AlertEventLink, AlertEventLink.event_id == ActivityEvent.id)
        .where(AlertEventLink.alert_id == alert.id)
        .order_by(ActivityEvent.timestamp.asc())
    )
    correlated = db.execute(events_stmt).scalars().all()
    correlated_reads = [EventRead.model_validate(e) for e in correlated]

    # Review history
    history_stmt = (
        select(AlertReviewHistory)
        .where(AlertReviewHistory.alert_id == alert.id)
        .order_by(AlertReviewHistory.created_at.desc())
    )
    reviews = db.execute(history_stmt).scalars().all()
    review_reads = [ReviewHistoryRead.model_validate(r) for r in reviews]

    parsed_evidence = {}
    if alert.evidence_json:
        try:
            parsed_evidence = json.loads(alert.evidence_json)
        except Exception:
            parsed_evidence = {"raw": alert.evidence_json}

    detail = AlertDetail.model_validate(alert)
    detail.event_ids = [e.id for e in correlated]
    detail.parsed_evidence = parsed_evidence
    detail.correlated_events = correlated_reads
    detail.reviews = review_reads

    return detail


@router.post("/{alert_id}/review", response_model=AlertDetail)
def update_alert_review(
    alert_id: str,
    review_data: AlertReviewUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    if review_data.review_status not in VALID_REVIEW_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review status '{review_data.review_status}'. Must be one of: {', '.join(VALID_REVIEW_STATUSES)}",
        )

    stmt = select(Alert).where(
        Alert.id == alert_id,
        Alert.workspace_id == workspace.id
    )
    alert = db.execute(stmt).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found in active workspace.")

    previous_status = alert.review_status
    now = datetime.now(timezone.utc)

    # Update alert review status
    alert.review_status = review_data.review_status
    alert.updated_at = now

    # Add history record
    history_entry = AlertReviewHistory(
        alert_id=alert.id,
        workspace_id=workspace.id,
        previous_status=previous_status,
        new_status=review_data.review_status,
        note=review_data.note.strip(),
        author=(review_data.author or "Security Analyst").strip(),
        created_at=now,
    )
    db.add(history_entry)
    db.commit()
    db.refresh(alert)

    return get_alert_detail(alert_id, workspace, db)


@router.get("/{alert_id}/history", response_model=List[ReviewHistoryRead])
def get_alert_review_history(
    alert_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    stmt = (
        select(AlertReviewHistory)
        .where(
            AlertReviewHistory.alert_id == alert_id,
            AlertReviewHistory.workspace_id == workspace.id
        )
        .order_by(AlertReviewHistory.created_at.desc())
    )
    history = db.execute(stmt).scalars().all()
    return [ReviewHistoryRead.model_validate(h) for h in history]
