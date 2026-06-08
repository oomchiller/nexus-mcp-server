from typing import Dict, Any
from ..nexus_client import NexusClient
from .repositories import list_repositories
from .blobstores import list_blobstores

async def compare_instances(source: NexusClient, target: NexusClient) -> Dict[str, Any]:
    """Compare source and target Nexus instances."""
    s_repos = {r.name: r for r in await list_repositories(source)}
    t_repos = {r.name: r for r in await list_repositories(target)}

    s_blobs = {b.name: b for b in await list_blobstores(source)}
    t_blobs = {b.name: b for b in await list_blobstores(target)}

    repo_diff: Dict[str, Any] = {
        "missing_on_target": sorted(list(set(s_repos.keys()) - set(t_repos.keys()))),
        "missing_on_source": sorted(list(set(t_repos.keys()) - set(s_repos.keys()))),
        "mismatched_config": []
    }

    for name in set(s_repos.keys()) & set(t_repos.keys()):
        s = s_repos[name]
        t = t_repos[name]
        if s.format != t.format or s.type != t.type:
            repo_diff["mismatched_config"].append({
                "name": name,
                "source": {"format": s.format, "type": s.type},
                "target": {"format": t.format, "type": t.type}
            })

    blob_diff = {
        "missing_on_target": sorted(list(set(s_blobs.keys()) - set(t_blobs.keys()))),
        "missing_on_source": sorted(list(set(t_blobs.keys()) - set(s_blobs.keys())))
    }

    report_md = "# Instance Comparison Report\n\n"
    report_md += f"**Source:** {source.base_url}\n"
    report_md += f"**Target:** {target.base_url}\n\n"

    report_md += "## Repositories\n\n"
    if repo_diff["missing_on_target"]:
        report_md += "### Missing on Target\n- " + "\n- ".join(repo_diff["missing_on_target"]) + "\n\n"
    if repo_diff["mismatched_config"]:
        report_md += "### Mismatched Configuration\n"
        for m in repo_diff["mismatched_config"]:
            report_md += f"- **{m['name']}**: Source({m['source']['format']}/{m['source']['type']}) != Target({m['target']['format']}/{m['target']['type']})\n"
        report_md += "\n"

    if not any(repo_diff.values()):
        report_md += "All repositories match.\n\n"

    report_md += "## Blob Stores\n\n"
    if blob_diff["missing_on_target"]:
        report_md += "### Missing on Target\n- " + "\n- ".join(blob_diff["missing_on_target"]) + "\n\n"
    if not any(blob_diff.values()):
        report_md += "All blob stores match.\n\n"

    return {
        "markdown": report_md,
        "diff": {
            "repositories": repo_diff,
            "blobstores": blob_diff
        }
    }
