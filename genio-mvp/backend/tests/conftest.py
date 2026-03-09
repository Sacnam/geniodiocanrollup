"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session


# Test database
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with database override."""
    
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client: TestClient):
    """Create a test user and return auth tokens."""
    # Register
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    return {
        "email": "test@example.com",
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest.fixture(name="db_engine")
def db_engine_fixture():
    """Create a test database engine for migration tests."""
    from sqlalchemy import create_engine as sa_create_engine
    
    engine = sa_create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    SQLModel.metadata.drop_all(engine)
