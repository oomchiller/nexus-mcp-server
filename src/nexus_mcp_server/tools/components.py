from typing import List, Optional, Dict, Any
from urllib.parse import quote

from ..errors import NexusNotFoundError
from ..nexus_client import NexusClient
from ..models import Component

async def search_components(
    client: NexusClient,
    repository: Optional[str] = None,
    group: Optional[str] = None,
    name: Optional[str] = None,
    version: Optional[str] = None,
    limit: int = 50
) -> List[Component]:
    """Search for components."""
    params: Dict[str, Any] = {"limit": limit}
    if repository:
        params["repository"] = repository
    if group:
        params["group"] = group
    if name:
        params["name"] = name
    if version:
        params["version"] = version

    components = []
    async for item in client.list_paginated("/service/rest/v1/components", params=params, max_pages=1):
        components.append(Component(
            id=item["id"],
            repository=item["repository"],
            format=item["format"],
            group=item.get("group"),
            name=item["name"],
            version=item.get("version")
        ))
    return components

async def get_component(client: NexusClient, component_id: str) -> Optional[Component]:
    """Get details for a specific component."""
    try:
        item = await client.request("GET", f"/service/rest/v1/components/{quote(component_id, safe='')}")
        return Component(
            id=item["id"],
            repository=item["repository"],
            format=item["format"],
            group=item.get("group"),
            name=item["name"],
            version=item.get("version")
        )
    except NexusNotFoundError:
        return None
