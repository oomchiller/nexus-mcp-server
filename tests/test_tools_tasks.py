from typing import Any

from nexus_mcp_server.tools.tasks import list_tasks


class TasksClient:
    async def request(self, method: str, path: str) -> Any:
        return {
            "items": [
                {
                    "id": "task-1",
                    "name": "Backup database",
                    "type": "db.backup",
                    "currentState": "WAITING",
                    "lastRunResult": "FAILED",
                    "nextRun": "2026-06-05T05:00:00.000+00:00",
                }
            ],
            "continuationToken": None,
        }


def test_list_tasks_accepts_nexus_370_current_state() -> None:
    import asyncio

    tasks = asyncio.run(list_tasks(TasksClient()))  # type: ignore[arg-type]

    assert len(tasks) == 1
    assert tasks[0].status == "WAITING"
    assert tasks[0].lastRunResult == "FAILED"
