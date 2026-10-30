from typing import List, Optional, Dict, Any
from urllib.parse import quote

from ..errors import NexusNotFoundError
from ..nexus_client import NexusClient
from ..models import BlobStore

async def list_blobstores(client: NexusClient) -> List[BlobStore]:
    """List all blob stores."""
    data = await client.request("GET", "/service/rest/v1/blobstores")
    return [BlobStore(**item) for item in data]

async def get_blobstore(client: NexusClient, name: str) -> Optional[BlobStore]:
    """Get details for a specific blob store."""
    try:
        data = await client.request("GET", f"/service/rest/v1/blobstores/{quote(name, safe='')}")
        return BlobStore(**data)
    except NexusNotFoundError:
        return None

async def generate_blobstore_usage_report(client: NexusClient) -> Dict[str, Any]:
    """Generate a report of blob store usage."""
    blobs = await list_blobstores(client)
    total_blobs = sum(b.blobCount or 0 for b in blobs)
    total_bytes = sum(b.totalSizeInBytes or 0 for b in blobs)

    usage_data = []
    for b in blobs:
        usage_data.append({
            "name": b.name,
            "type": b.type,
            "count": b.blobCount,
            "size_mb": round((b.totalSizeInBytes or 0) / 1024 / 1024, 2)
        })

    from ..report import to_markdown_table
    md = "# Blob Store Usage Report\n\n"
    md += to_markdown_table(usage_data, ["name", "type", "count", "size_mb"])
    md += f"\n\n**Total Blobs:** {total_blobs}\n"
    md += f"**Total Size:** {round(total_bytes / 1024 / 1024 / 1024, 2)} GB\n"

    return {
        "markdown": md,
        "data": usage_data,
        "totals": {"blobs": total_blobs, "bytes": total_bytes}
    }
