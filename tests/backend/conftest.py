import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend app is in sys.path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.services.workspace_service import create_guest_workspace

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client, db_session):
    """
    Returns (client, workspace) with cookies and CSRF headers pre-set.
    """
    ws = create_guest_workspace(db_session, name="Test Isolated Workspace")
    client.cookies.set(settings.SESSION_COOKIE_NAME, ws.session_token)
    client.cookies.set(settings.CSRF_COOKIE_NAME, ws.csrf_token)
    client.headers[settings.CSRF_HEADER_NAME] = ws.csrf_token
    return client, ws
