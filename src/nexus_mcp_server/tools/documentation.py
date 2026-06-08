from typing import Any, Dict

from ..knowledge_graph.builder import build_knowledge_graph
from ..knowledge_graph.entities import EntityType
from ..knowledge_graph.query_engine import QueryEngine
from ..nexus_client import NexusClient
from ..operational.expert import OperationalExpert
from ..report import generate_report_header


async def generate_audit_report(client: NexusClient) -> Dict[str, Any]:
    """Generate a limited evidence-based Nexus configuration audit report."""
    graph = await build_knowledge_graph(client)
    risks = OperationalExpert(graph).detect_risks()
    storage = QueryEngine(graph).explain_storage_strategy()

    repos = graph.get_entities_by_type(EntityType.REPOSITORY)
    blobstores = graph.get_entities_by_type(EntityType.BLOBSTORE)
    tasks = graph.get_entities_by_type(EntityType.TASK)
    users = graph.get_entities_by_type(EntityType.USER)
    roles = graph.get_entities_by_type(EntityType.ROLE)
    privileges = graph.get_entities_by_type(EntityType.PRIVILEGE)

    markdown = generate_report_header("Nexus Configuration Audit", client.base_url)
    markdown += "## Scope\n\n"
    markdown += (
        "This report is generated from Nexus REST APIs available to the configured account. "
        "It is a configuration and operational-smell audit, not a full security assessment.\n\n"
    )

    markdown += "## Inventory Summary\n\n"
    markdown += f"- Repositories: {len(repos)}\n"
    markdown += f"- Blob stores: {len(blobstores)}\n"
    markdown += f"- Tasks: {len(tasks)}\n"
    markdown += f"- Users: {len(users)}\n"
    markdown += f"- Roles: {len(roles)}\n"
    markdown += f"- Privileges: {len(privileges)}\n\n"

    markdown += "## Findings\n\n"
    if risks:
        for finding in risks:
            markdown += f"### {finding['title']}\n"
            markdown += f"- Severity: {finding['severity']}\n"
            markdown += f"- Confidence: {finding['confidence']}\n"
            markdown += f"- Affected objects: {', '.join(finding['affected_objects'])}\n"
            markdown += f"- Evidence: {'; '.join(finding['evidence'])}\n"
            markdown += f"- Suggested action: {finding['suggested_action']}\n\n"
    else:
        markdown += "No graph-derived operational findings were detected.\n\n"

    markdown += "## Storage Summary\n\n"
    for detail in storage["findings"][0]["details"]:
        repo_names = detail["managed_repositories"]
        repo_text = ", ".join(repo_names) if repo_names else "none observed"
        markdown += f"- {detail['blobstore']}: {repo_text}\n"

    limitations = graph.metadata.get("limitations", [])
    if limitations:
        markdown += "\n## Limitations\n\n"
        for item in limitations:
            markdown += f"- {item}\n"

    return {
        "markdown": markdown,
        "summary": {
            "repository_count": len(repos),
            "blobstore_count": len(blobstores),
            "task_count": len(tasks),
            "user_count": len(users),
            "role_count": len(roles),
            "privilege_count": len(privileges),
            "finding_count": len(risks),
        },
        "findings": risks,
        "limitations": limitations,
        "metadata": graph.metadata,
    }
