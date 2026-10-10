from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc, asc

from app.api.deps import get_current_workspace
from app.database import get_db
from app.models import Workspace, ActivityEvent, Alert, AlertEventLink
from app.schemas.event import EventRead, EventListResponse
from app.schemas.report import ReportFilterParams
from app.services.report_service import generate_events_csv

router = APIRouter(prefix="/events", tags=["Activity Logs"])

SORTABLE_FIELDS = {
    "timestamp": ActivityEvent.timestamp,
    "actor": ActivityEvent.actor,
    "action": ActivityEvent.action,
    "target": ActivityEvent.target,
    "status": ActivityEvent.status,
    "source_ip": ActivityEvent.source_ip,
}


@router.get("", response_model=EventListResponse)
def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("timestamp"),
    sort_order: str = Query("desc"),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    ws_id = workspace.id
    conds = [ActivityEvent.workspace_id == ws_id]

    if actor:
        conds.append(ActivityEvent.actor == actor.strip())
    if action:
        conds.append(ActivityEvent.action == action.strip().lower())
    if status:
        conds.append(ActivityEvent.status == status.strip().lower())
    if date_from:
        conds.append(ActivityEvent.timestamp >= date_from)
    if date_to:
        conds.append(ActivityEvent.timestamp <= date_to)

    if search:
        s = f"%{search.strip().lower()}%"
        conds.append(
            or_(
                func.lower(ActivityEvent.actor).like(s),
                func.lower(ActivityEvent.target).like(s),
                func.lower(ActivityEvent.action).like(s),
                func.lower(ActivityEvent.source_ip).like(s),
                func.lower(ActivityEvent.command).like(s),
                func.lower(ActivityEvent.details).like(s),
            )
        )

    # Count total
    total = db.execute(
        select(func.count(ActivityEvent.id)).where(and_(*conds))
    ).scalar_one() or 0

    # Sorting
    sort_col = SORTABLE_FIELDS.get(sort_by, ActivityEvent.timestamp)
    order_clause = desc(sort_col) if sort_order.lower() == "desc" else asc(sort_col)

    # Pagination
    offset = (page - 1) * page_size
    stmt = (
        select(ActivityEvent)
        .where(and_(*conds))
        .order_by(order_clause)
        .offset(offset)
        .limit(page_size)
    )
    items = db.execute(stmt).scalars().all()

    # Fetch associated alert IDs for the events
    event_ids = [e.id for e in items]
    alert_links_stmt = select(AlertEventLink.event_id, AlertEventLink.alert_id).where(
        AlertEventLink.event_id.in_(event_ids)
    )
    links = db.execute(alert_links_stmt).all()
    event_to_alerts: dict[str, list[str]] = {}
    for eid, aid in links:
        if eid not in event_to_alerts:
            event_to_alerts[eid] = []
        event_to_alerts[eid].append(aid)

    # Format output
    result_items = []
    for e in items:
        read_obj = EventRead.model_validate(e)
        read_obj.alert_ids = event_to_alerts.get(e.id, [])
        result_items.append(read_obj)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return EventListResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/export")
def export_filtered_events_csv(
    search: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    """
    Exports the FULL filtered event dataset to CSV, not just the currently paged slice.
    """
    filters = ReportFilterParams(
        actor=actor,
        date_from=date_from,
        date_to=date_to,
    )
    csv_content = generate_events_csv(db, workspace.id, filters)
    now_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"sentinel_events_export_{now_str}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{event_id}", response_model=EventRead)
def get_event_detail(
    event_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    stmt = select(ActivityEvent).where(
        ActivityEvent.id == event_id,
        ActivityEvent.workspace_id == workspace.id
    )
    event = db.execute(stmt).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found in active workspace.")

    # Fetch linked alert IDs
    links_stmt = select(AlertEventLink.alert_id).where(AlertEventLink.event_id == event.id)
    alert_ids = [aid for (aid,) in db.execute(links_stmt).all()]

    read_obj = EventRead.model_validate(event)
    read_obj.alert_ids = alert_ids
    return read_obj
