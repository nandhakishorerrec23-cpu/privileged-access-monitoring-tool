from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import Workspace
from app.services.workspace_service import get_workspace_by_token, create_guest_workspace


def get_current_workspace(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Workspace:
    """
    Retrieves the guest workspace for the visitor based on HttpOnly session cookie.
    If no session cookie is found or session has expired, a new guest session is automatically created,
    and secure cookies are set on the response.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    workspace = None
    if token:
        workspace = get_workspace_by_token(db, token)

    if not workspace:
        # Create a new isolated guest session
        workspace = create_guest_workspace(db)
        
        # Set HttpOnly session cookie
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=workspace.session_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRE_HOURS * 3600,
            path="/",
        )
        # Set readable CSRF cookie
        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=workspace.csrf_token,
            httponly=False,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRE_HOURS * 3600,
            path="/",
        )

    # State-changing CSRF verification
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        # Allow bootstrap / reset to initialize tokens without pre-existing CSRF check
        if not (request.url.path.endswith("/session/bootstrap") or request.url.path.endswith("/session/reset")):
            csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)
            csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            
            # Verify that either the header matches workspace.csrf_token or cookie matches header
            if not csrf_header or (csrf_header != workspace.csrf_token and csrf_header != csrf_cookie):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token validation failed. State-changing requests must supply a valid X-CSRF-Token header matching the session.",
                )

    return workspace
