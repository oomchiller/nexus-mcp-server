# Changelog

## 0.1.0 - 2026-10-30

First public beta.

- 17 MCP tools for Nexus observation, inventory, audit, documentation, IaC context, OpenAPI discovery and gated admin actions.
- `readonly` mode by default; writes need `NEXUS_MCP_MODE=admin` and `NEXUS_MCP_ENABLE_WRITE_TOOLS=true`.
- `NEXUS_MCP_ENABLE_PROMPTS` and `NEXUS_MCP_ENABLE_RESOURCES` switch off prompts and resources for multi-instance gateways.
- All instance settings can be supplied through the environment.
- Container image `ghcr.io/oomchiller/nexus-mcp-server` for `linux/amd64` and `linux/arm64`, built from `uv.lock`, running as an unprivileged user over stdio.
- Single-object helpers return `None` only for `404`; other Nexus failures propagate.
- Removed unpopulated graph types `Capability`, `AFFECTS_REPOSITORY` and `AFFECTS_BLOBSTORE`.
