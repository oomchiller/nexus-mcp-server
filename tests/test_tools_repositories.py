from typing import Any

from nexus_mcp_server.tools.repositories import list_repositories


class RepositoriesClient:
    async def request(self, method: str, path: str) -> Any:
        return [
            {
                "name": "maven",
                "format": "maven2",
                "type": "proxy",
                "url": "http://repo.example/repository/maven",
            }
        ]


def test_list_repositories_defaults_online_when_missing() -> None:
    import asyncio

    repos = asyncio.run(list_repositories(RepositoriesClient()))  # type: ignore[arg-type]

    assert len(repos) == 1
    assert repos[0].online is True
