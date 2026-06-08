# Contributing

This project is a Nexus-specific MCP server. Contributions should keep the project focused on Sonatype Nexus Repository Manager.

## Local Checks

Run these before opening a pull request:

```bash
uv run pytest
uv run ruff check .
uv run mypy src tests
```

## Scope Rules

Acceptable changes:

- Nexus REST compatibility fixes;
- MCP tool/resource safety fixes;
- tests for Nexus version and edition differences;
- documentation that reflects implemented behavior;
- small improvements to existing Nexus inventory, audit, documentation, IaC, or migration support.

Out of scope:

- generic infrastructure inventory;
- CMDB functionality;
- OpenStack, GitLab, Kubernetes, Harbor, or host management integrations;
- arbitrary shell execution;
- remote HTTP service work unless stdio behavior remains stable.

## Safety Rules

- Keep `readonly` as the default.
- Keep write actions behind both `NEXUS_MCP_MODE=admin` and `NEXUS_MCP_ENABLE_WRITE_TOOLS=true`.
- Keep raw API disabled by default.
- Do not expose a helper as an MCP tool unless it is tested, documented, version-tolerant, and useful to end users.
- Do not claim support for a Nexus version or authentication method without test evidence.

## Documentation

Update documentation when behavior changes:

- `README.md` for user-facing setup and safety facts;
- `ARCHITECTURE.md` for internal design;
- `DECISIONS.md` for decisions that should not be changed casually;
- `docs/COMPATIBILITY.md` for version evidence;
- `docs/HIDDEN_FUNCTIONALITY.md` when helper functions are added, removed, or exposed.
