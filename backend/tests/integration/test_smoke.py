import pytest


pytestmark = pytest.mark.anyio


async def test_health_and_documentation_are_available(api_client):
    health = await api_client.get("/health")
    docs = await api_client.get("/docs")
    openapi = await api_client.get("/openapi.json")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert docs.status_code == 200
    assert openapi.status_code == 200
    assert "/api/v1/auth/login" in openapi.json()["paths"]


async def test_protected_endpoint_rejects_anonymous_requests(api_client):
    response = await api_client.get("/api/v1/projects")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


async def test_registration_session_and_project_lifecycle(authenticated_client):
    client = authenticated_client
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "integration@example.com"

    created = await client.post("/api/v1/projects", json={
        "mode": "PLANNED",
        "title": "Integration project",
        "status": "DRAFT",
        "input": {"budget": 100, "websiteType": "SaaS"},
    })
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]

    listed = await client.get("/api/v1/projects")
    assert listed.status_code == 200
    assert [project["id"] for project in listed.json()] == [project_id]

    fetched = await client.get(f"/api/v1/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["input"]["budget"] == 100

    updated = await client.patch(f"/api/v1/projects/{project_id}", json={"title": "Updated integration project"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated integration project"

    assert (await client.post(f"/api/v1/projects/{project_id}/archive")).status_code == 200
    assert (await client.post(f"/api/v1/projects/{project_id}/restore")).status_code == 200
    assert (await client.delete(f"/api/v1/projects/{project_id}")).status_code == 200


async def test_validation_errors_use_the_public_error_contract(authenticated_client):
    response = await authenticated_client.post("/api/v1/projects", json={"mode": "PLANNED", "status": 42})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "VALIDATION_ERROR"
    assert body["requestId"]
