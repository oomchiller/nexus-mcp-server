# Sonatype Nexus MCP Server

Python MCP server for Sonatype Nexus Repository Manager 3.x.

It exposes Nexus inventory, configuration context, audit findings, documentation output, IaC context, migration helpers, and guarded administrative actions to MCP clients.

This project is Nexus-specific. It is not a CMDB, generic infrastructure framework, or multi-provider abstraction layer.

## What It Does

- Reads Nexus repositories, blob stores, tasks, cleanup policies, routing rules, content selectors, users, roles, and privileges when the configured Nexus account can access those APIs.
- Builds a Nexus-specific in-memory graph for relationships such as repository-to-blobstore, group membership, cleanup policies, roles, and privileges.
- Exposes MCP resources for common live inventory.
- Exposes MCP tools for explanation, audit, documentation generation, IaC context, OpenAPI discovery, raw API access, and guarded admin actions.
- Keeps invasive operations disabled unless both admin mode and write-tool enablement are configured.

## Current Status

The server is usable for read-only Nexus observation, inventory, graph-derived explanations, limited configuration audits, documentation generation, and basic IaC context generation.

Current release: 0.1.0, public beta. See [CHANGELOG.md](CHANGELOG.md).

Known limitations are tracked in [ROADMAP.md](ROADMAP.md):

- Some helper functions are implemented as internal code but are intentionally not exposed as MCP tools.
- Audit output is evidence-based but limited to REST-visible configuration and graph-derived operational findings.
- Token authentication is not implemented.
- Used in production in read-only mode on Nexus Pro 3.96.1-01; partially verified on OSS 3.70; OSS 3.90 and 3.92 are inferred. See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).

## Installation

```bash
uv sync
uv run nexus-mcp-server \
  --transport stdio \
  --nexus-url https://nexus.example.com \
  --nexus-username readonly-user
```

Alternative module entrypoint:

```bash
uv run python -m nexus_mcp_server
```

Package entrypoint after installation:

```bash
nexus-mcp-server
```

## Configuration

Set environment variables or create a local `.env` file.

```bash
NEXUS_URL=https://nexus.example.com
NEXUS_USERNAME=readonly-user
NEXUS_PASSWORD=change-me
NEXUS_ALLOWED_HOSTS=nexus.example.com
NEXUS_MCP_MODE=readonly
NEXUS_MCP_ENABLE_RAW_API=false
NEXUS_MCP_ENABLE_WRITE_TOOLS=false
```

Supported variables:

| Variable | Description | Default |
| --- | --- | --- |
| `NEXUS_URL` | Source Nexus base URL | required |
| `NEXUS_USERNAME` | Username for Basic Auth | unset |
| `NEXUS_PASSWORD` | Password for Basic Auth | unset |
| `NEXUS_VERIFY_TLS` | Verify source TLS certificates | `true` |
| `NEXUS_CA_BUNDLE` | PEM file of CA certificates to trust for the source instead of the bundled public roots; needs `NEXUS_VERIFY_TLS=true` | unset |
| `NEXUS_TIMEOUT_SECONDS` | HTTP timeout in seconds | `30` |
| `NEXUS_ALLOWED_HOSTS` | Comma-separated allowed Nexus hostnames | `localhost,127.0.0.1` |
| `NEXUS_TARGET_URL` | Optional target Nexus URL for comparison code paths | unset |
| `NEXUS_TARGET_USERNAME` | Optional target Basic Auth username | unset |
| `NEXUS_TARGET_PASSWORD` | Optional target Basic Auth password | unset |
| `NEXUS_TARGET_VERIFY_TLS` | Verify target TLS certificates | `true` |
| `NEXUS_TARGET_CA_BUNDLE` | PEM file of CA certificates to trust for the target | unset |
| `NEXUS_LOG_LEVEL` | Python log level | `INFO` |
| `NEXUS_MCP_MODE` | `readonly`, `audit`, or `admin` | `readonly` |
| `NEXUS_MCP_ENABLE_RAW_API` | Enable `nexus_api_call` | `false` |
| `NEXUS_MCP_RAW_API_GET_ONLY` | Reject every raw API method except `GET` | `false` |
| `NEXUS_MCP_ENABLE_WRITE_TOOLS` | Allow write execution in admin mode | `false` |
| `NEXUS_MCP_ENABLE_PROMPTS` | Register MCP prompts | `true` |
| `NEXUS_MCP_ENABLE_RESOURCES` | Register MCP resources | `true` |
| `NEXUS_MCP_MAX_PAGE_SIZE` | Configured page-size limit | `100` |
| `NEXUS_MCP_MAX_RAW_RESPONSE_BYTES` | Max response size enforced by client | `1048576` |

