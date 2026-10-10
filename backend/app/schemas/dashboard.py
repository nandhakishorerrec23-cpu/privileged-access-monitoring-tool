from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel

class DashboardMetrics(BaseModel):
    total_events: int
    total_active_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    open_investigations: int  # review_status in ('Open', 'Investigating')
    distinct_admins: int
    latest_import_time: Optional[datetime] = None
    active_rules_count: int
    total_rules_count: int

class SeverityCount(BaseModel):
    severity: str
    count: int
    percentage: float

class TimelinePoint(BaseModel):
    date: str  # YYYY-MM-DD or hourly string
    event_count: int
    alert_count: int

class TopFlaggedActor(BaseModel):
    actor: str
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    latest_activity: datetime

class ActionDistributionItem(BaseModel):
    action: str
    count: int

class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    severity_distribution: List[SeverityCount]
    activity_timeline: List[TimelinePoint]
    top_flagged_actors: List[TopFlaggedActor]
    action_distribution: List[ActionDistributionItem]
