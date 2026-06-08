from typing import Any

import pytest
from nexus_mcp_server.nexus_client import NexusClient
from nexus_mcp_server.errors import NexusAuthError, NexusNotFoundError, SafetyError

@pytest.mark.asyncio
async def test_nexus_client_request_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(url="http://nexus/api", json={"status": "ok"})

    client = NexusClient("http://nexus")
    response = await client.request("GET", "/api")

    assert response == {"status": "ok"}

@pytest.mark.asyncio
async def test_nexus_client_auth_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(url="http://nexus/api", status_code=401)

    client = NexusClient("http://nexus")
    with pytest.raises(NexusAuthError):
        await client.request("GET", "/api")

@pytest.mark.asyncio
async def test_nexus_client_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(url="http://nexus/api", status_code=404)

    client = NexusClient("http://nexus")
    with pytest.raises(NexusNotFoundError):
        await client.request("GET", "/api")

@pytest.mark.asyncio
async def test_nexus_client_pagination(httpx_mock: Any) -> None:
    # Page 1
    httpx_mock.add_response(
        url="http://nexus/api?limit=2",
        json={"items": [{"id": 1}, {"id": 2}], "continuationToken": "token2"}
    )
    # Page 2
    httpx_mock.add_response(
        url="http://nexus/api?limit=2&continuationToken=token2",
        json={"items": [{"id": 3}], "continuationToken": None}
    )

    client = NexusClient("http://nexus")
    results = await client.get_all("/api", params={"limit": 2})

    assert results == [{"id": 1}, {"id": 2}, {"id": 3}]


@pytest.mark.asyncio
async def test_nexus_client_rejects_absolute_url() -> None:
    client = NexusClient("http://nexus")

    with pytest.raises(SafetyError, match="Absolute request URLs are not allowed"):
        await client.request("GET", "http://evil.example/service/rest/v1/repositories")


@pytest.mark.asyncio
async def test_nexus_client_redacts_error_details(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="http://nexus/api",
        status_code=500,
        json={"password": "secret-value", "message": "secret-value"},
    )

    client = NexusClient("http://nexus", password="secret-value")
    with pytest.raises(Exception) as exc_info:
        await client.request("GET", "/api", retries=0)

    error = exc_info.value
    assert getattr(error, "details") == {
        "password": "********",
        "message": "********",
    }
