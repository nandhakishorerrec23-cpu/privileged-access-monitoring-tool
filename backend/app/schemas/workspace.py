from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class WorkspaceSessionInfo(BaseModel):
    workspace_id: str
    name: str
    csrf_token: str
    expires_at: datetime
    is_demo: bool
    events_count: int
    alerts_count: int
    unreviewed_alerts_count: int
