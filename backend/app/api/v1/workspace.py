from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.api.deps import get_current_workspace
from app.config import settings
from app.database import get_db
from app.models import Workspace, ActivityEvent, Alert
from app.schemas.workspace import WorkspaceSessionInfo
from app.services.workspace_service import create_guest_workspace

router = APIRouter(prefix="/session", tags=["Session & Workspace"])


@router.post("/bootstrap", response_model=WorkspaceSessionInfo)
def bootstrap_session(
    response: Response,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    """
    Initializes or confirms an isolated guest workspace session.
    Sets HttpOnly session cookie and returns session CSRF metadata.
    """
    # Set cookies explicitly
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=workspace.session_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        path="/",
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=workspace.csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        path="/",
    )

    events_count = db.execute(
        select(func.count(ActivityEvent.id)).where(ActivityEvent.workspace_id == workspace.id)
    ).scalar_one() or 0

    alerts_count = db.execute(
        select(func.count(Alert.id)).where(Alert.workspace_id == workspace.id)
    ).scalar_one() or 0

    unreviewed_count = db.execute(
        select(func.count(Alert.id)).where(
            Alert.workspace_id == workspace.id,
            Alert.review_status == "Open"
        )
    ).scalar_one() or 0

    return WorkspaceSessionInfo(
        workspace_id=workspace.id,
        name=workspace.name,
        csrf_token=workspace.csrf_token,
        expires_at=workspace.expires_at,
        is_demo=workspace.is_demo,
        events_count=events_count,
        alerts_count=alerts_count,
        unreviewed_alerts_count=unreviewed_count,
    )


@router.get("/info", response_model=WorkspaceSessionInfo)
def get_session_info(
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    events_count = db.execute(
        select(func.count(ActivityEvent.id)).where(ActivityEvent.workspace_id == workspace.id)
    ).scalar_one() or 0

    alerts_count = db.execute(
        select(func.count(Alert.id)).where(Alert.workspace_id == workspace.id)
    ).scalar_one() or 0

    unreviewed_count = db.execute(
        select(func.count(Alert.id)).where(
            Alert.workspace_id == workspace.id,
            Alert.review_status == "Open"
        )
    ).scalar_one() or 0

    return WorkspaceSessionInfo(
        workspace_id=workspace.id,
        name=workspace.name,
        csrf_token=workspace.csrf_token,
        expires_at=workspace.expires_at,
        is_demo=workspace.is_demo,
        events_count=events_count,
        alerts_count=alerts_count,
        unreviewed_alerts_count=unreviewed_count,
    )


@router.post("/reset", response_model=WorkspaceSessionInfo)
def reset_session(
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Creates a fresh, empty isolated workspace and assigns new tokens.
    """
    new_ws = create_guest_workspace(db, name="Fresh Demo Guest Workspace")
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=new_ws.session_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        path="/",
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=new_ws.csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        path="/",
    )

    return WorkspaceSessionInfo(
        workspace_id=new_ws.id,
        name=new_ws.name,
        csrf_token=new_ws.csrf_token,
        expires_at=new_ws.expires_at,
        is_demo=new_ws.is_demo,
        events_count=0,
        alerts_count=0,
        unreviewed_alerts_count=0,
    )
