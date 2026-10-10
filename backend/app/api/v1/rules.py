import json
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.api.deps import get_current_workspace
from app.database import get_db
from app.models import Workspace, RuleConfig, Alert
from app.schemas.rule import RuleConfigRead, RuleConfigUpdate, ReanalyzeResponse
from app.services.detection_engine import run_detection_pipeline

router = APIRouter(prefix="/rules", tags=["Detection Rules"])


@router.get("", response_model=List[RuleConfigRead])
def list_workspace_rules(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    stmt = (
        select(RuleConfig)
        .where(RuleConfig.workspace_id == workspace.id)
        .order_by(RuleConfig.rule_code.asc())
    )
    rules = db.execute(stmt).scalars().all()
    
    result = []
    for r in rules:
        cfg_dict = {}
        if r.config_json:
            try:
                cfg_dict = json.loads(r.config_json)
            except Exception:
                cfg_dict = {}
        result.append(RuleConfigRead(
            id=r.id,
            workspace_id=r.workspace_id,
            rule_code=r.rule_code,
            name=r.name,
            description=r.description,
            severity=r.severity,
            is_enabled=r.is_enabled,
            config=cfg_dict,
            version=r.version,
            updated_at=r.updated_at,
        ))
    return result


@router.put("/{rule_code}", response_model=RuleConfigRead)
def update_workspace_rule(
    rule_code: str,
    update_data: RuleConfigUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    code = rule_code.strip().upper()
    stmt = select(RuleConfig).where(
        RuleConfig.workspace_id == workspace.id,
        RuleConfig.rule_code == code
    )
    rule = db.execute(stmt).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{code}' not found in active workspace.")

    now = datetime.now(timezone.utc)
    rule.is_enabled = update_data.is_enabled
    rule.config_json = json.dumps(update_data.config)
    rule.version += 1
    rule.updated_at = now

    db.commit()
    db.refresh(rule)

    return RuleConfigRead(
        id=rule.id,
        workspace_id=rule.workspace_id,
        rule_code=rule.rule_code,
        name=rule.name,
        description=rule.description,
        severity=rule.severity,
        is_enabled=rule.is_enabled,
        config=update_data.config,
        version=rule.version,
        updated_at=rule.updated_at,
    )


@router.post("/reanalyze", response_model=ReanalyzeResponse)
def trigger_workspace_reanalysis(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    """
    Re-evaluates all existing activity logs against the currently active rules and thresholds.
    Preserves analyst notes and review decisions for matching alerts, and deactivates alerts
    for rules that have been disabled or thresholds that no longer match.
    """
    run = run_detection_pipeline(db, workspace.id, trigger_type="reanalyze")

    total_active = db.execute(
        select(func.count(Alert.id)).where(
            Alert.workspace_id == workspace.id,
            Alert.is_active == True
        )
    ).scalar_one() or 0

    return ReanalyzeResponse(
        run_id=run.id,
        events_analyzed=run.events_analyzed,
        alerts_created=run.alerts_created,
        alerts_deactivated=run.alerts_deactivated,
        total_active_alerts=total_active,
        message=f"Reanalysis complete. Analyzed {run.events_analyzed} events. Created {run.alerts_created} new alerts, deactivated {run.alerts_deactivated} alerts. Total active alerts: {total_active}.",
    )
