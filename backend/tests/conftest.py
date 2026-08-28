import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def test_session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
async def api_client(test_session_factory):
    def override_get_db():
        with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(api_client):
    response = await api_client.post("/api/v1/auth/register", json={
        "fullName": "Integration Test User",
        "email": "integration@example.com",
        "password": "StrongPass1!",
    })
    assert response.status_code == 201, response.text
    return api_client