Authentication currently implemented in code:

- Basic Auth with `NEXUS_USERNAME` and `NEXUS_PASSWORD`.

Not implemented:

- Bearer token authentication.
- Nexus user-token authentication.

Every setting, including the instance URL, username, TLS verification and
allowed hosts, can be supplied through the environment alone; no command-line
arguments are required.

### Tools-only mode

Gateways that run several instances of this server side by side, such as the
Docker MCP Gateway, prefix tool names per server but not prompt names or
resource URIs, so a second instance fails with a prompt or resource name
collision. Disable both to expose tools only:

```bash
NEXUS_MCP_ENABLE_PROMPTS=false
NEXUS_MCP_ENABLE_RESOURCES=false
```

Tool names and schemas are the same in every mode.

### Command-line options

CLI connection options override the corresponding environment variables:

```text
--transport {stdio,sse,streamable-http}
--nexus-url URL
--nexus-username USERNAME
--verify-ssl / --no-verify-ssl
--ca-bundle PATH
```

The server does not read `SSL_CERT_FILE` or the system trust store. For a
Nexus behind a private CA, set `NEXUS_CA_BUNDLE` to a PEM file with that CA
(the full bundle replaces the public roots) rather than disabling verification.
An unreadable bundle, or a bundle with verification disabled, stops the server
at startup.

Keep `NEXUS_PASSWORD` in the environment instead of placing it in command-line
arguments, where it may be visible in process listings.

## Container Image

Release images are published to GitHub Container Registry for `linux/amd64`
and `linux/arm64`. They run over stdio as an unprivileged user and are
configured entirely through the environment:

```bash
docker run --rm -i \
  -e NEXUS_URL=https://nexus.example.com \
  -e NEXUS_USERNAME=readonly-user \
  -e NEXUS_PASSWORD \
  -e NEXUS_ALLOWED_HOSTS=nexus.example.com \
  -e NEXUS_MCP_ENABLE_PROMPTS=false \
  -e NEXUS_MCP_ENABLE_RESOURCES=false \
  ghcr.io/oomchiller/nexus-mcp-server:0.1.0
```

To build the same image locally from `uv.lock`: `docker build -t nexus-mcp-server .`

The image defaults to `readonly` mode with write tools disabled.

## MCP Client Examples

Claude Desktop style configuration:

```json
{
  "mcpServers": {
    "nexus": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/nexus-mcp-server",
        "run",
        "nexus-mcp-server",
        "--transport",
        "stdio",
        "--nexus-url",
        "https://nexus.example.com",
        "--nexus-username",
        "readonly-user"
      ],
      "env": {
        "NEXUS_PASSWORD": "change-me",
        "NEXUS_ALLOWED_HOSTS": "nexus.example.com",
        "NEXUS_MCP_MODE": "readonly"
      }
    }
  }
}
```

Codex CLI configuration is available in `examples/codex-mcp.example.toml`.

Gemini CLI style configuration also depends on the local Gemini MCP config format. Use the same stdio command and environment values.

## Safety Model

Modes:

