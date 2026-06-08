from typing import Any, Dict
from urllib.parse import quote

from ..nexus_client import NexusClient
from ..safety import validate_operation
from ..config import Settings

async def delete_repository(client: NexusClient, settings: Settings, name: str) -> Dict[str, Any]:
    """Delete a repository. HARMFUL."""
    validate_operation(settings, "DELETE")
    encoded_name = quote(name, safe="")
    await client.request("DELETE", f"/service/rest/v1/repositories/{encoded_name}")
    return {"status": "success", "message": f"Repository '{name}' deleted."}

async def run_task(client: NexusClient, settings: Settings, task_id: str) -> Dict[str, Any]:
    """Run a scheduled task immediately. HARMFUL."""
    validate_operation(settings, "POST")
    encoded_task_id = quote(task_id, safe="")
    await client.request("POST", f"/service/rest/v1/tasks/{encoded_task_id}/run")
    return {"status": "success", "message": f"Task '{task_id}' triggered."}
