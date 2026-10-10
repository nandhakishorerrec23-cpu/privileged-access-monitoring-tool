from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict

class RuleConfigRead(BaseModel):
    id: str
    workspace_id: str
    rule_code: str
    name: str
    description: str
    severity: str
    is_enabled: bool
    config: Dict[str, Any]
    version: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleConfigUpdate(BaseModel):
    is_enabled: bool
    config: Dict[str, Any] = {}


class ReanalyzeResponse(BaseModel):
    run_id: str
    events_analyzed: int
    alerts_created: int
    alerts_deactivated: int
    total_active_alerts: int
    message: str