| Mode | Behavior |
| --- | --- |
| `readonly` | Rejects `POST`, `PUT`, and `DELETE`. |
| `audit` | Rejects `POST`, `PUT`, and `DELETE`; currently no extra enforcement distinction from `readonly`. |
| `admin` | Allows writes only when `NEXUS_MCP_ENABLE_WRITE_TOOLS=true`. |

Guardrails:

- Raw API is disabled unless `NEXUS_MCP_ENABLE_RAW_API=true`.
- Raw API paths are decoded, canonicalized, and restricted to `/service/rest/`.
- Configured source and target Nexus base URLs must match `NEXUS_ALLOWED_HOSTS`.
- Write tools fail closed unless admin mode and write enablement are both set.
- Admin tool path parameters are URL encoded before requests are made.
- Log and output redaction masks configured source/target password values and common secret-bearing keys.

Known remaining risks:

- Redaction is a safety boundary, not a substitute for least-privilege Nexus accounts.
- Optional Nexus endpoints can be unavailable because of version, edition, or permissions. Graph tools report these gaps as limitations instead of failing for optional collectors.

## MCP Resources

- `nexus://instance/summary`
- `nexus://repositories`
- `nexus://blobstores`
- `nexus://tasks`
- `nexus://cleanup-policies`
- `nexus://security/summary`
- `nexus://architecture`
- `nexus://knowledge_graph`

## MCP Tools

Explanation and graph:

- `nexus_understand_architecture`
- `nexus_explain_repository`
- `nexus_explain_storage_strategy`

Inventory and documentation:

- `nexus_generate_inventory_json`
- `nexus_generate_architecture_md`
- `nexus_generate_repository_catalog_md`

Audit:

- `nexus_detect_architecture_smells`
- `nexus_generate_audit_report`

IaC:

- `nexus_generate_terraform_context`
- `nexus_generate_puppet_context`
- `nexus_compare_live_state_with_declared_state`

OpenAPI:

- `nexus_openapi_list_operations`
- `nexus_generate_capability_map`

Admin and raw API:

- `nexus_delete_repository`
- `nexus_run_task`
- `nexus_api_call`

## Real-World Questions

| Question | Current support |
| --- | --- |
| What repositories exist? | Yes, through `nexus://repositories` and raw `/service/rest/v1/repositories`. |
| What blob stores exist? | Yes, through `nexus://blobstores`. |
| Which repositories appear unused? | Not directly implemented. Asset/component inspection helpers exist but are not registered as MCP tools. |
| Which blob stores appear unused? | Yes, graph-derived `nexus_detect_architecture_smells`. |
| How is storage organized? | Yes, `nexus_explain_storage_strategy`, when repository detail endpoints expose storage metadata. |
| How does live state differ from Terraform/Puppet? | Partially. Current drift compares repository name, format, and type only. |
| What are the operational risks? | Partially. Current risk rules cover a small set of graph smells. |
| Is the environment ready for migration? | Partially. Migration helper code exists but is not exposed as a first-class MCP tool. |
| What changed since the last inventory? | Not implemented. Requires saved baseline input or persistence. |
| How should documentation be updated? | Partially. Markdown generators can produce current architecture/catalog artifacts. |

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md): internal design and MCP surface.
- [DECISIONS.md](DECISIONS.md): architectural decisions, rationale, and tradeoffs.
- [ROADMAP.md](ROADMAP.md): realistic next steps before public release.
- [AGENTS.md](AGENTS.md): project memory for future AI agents and maintainers.
- [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md): Nexus version compatibility evidence.
- [docs/HIDDEN_FUNCTIONALITY.md](docs/HIDDEN_FUNCTIONALITY.md): implemented-but-unregistered helper audit.
- [docs/RELEASE_CANDIDATE_REVIEW.md](docs/RELEASE_CANDIDATE_REVIEW.md): current beta readiness assessment.

## Development Checks

```bash
uv run pytest
uv run ruff check .
uv run mypy src tests
```

Current state from the architecture review:

- `pytest` passes.
- `ruff check .` passes.
- `mypy src tests` passes.

## License

MIT
