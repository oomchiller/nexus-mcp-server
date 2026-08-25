from typing import Any

import pytest

from nexus_mcp_server.nexus_client import NexusClient
from nexus_mcp_server.tools.repository_content import audit_repository_content


@pytest.mark.asyncio
async def test_audit_repository_content_collects_all_pages(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        url="http://nexus/service/rest/v1/components?repository=quest",
        json={
            "items": [
                {
                    "name": "vasclnt",
                    "version": "5.1.2",
                    "assets": [
                        {
                            "path": "pool/vasclnt.deb",
                            "lastDownloaded": "2026-08-23T14:53:00.000+00:00",
                        }
                    ],
                }
            ],
            "continuationToken": "next-page",
        },
    )
    httpx_mock.add_response(
        url=(
            "http://nexus/service/rest/v1/components?repository=quest"
            "&continuationToken=next-page"
        ),
        json={
            "items": [
                {
                    "name": "pamdefender",
                    "version": "5.5.4",
                    "assets": [{"path": "pool/pamdefender.deb"}],
                }
            ],
            "continuationToken": None,
        },
    )

    result = await audit_repository_content(NexusClient("http://nexus"), "quest")

    assert result["complete"] is True
    assert result["page_count"] == 2
    assert result["component_count"] == 2
    assert result["asset_count"] == 2
    assert result["latest_last_downloaded"] == "2026-08-23T14:53:00.000+00:00"
    assert result["components"] == [
        {
            "group": None,
            "name": "pamdefender",
            "version": "5.5.4",
            "assets": [
                {
                    "path": "pool/pamdefender.deb",
                    "content_type": None,
                    "file_size": None,
                    "last_modified": None,
                    "last_downloaded": None,
                }
            ],
        },
        {
            "group": None,
            "name": "vasclnt",
            "version": "5.1.2",
            "assets": [
                {
                    "path": "pool/vasclnt.deb",
                    "content_type": None,
                    "file_size": None,
                    "last_modified": None,
                    "last_downloaded": "2026-08-23T14:53:00.000+00:00",
                }
            ],
        },
    ]
    assert "continuationToken" not in str(result)


@pytest.mark.asyncio
async def test_audit_repository_content_marks_component_limit_incomplete(
    httpx_mock: Any,
) -> None:
    httpx_mock.add_response(
        url="http://nexus/service/rest/v1/components?repository=quest",
        json={
            "items": [
                {"name": "one", "assets": []},
                {"name": "two", "assets": []},
            ],
            "continuationToken": "not-returned",
        },
    )

    result = await audit_repository_content(
        NexusClient("http://nexus"), "quest", max_components=1
    )

    assert result["complete"] is False
    assert result["truncation_reason"] == "max_components"
    assert result["component_count"] == 1
    assert "not-returned" not in str(result)
