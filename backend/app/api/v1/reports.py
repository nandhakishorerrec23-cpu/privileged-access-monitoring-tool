import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_workspace
from app.database import get_db
from app.models import Workspace
from app.schemas.report import ReportFilterParams, AuditReportJSON
from app.services.report_service import (
    generate_alerts_csv,
    generate_events_csv,
    generate_audit_json,
    generate_printable_html_report,
)

router = APIRouter(prefix="/reports", tags=["Audit Reports"])


@router.get("/preview", response_model=AuditReportJSON)
def preview_audit_report(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    rule_code: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    filters = ReportFilterParams(
        date_from=date_from,
        date_to=date_to,
        severity=severity,
        review_status=review_status,
        rule_code=rule_code,
        actor=actor,
    )
    return generate_audit_json(db, workspace.id, filters)


@router.get("/export")
def export_audit_report(
    format: str = Query("html", regex="^(html|json|csv_alerts|csv_events)$"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    severity: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    rule_code: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    filters = ReportFilterParams(
        date_from=date_from,
        date_to=date_to,
        severity=severity,
        review_status=review_status,
        rule_code=rule_code,
        actor=actor,
    )
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if format == "html":
        content = generate_printable_html_report(db, workspace.id, filters)
        filename = f"sentinel_audit_report_{now_str}.html"
        return Response(
            content=content,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    elif format == "json":
        data = generate_audit_json(db, workspace.id, filters)
        content = json.dumps(data, indent=2)
        filename = f"sentinel_audit_report_{now_str}.json"
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    elif format == "csv_alerts":
        content = generate_alerts_csv(db, workspace.id, filters)
        filename = f"sentinel_alerts_{now_str}.csv"
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    elif format == "csv_events":
        content = generate_events_csv(db, workspace.id, filters)
        filename = f"sentinel_events_{now_str}.csv"
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'.")
