import pytest
from sqlalchemy import func, select

from app.models import User


pytestmark = pytest.mark.anyio


async def test_registration_is_persisted_and_credentials_can_login_again(api_client, test_session_factory):
    credentials = {
        "fullName": "Persistent User",
        "email": "Persistent.User@Example.com",
        "password": "StrongPass1!",
    }

    registered = await api_client.post("/api/v1/auth/register", json=credentials)
    assert registered.status_code == 201, registered.text
    assert registered.json()["success"] is True
    assert registered.json()["message"] == "Registration successful."
    assert registered.json()["user"]["email"] == "persistent.user@example.com"

    with test_session_factory() as db:
        saved = db.scalar(select(User).where(User.email == "persistent.user@example.com"))
        assert saved is not None
        assert saved.full_name == "Persistent User"

    await api_client.post("/api/v1/auth/logout")
    logged_in = await api_client.post("/api/v1/auth/login", json={
        "email": "PERSISTENT.USER@EXAMPLE.COM",
        "password": credentials["password"],
    })
    assert logged_in.status_code == 200, logged_in.text
    assert logged_in.json()["user"]["email"] == "persistent.user@example.com"


async def test_duplicate_email_is_rejected_without_creating_another_user(api_client, test_session_factory):
    first = {
        "fullName": "First User",
        "email": "duplicate@example.com",
        "password": "StrongPass1!",
    }
    assert (await api_client.post("/api/v1/auth/register", json=first)).status_code == 201

    duplicate = await api_client.post("/api/v1/auth/register", json={
        **first,
        "fullName": "Second User",
        "email": "DUPLICATE@EXAMPLE.COM",
    })
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "AUTH_EMAIL_EXISTS"
    assert duplicate.json()["message"] == "An account already exists for this email."

    with test_session_factory() as db:
        count = db.scalar(select(func.count()).select_from(User).where(User.email == "duplicate@example.com"))
        assert count == 1
