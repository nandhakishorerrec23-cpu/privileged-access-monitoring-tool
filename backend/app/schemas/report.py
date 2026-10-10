from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ReportFilterParams(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    severity: Optional[str] = None
    review_status: Optional[str] = None
    rule_code: Optional[str] = None
    actor: Optional[str] = None

class ReportSummary(BaseModel):
    total_events_in_scope: int
    total_alerts_in_scope: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    open_alerts: int
    investigating_alerts: int
    resolved_alerts: int
    false_positives: int

class AuditReportJSON(BaseModel):
    title: str = "Sentinel Privileged Access Monitoring Audit Report"
    report_id: str
    generated_at: str
    timezone: str
    workspace_id: str
    filters_applied: Dict[str, Any]
    summary: ReportSummary
    rules_in_force: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    events_sample: List[Dict[str, Any]]
    disclaimer: str
