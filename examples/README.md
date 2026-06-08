# MCP Client Examples

These examples show stdio MCP configuration for running this server from a local checkout.

Replace:

- `/path/to/nexus-mcp-server`;
- `https://nexus.example.com`;
- `readonly-user`;
- `replace-with-secret`.

Recommended production defaults:

- use a read-only Nexus account;
- set `NEXUS_ALLOWED_HOSTS` to the exact Nexus hostname;
- keep `NEXUS_MCP_MODE=readonly`;
- keep `NEXUS_MCP_ENABLE_RAW_API=false`;
- keep `NEXUS_MCP_ENABLE_WRITE_TOOLS=false`.

Files:

- `claude-desktop.json`
- `codex-mcp.example.toml`
- `gemini-cli-mcp.example.json`
