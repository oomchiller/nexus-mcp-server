# Roadmap

This roadmap lists concrete work after the 0.1.0 public beta.

## Resolved For 0.1.0

- Tool surface: the 17 registered tools are the public surface for 0.1.0; unregistered helpers stay internal (see `docs/HIDDEN_FUNCTIONALITY.md`).
- Broad `except Exception` blocks were replaced: single-object helpers return `None` only for `404`, graph collectors record a listed set of Nexus, transport and response-shape errors as limitations.
- Unused graph concepts `Capability`, `AFFECTS_REPOSITORY` and `AFFECTS_BLOBSTORE` were removed.
- Compatibility: production use on Nexus Pro 3.96.1-01 in read-only mode is documented.

## Before 1.0

- Validate Nexus OSS 3.90 and 3.92 with live instances or fixtures.
- Exercise admin write tools against a live non-production instance.
- Optionally hide write tools from the tool list while write gates are closed.

## Short-Term Improvements

- Add a registered `nexus_migration_readiness_report` tool.
- Add registered read tools for component and asset search if they are considered part of the public MCP surface.
- Add a saved-baseline comparison input for "what changed since last inventory".
- Add input bounds for search limits and declared-state size.
- Add tests for every registered MCP tool wrapper.
- Add tests for malformed repository/blobstore/security response shapes.

## Documentation Work

- Add tested MCP client configuration examples for Claude Desktop, Codex CLI, and Gemini CLI when exact supported formats are known.
- Document required Nexus privileges for each resource/tool group.
- Document known OSS vs Pro endpoint differences after testing.

## Not Planned

- Generic infrastructure inventory.
- CMDB functionality.
- OpenStack, GitLab, Kubernetes, or Linux host management.
- Multi-provider abstraction.
- Arbitrary shell execution.
- A remote HTTP MCP service before stdio behavior is stable.
