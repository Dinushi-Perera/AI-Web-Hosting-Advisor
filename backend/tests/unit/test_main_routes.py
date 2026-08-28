import httpx
import pytest

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_root_redirects_to_api_documentation():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
        response = await client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


@pytest.mark.anyio
async def test_doc_alias_redirects_to_api_documentation():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
        response = await client.get("/doc", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


@pytest.mark.anyio
async def test_favicon_request_does_not_return_not_found():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
        response = await client.get("/favicon.ico")

    assert response.status_code == 204
    assert response.content == b""
