from typing import List, Optional
from ..nexus_client import NexusClient
from ..models import NexusTask

async def list_tasks(client: NexusClient) -> List[NexusTask]:
    """List all tasks."""
    data = await client.request("GET", "/service/rest/v1/tasks")
    items = data.get("items", [])
    return [
        NexusTask(
            id=item["id"],
            name=item["name"],
            type=item["type"],
            status=item.get("status") or item.get("currentState", "unknown"),
            lastRunResult=item.get("lastRunResult"),
            nextRun=item.get("nextRun")
        ) for item in items
    ]

async def get_task(client: NexusClient, task_id: str) -> Optional[NexusTask]:
    """Get details for a specific task."""
    try:
        item = await client.request("GET", f"/service/rest/v1/tasks/{task_id}")
        return NexusTask(
            id=item["id"],
            name=item["name"],
            type=item["type"],
            status=item.get("status") or item.get("currentState", "unknown"),
            lastRunResult=item.get("lastRunResult"),
            nextRun=item.get("nextRun")
        )
    except Exception:
        return None
