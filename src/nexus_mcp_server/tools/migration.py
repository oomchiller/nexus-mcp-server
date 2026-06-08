from typing import Dict, Any, Optional
from ..nexus_client import NexusClient
from ..report import generate_report_header
from .repositories import list_repositories
from .blobstores import list_blobstores
from .tasks import list_tasks

async def generate_migration_readiness_report(client: NexusClient) -> Dict[str, Any]:
    """Generate a migration readiness report."""
    repos = await list_repositories(client)
    blobstores = await list_blobstores(client)
    tasks = await list_tasks(client)

    repo_types: Dict[str, int] = {}
    for r in repos:
        repo_types[r.type] = repo_types.get(r.type, 0) + 1

    findings = []
    recommendations = []

    offline_repos = [r.name for r in repos if not r.online]
    if offline_repos:
        findings.append(f"Offline repositories detected: {', '.join(offline_repos)}")
        recommendations.append("Verify why repositories are offline before migration.")

    failed_tasks = [t.name for t in tasks if t.status == "FAILURE"]
    if failed_tasks:
        findings.append(f"Failed tasks detected: {', '.join(failed_tasks)}")
        recommendations.append("Resolve task failures as they might impact data consistency.")

    report_md = generate_report_header("Nexus Migration Readiness Report", client.base_url)
    report_md += "## Summary\n\n"
    report_md += f"- Total Repositories: {len(repos)}\n"
    report_md += f"- Total Blob Stores: {len(blobstores)}\n\n"

    report_md += "## Findings\n\n"
    for f in findings:
        report_md += f"- {f}\n"
    if not findings:
        report_md += "No critical findings.\n"

    report_md += "\n## Recommendations\n\n"
    for rec in recommendations:
        report_md += f"- {rec}\n"
    if not recommendations:
        report_md += "Proceed with standard migration plan.\n"

    return {
        "markdown": report_md,
        "summary": {
            "repository_count": len(repos),
            "blobstore_count": len(blobstores),
            "findings_count": len(findings)
        }
    }

async def generate_cutover_checklist() -> str:
    """Generate a markdown checklist for Nexus migration cutover."""
    return """# Nexus Migration Cutover Checklist

## 1. Pre-Cutover (Preparation)
- [ ] Notify users of scheduled maintenance window.
- [ ] Freeze writes on source Nexus (set to Read-Only if possible).
- [ ] Verify target Nexus is online and reachable.
- [ ] Ensure all required blob stores are created on target.

## 2. Data Migration
- [ ] Backup OrientDB / PostgreSQL on source.
- [ ] Sync blob store data (rsync, S3 replication, etc.).
- [ ] Run migration tool (if applicable).
- [ ] Verify data integrity on target.

## 3. Configuration Validation
- [ ] Verify repository configuration matches source.
- [ ] Verify security roles and privileges.
- [ ] Verify LDAP/SAML integration.
- [ ] Check scheduled tasks on target.

## 4. Cutover
- [ ] Update DNS or Load Balancer to point to target Nexus.
- [ ] Verify clients can connect to the new URL.
- [ ] Perform smoke tests for Hosted, Proxy, and Group repositories.

## 5. Post-Cutover
- [ ] Monitor logs for errors.
- [ ] Confirm successful component uploads/downloads.
- [ ] Decommission source instance after stability period.

## Rollback Plan
- [ ] Revert DNS/LB changes to point back to source.
- [ ] Enable writes on source instance.
"""

async def generate_repository_inventory_report(client: NexusClient) -> Dict[str, Any]:
    """Generate a repository inventory report."""
    repos = await list_repositories(client)
    inventory = []
    for r in repos:
        inventory.append({
            "name": r.name,
            "format": r.format,
            "type": r.type,
            "online": r.online,
            "url": r.url
        })

    from ..report import to_markdown_table
    md = "# Nexus Repository Inventory\n\n"
    md += to_markdown_table(inventory, ["name", "format", "type", "online", "url"])

    return {
        "markdown": md,
        "inventory": inventory
    }

async def generate_hosted_repository_activity_report(client: NexusClient, repository: Optional[str] = None) -> Dict[str, Any]:
    """Generate a hosted repository activity report based on recent assets."""
    from .assets import search_assets

    # We'll use search_assets to find the most recent assets as a proxy for activity
    # Note: Nexus REST API doesn't provide a direct "last modified" for the repo itself
    all_repos = await list_repositories(client)
    hosted_repos = [r.name for r in all_repos if r.type == "hosted"]
    target_repos = [repository] if repository else hosted_repos

    activity = []
    for repo in target_repos:
        assets = await search_assets(client, repository=repo, limit=1)
        # In a real scenario, we'd need more metadata or separate search
        activity.append({
            "repository": repo,
            "has_assets": len(assets) > 0,
            "note": "Nexus REST API has limited activity tracking per repository."
        })

    return {
        "activity": activity,
        "note": "Report based on presence of assets. Reliable last-modified requires DB access."
    }
