from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc, case

from app.api.deps import get_current_workspace
from app.database import get_db
from app.models import Workspace, ActivityEvent, Alert, RuleConfig, ImportBatch
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardMetrics,
    SeverityCount,
    TimelinePoint,
    TopFlaggedActor,
    ActionDistributionItem,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard_data(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    ws_id = workspace.id

    # Conditions for events
    evt_conds = [ActivityEvent.workspace_id == ws_id]
    if date_from:
        evt_conds.append(ActivityEvent.timestamp >= date_from)
    if date_to:
        evt_conds.append(ActivityEvent.timestamp <= date_to)

    total_events = db.execute(
        select(func.count(ActivityEvent.id)).where(and_(*evt_conds))
    ).scalar_one() or 0

    # Conditions for alerts
    alt_conds = [Alert.workspace_id == ws_id, Alert.is_active == True]
    if date_from:
        alt_conds.append(Alert.trigger_time >= date_from)
    if date_to:
        alt_conds.append(Alert.trigger_time <= date_to)

    total_active_alerts = db.execute(
        select(func.count(Alert.id)).where(and_(*alt_conds))
    ).scalar_one() or 0

    critical_alerts = db.execute(
        select(func.count(Alert.id)).where(and_(*alt_conds, Alert.severity == "Critical"))
    ).scalar_one() or 0

    high_alerts = db.execute(
        select(func.count(Alert.id)).where(and_(*alt_conds, Alert.severity == "High"))
    ).scalar_one() or 0

    medium_alerts = db.execute(
        select(func.count(Alert.id)).where(and_(*alt_conds, Alert.severity == "Medium"))
    ).scalar_one() or 0

    open_investigations = db.execute(
        select(func.count(Alert.id)).where(
            and_(
                *alt_conds,
                Alert.review_status.in_(["Open", "Investigating"])
            )
        )
    ).scalar_one() or 0

    # Distinct administrators count
    distinct_admins = db.execute(
        select(func.count(func.distinct(ActivityEvent.actor))).where(
            and_(
                *evt_conds,
                ActivityEvent.action.in_([
                    "create_admin", "change_privilege", "delete_user", "clear_logs",
                    "disable_security", "export_sensitive", "update_config", "reset_admin_password"
                ])
            )
        )
    ).scalar_one() or 0

    # If no privileged actions yet, distinct actors in total
    if distinct_admins == 0:
        distinct_admins = db.execute(
            select(func.count(func.distinct(ActivityEvent.actor))).where(and_(*evt_conds))
        ).scalar_one() or 0

    # Latest import time
    latest_import = db.execute(
        select(func.max(ImportBatch.created_at)).where(ImportBatch.workspace_id == ws_id)
    ).scalar_one()

    # Rules count
    active_rules_count = db.execute(
        select(func.count(RuleConfig.id)).where(
            RuleConfig.workspace_id == ws_id,
            RuleConfig.is_enabled == True
        )
    ).scalar_one() or 0

    total_rules_count = db.execute(
        select(func.count(RuleConfig.id)).where(RuleConfig.workspace_id == ws_id)
    ).scalar_one() or 0

    metrics = DashboardMetrics(
        total_events=total_events,
        total_active_alerts=total_active_alerts,
        critical_alerts=critical_alerts,
        high_alerts=high_alerts,
        medium_alerts=medium_alerts,
        open_investigations=open_investigations,
        distinct_admins=distinct_admins,
        latest_import_time=latest_import,
        active_rules_count=active_rules_count,
        total_rules_count=total_rules_count,
    )

    # Severity distribution
    sev_query = db.execute(
        select(Alert.severity, func.count(Alert.id))
        .where(and_(*alt_conds))
        .group_by(Alert.severity)
    ).all()
    sev_map = {s: c for s, c in sev_query}
    sev_distribution = []
    for sev in ["Critical", "High", "Medium", "Low"]:
        cnt = sev_map.get(sev, 0)
        pct = (cnt / total_active_alerts * 100.0) if total_active_alerts > 0 else 0.0
        sev_distribution.append(SeverityCount(severity=sev, count=cnt, percentage=round(pct, 1)))

    # Activity Timeline (Aggregate by date YYYY-MM-DD)
    # 1. Events by day
    events_by_day_query = db.execute(
        select(func.strftime('%Y-%m-%d', ActivityEvent.timestamp), func.count(ActivityEvent.id))
        .where(and_(*evt_conds))
        .group_by(func.strftime('%Y-%m-%d', ActivityEvent.timestamp))
        .order_by(func.strftime('%Y-%m-%d', ActivityEvent.timestamp))
    ).all()
    events_by_day = {d: c for d, c in events_by_day_query if d}

    # 2. Alerts by day
    alerts_by_day_query = db.execute(
        select(func.strftime('%Y-%m-%d', Alert.trigger_time), func.count(Alert.id))
        .where(and_(*alt_conds))
        .group_by(func.strftime('%Y-%m-%d', Alert.trigger_time))
        .order_by(func.strftime('%Y-%m-%d', Alert.trigger_time))
    ).all()
    alerts_by_day = {d: c for d, c in alerts_by_day_query if d}

    all_days = sorted(set(list(events_by_day.keys()) + list(alerts_by_day.keys())))
    timeline = []
    for d in all_days:
        timeline.append(TimelinePoint(
            date=d,
            event_count=events_by_day.get(d, 0),
            alert_count=alerts_by_day.get(d, 0),
        ))

    # Top flagged actors
    top_actors_query = db.execute(
        select(
            Alert.actor,
            func.count(Alert.id).label("total_alerts"),
            func.sum(case((Alert.severity == "Critical", 1), else_=0)).label("crit_cnt"),
            func.sum(case((Alert.severity == "High", 1), else_=0)).label("high_cnt"),
            func.max(Alert.trigger_time).label("latest_act"),
        )
        .where(and_(*alt_conds))
        .group_by(Alert.actor)
        .order_by(desc("total_alerts"))
        .limit(6)
    ).all()

    top_actors = []
    for row in top_actors_query:
        top_actors.append(TopFlaggedActor(
            actor=row[0],
            total_alerts=row[1],
            critical_alerts=row[2] or 0,
            high_alerts=row[3] or 0,
            latest_activity=row[4],
        ))

    # Action distribution
    action_query = db.execute(
        select(ActivityEvent.action, func.count(ActivityEvent.id))
        .where(and_(*evt_conds))
        .group_by(ActivityEvent.action)
        .order_by(desc(func.count(ActivityEvent.id)))
        .limit(8)
    ).all()
    action_dist = [ActionDistributionItem(action=a, count=c) for a, c in action_query]

    return DashboardResponse(
        metrics=metrics,
        severity_distribution=sev_distribution,
        activity_timeline=timeline,
        top_flagged_actors=top_actors,
        action_distribution=action_dist,
    )
