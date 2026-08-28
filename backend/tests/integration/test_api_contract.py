from collections import Counter

import pytest


pytestmark = pytest.mark.anyio


async def test_every_api_operation_has_a_unique_id_and_response(api_client):
    response = await api_client.get("/openapi.json")
    assert response.status_code == 200
    operations = []
    for path, path_item in response.json()["paths"].items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            operations.append((path, method, operation["operationId"]))
            assert operation.get("responses"), f"{method.upper()} {path} has no responses"
    duplicates = [name for name, count in Counter(item[2] for item in operations).items() if count > 1]
    assert not duplicates
    assert len(operations) >= 70


async def test_browser_entry_routes_do_not_return_404(api_client):
    for path in ("/", "/doc"):
        response = await api_client.get(path, follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"
    assert (await api_client.get("/favicon.ico")).status_code == 204


async def test_openapi_covers_every_public_route_group(api_client):
    paths = (await api_client.get("/openapi.json")).json()["paths"]
    required = {"auth", "users", "projects", "analysis", "pricing", "reports", "notifications", "testing", "workload"}
    documented = {
        path.removeprefix("/api/v1/").split("/", 1)[0]
        for path in paths
        if path.startswith("/api/v1/")
    }
    assert required.issubset(documented)
