# Roadmap

This roadmap lists concrete work needed before a public GitHub release.

## Release Blockers

1. Decide the MCP tool surface.

   Current problem: many helper functions exist but are not registered as MCP tools.

   Expected result: either expose useful helpers such as component/asset search and migration readiness, or remove dead helper code.

2. Replace broad `except Exception` blocks.

   Current problem: some helpers return `None` for permission, validation, server, and connectivity failures.

   Expected result: not-found cases are handled explicitly; operational failures are surfaced.

3. Validate Nexus OSS 3.90 and 3.92 compatibility.

   Current problem: compatibility beyond OSS 3.70 is inferred from OpenAPI-tolerant behavior, not verified against live instances or fixtures.

   Expected result: compatibility fixtures or live validation notes for OSS 3.90 and 3.92.

4. Remove or implement unused graph concepts.

   Current problem: `Capability`, `AFFECTS_REPOSITORY`, and `AFFECTS_BLOBSTORE` are defined but not populated.

   Expected result: unused concepts are removed, or implemented with tests and documentation.

## Short-Term Improvements

- Add a registered `nexus_migration_readiness_report` tool.
- Add registered read tools for component and asset search if they are considered part of the public MCP surface.
- Add a saved-baseline comparison input for "what changed since last inventory".
- Add input bounds for search limits and declared-state size.
- Add tests for every registered MCP tool wrapper.
- Add tests for malformed repository/blobstore/security response shapes.

## Documentation Work

- Add tested MCP client configuration examples for Claude Desktop, Codex CLI, and Gemini CLI when exact supported formats are known.
- Document tested Nexus Repository Manager versions.
- Document required Nexus privileges for each resource/tool group.
- Document known OSS vs Pro endpoint differences after testing.

## Not Planned

- Generic infrastructure inventory.
- CMDB functionality.
- OpenStack, GitLab, Kubernetes, or Linux host management.
- Multi-provider abstraction.
- Arbitrary shell execution.
- A remote HTTP MCP service before stdio behavior is stable.
