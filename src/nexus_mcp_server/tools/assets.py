from typing import List, Optional, Dict, Any
from ..nexus_client import NexusClient
from ..models import Asset

async def search_assets(
    client: NexusClient,
    repository: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 50
) -> List[Asset]:
    """Search for assets."""
    params: Dict[str, Any] = {"limit": limit}
    if repository:
        params["repository"] = repository
    # name in search_assets usually refers to path or name in the REST API
    if name:
        params["q"] = name

    assets = []
    async for item in client.list_paginated("/service/rest/v1/assets", params=params, max_pages=1):
        assets.append(Asset(
            id=item["id"],
            path=item["path"],
            format=item["format"],
            repository=item["repository"]
        ))
    return assets
