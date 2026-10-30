# Release Candidate Review

Status: `RELEASED_0.1.0_BETA`

This status means the repository is published as a public beta (0.1.0) with clear limitations. It does not mean production-ready admin operation.

## Architecture Audit

What works:

- stdio FastMCP server;
- read-only resources for repositories, blobstores, tasks, cleanup policies, architecture, security summary, and knowledge graph;
- graph-derived storage explanation and repository explanation;
- inventory JSON and Markdown generation;
- limited evidence-based audit report;
- OpenAPI discovery and capability map;
- raw API and admin tools behind runtime safety gates.

Partial:

- migration support is helper code, not a first-class MCP workflow;
- Terraform/Puppet support emits basic context and shallow drift results;
- architecture smells cover a small rule set;
- repository-to-blobstore relationships require repository detail endpoints and storage metadata.

Still not implemented:

- saved inventory baseline comparison;
- unused repository detection;
- full security audit;
- token authentication;
- remote MCP HTTP transport.

## Security Audit

Current safety properties:

- readonly is the default mode;
- `readonly` and `audit` reject writes;
- writes require `NEXUS_MCP_MODE=admin` and `NEXUS_MCP_ENABLE_WRITE_TOOLS=true`;
- raw API requires `NEXUS_MCP_ENABLE_RAW_API=true`;
- raw API paths are decoded, canonicalized, and restricted to `/service/rest/`;
- `NexusClient.request()` rejects absolute URLs;
- admin path parameters are URL encoded;
- outputs are passed through recursive secret redaction.

Remaining risks:

- least-privilege Nexus credentials are still required;
- harmful tools are visible in the MCP tool list even when runtime gates block execution.

## MCP Surface Review

Keep:

- `nexus_understand_architecture`
- `nexus_explain_repository`
- `nexus_explain_storage_strategy`
- `nexus_audit_repository_content`
- `nexus_generate_inventory_json`
- `nexus_generate_architecture_md`
- `nexus_generate_repository_catalog_md`
- `nexus_detect_architecture_smells`
- `nexus_generate_audit_report`
- `nexus_generate_terraform_context`
- `nexus_generate_puppet_context`
- `nexus_compare_live_state_with_declared_state`
- `nexus_openapi_list_operations`
- `nexus_generate_capability_map`
- `nexus_delete_repository`
- `nexus_run_task`
- `nexus_api_call`

Overlaps:

- `nexus_understand_architecture` and `nexus_explain_storage_strategy` currently return the same storage-oriented explanation. Keep both for beta only if documentation says the former is a broad entry point and the latter is storage-specific.

Do not expose yet:

- component/asset helpers;
- migration readiness helpers;
- source/target comparison helpers;
- anonymous/realm helpers.

## Production Readiness

Read-only production observation: acceptable with a low-privilege account and explicit `NEXUS_ALLOWED_HOSTS`.

Admin production operation: not recommended as a default. It requires explicit admin mode, write enablement, and operator review.

Public GitHub beta: released as 0.1.0, with CI and a container image on GHCR.

Production-ready release: requires validation on Nexus OSS 3.90 and 3.92, admin tools exercised against a live instance, and stronger tests for malformed responses.
