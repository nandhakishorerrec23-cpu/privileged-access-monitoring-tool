from fastapi import APIRouter

from app.api.v1.workspace import router as workspace_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.events import router as events_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.rules import router as rules_router
from app.api.v1.reports import router as reports_router
from app.api.v1.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(workspace_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(ingest_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(rules_router)
api_v1_router.include_router(reports_router)
