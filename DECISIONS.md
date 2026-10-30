# Architecture Decisions

## Decision: Keep The Project Nexus-Specific

Rationale:

- The original goal is a production-ready MCP server for Sonatype Nexus Repository Manager.
- Nexus repository formats, blob stores, groups, cleanup policies, routing rules, tasks, users, roles, and privileges have product-specific semantics.

Tradeoff:

- The project should not attempt to become reusable for other infrastructure tools.

Consequence:

- Avoid provider-neutral entity names unless they directly represent Nexus concepts.

## Decision: Use A Small Nexus Knowledge Graph

Rationale:

- Many useful Nexus questions span multiple REST endpoints.
- Graph relationships make storage topology, group membership, cleanup policies, and role/privilege links easier to explain with evidence.

Tradeoff:

- The graph introduces complexity and can fail if required endpoints are unavailable.

Consequence:

- Keep the graph limited to Nexus objects.
- Remove unused graph entity/relationship types until they are backed by implemented readers.

## Decision: Readonly By Default

Rationale:

- Nexus is usually production infrastructure.
- Observation, inventory, and audit must be safe by default.

Tradeoff:

- Operators must explicitly configure admin mode for invasive actions.

Consequence:

- Do not weaken `readonly` behavior.
- Write tools must keep runtime checks even if they are visible in MCP tool listings.

## Decision: Require Two Gates For Writes

Rationale:

- `NEXUS_MCP_MODE=admin` alone is not enough protection for an AI-connected tool.

Enforcement:

- Write methods require `NEXUS_MCP_MODE=admin`.
- Write methods also require `NEXUS_MCP_ENABLE_WRITE_TOOLS=true`.

Tradeoff:

- Admin usage requires extra setup.

Consequence:

- Keep both gates for `DELETE`, `POST`, and `PUT` operations.

## Decision: Disable Raw API By Default

Rationale:

- A raw API tool is useful for unsupported Nexus endpoints.
- It also bypasses first-class schemas and is easier to misuse.

Enforcement:

- `nexus_api_call` requires `NEXUS_MCP_ENABLE_RAW_API=true`.
- Raw API paths must stay under `/service/rest/`.
- Raw API writes require the same write gates as first-class harmful tools.

Tradeoff:

- Some legitimate Nexus endpoints require explicit opt-in.

Consequence:

- Do not enable raw API by default.
- Do not turn the raw API tool into a generic HTTP proxy.

## Decision: Basic Auth Is The Only Implemented Authentication Method

Rationale:

- The current code constructs `httpx.BasicAuth` from username/password only.

Tradeoff:

- Token authentication is not available yet.

Consequence:

- Documentation must not claim token support until code and tests exist.

## Decision: Stdio Transport First

Rationale:

- Local MCP clients can use stdio directly.
- It keeps deployment simple while the tool surface is still stabilizing.

Tradeoff:

- No remote MCP service is available.

Consequence:

- Do not add FastAPI/HTTP dependencies until HTTP transport is actually implemented.

## Decision: Separate Switches For Prompts And Resources

Rationale:

- Gateways that host several instances of this server, such as the Docker MCP Gateway, prefix tool names per server but not prompt names or resource URIs. A second instance fails with a prompt or resource name collision.
- Prompts and resources collide for different reasons (names versus URIs) and may be solved independently later, for example by instance-scoped resource URIs. Two switches, `NEXUS_MCP_ENABLE_PROMPTS` and `NEXUS_MCP_ENABLE_RESOURCES`, keep each choice explicit and follow the existing `NEXUS_MCP_ENABLE_*` naming. A single `NEXUS_MCP_TOOLS_ONLY` flag was rejected because it cannot express the partial cases.

Enforcement:

- Both switches default to `true`, so existing clients keep every prompt and resource.
- Tools are always registered; their names and schemas do not depend on these switches.
- Resources and prompts are registered in `main()` from settings, not at import time.

Tradeoff:

- Embedders that import `server.mcp` without calling `main()` must call `register_optional_capabilities()` themselves to get resources and prompts.

Consequence:

- Tools-only deployments set both switches to `false` instead of patching FastMCP registries.

## Decision: Evidence-Based Findings

Rationale:

- Infrastructure audit output must be traceable to observed Nexus data.

Tradeoff:

- Some useful recommendations cannot be made without additional data.

Consequence:

- Findings should include evidence, severity, confidence, and limitations.
- Do not let LLM prompts infer unsupported operational facts.

## Rejected Direction: Generic Knowledge Platform

Reason:

- It expands scope beyond the Nexus MCP mission.
- It makes adoption harder for engineers who only need Nexus inventory, audit, operation, and migration support.

Consequence:

- Avoid "platform", "digital twin", "CMDB", or multi-provider framing in code and docs.
