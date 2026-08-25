"""Bounded, server-side repository-content audits."""

from typing import Any, Dict, List

from ..errors import NexusApiError
from ..nexus_client import NexusClient


MAX_AUDIT_PAGES = 100
MAX_AUDIT_COMPONENTS = 5000


def _asset_summary(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the fields needed to compare hosted repository content."""
    return {
        "path": asset.get("path", ""),
        "content_type": asset.get("contentType"),
        "file_size": asset.get("fileSize"),
        "last_modified": asset.get("lastModified"),
        "last_downloaded": asset.get("lastDownloaded"),
    }


def _component_summary(component: Dict[str, Any]) -> Dict[str, Any]:
    assets = component.get("assets", [])
    if not isinstance(assets, list):
        assets = []

    return {
        "group": component.get("group"),
        "name": component.get("name", ""),
        "version": component.get("version"),
        "assets": sorted(
            (
                _asset_summary(asset)
                for asset in assets
                if isinstance(asset, dict)
            ),
            key=lambda asset: str(asset["path"]),
        ),
    }


async def audit_repository_content(
    client: NexusClient,
    repository: str,
    max_pages: int = MAX_AUDIT_PAGES,
    max_components: int = MAX_AUDIT_COMPONENTS,
) -> Dict[str, Any]:
    """Collect a complete component inventory without exposing page tokens.

    The component endpoint carries its assets, including `lastDownloaded`, so
    one paginated read provides both content and available access evidence.
    Every limit is reported as an incomplete inventory rather than silently
    returning a prefix.
    """
    if not repository:
        raise NexusApiError("Repository name must not be empty.")
    if not 1 <= max_pages <= MAX_AUDIT_PAGES:
        raise NexusApiError(
            f"max_pages must be between 1 and {MAX_AUDIT_PAGES}."
        )
    if not 1 <= max_components <= MAX_AUDIT_COMPONENTS:
        raise NexusApiError(
            f"max_components must be between 1 and {MAX_AUDIT_COMPONENTS}."
        )

    params: Dict[str, Any] = {"repository": repository}
    components: List[Dict[str, Any]] = []
    page_count = 0
    latest_last_downloaded = None
    asset_count = 0

    while page_count < max_pages:
        data = await client.request(
            "GET", "/service/rest/v1/components", params=params
        )
        page_count += 1

        if not isinstance(data, dict):
            raise NexusApiError("Expected a paginated component response.")
        items = data.get("items", [])
        if not isinstance(items, list):
            raise NexusApiError("Expected a component list in the response.")

        for item in items:
            if not isinstance(item, dict):
                raise NexusApiError("Expected a component object in the response.")
            if len(components) >= max_components:
                return _result(
                    repository,
                    components,
                    page_count,
                    asset_count,
                    latest_last_downloaded,
                    complete=False,
                    truncation_reason="max_components",
                )

            component = _component_summary(item)
            for asset in component["assets"]:
                asset_count += 1
                last_downloaded = asset["last_downloaded"]
                if isinstance(last_downloaded, str) and (
                    latest_last_downloaded is None
                    or last_downloaded > latest_last_downloaded
                ):
                    latest_last_downloaded = last_downloaded
            components.append(component)

        token = data.get("continuationToken")
        if not token:
            return _result(
                repository,
                components,
                page_count,
                asset_count,
                latest_last_downloaded,
                complete=True,
            )
        params["continuationToken"] = token

    return _result(
        repository,
        components,
        page_count,
        asset_count,
        latest_last_downloaded,
        complete=False,
        truncation_reason="max_pages",
    )


def _result(
    repository: str,
    components: List[Dict[str, Any]],
    page_count: int,
    asset_count: int,
    latest_last_downloaded: Any,
    complete: bool,
    truncation_reason: str | None = None,
) -> Dict[str, Any]:
    return {
        "repository": repository,
        "complete": complete,
        "truncation_reason": truncation_reason,
        "page_count": page_count,
        "component_count": len(components),
        "asset_count": asset_count,
        "latest_last_downloaded": latest_last_downloaded,
        "components": sorted(
            components,
            key=lambda component: (
                str(component["group"] or ""),
                str(component["name"]),
                str(component["version"] or ""),
            ),
        ),
    }
