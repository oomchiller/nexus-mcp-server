# Security Policy

## Supported Status

This repository is currently targeting GitHub beta. Use against production Nexus only with a least-privilege account unless you have reviewed the safety model.

## Reporting Vulnerabilities

Do not open public issues for vulnerabilities that could expose credentials, bypass host restrictions, bypass write gates, or trigger destructive Nexus actions.

Report privately through GitHub Security Advisories when available. If advisories are not enabled, contact the maintainer through the repository owner profile.

Include:

- affected version or commit;
- MCP tool/resource involved;
- Nexus version if known;
- reproduction steps;
- expected and actual behavior;
- whether credentials, tokens, repository contents, or destructive actions are involved.

## Security Boundaries

Implemented boundaries:

- `readonly` mode rejects `POST`, `PUT`, and `DELETE`;
- `audit` mode rejects `POST`, `PUT`, and `DELETE`;
- writes require `NEXUS_MCP_MODE=admin` and `NEXUS_MCP_ENABLE_WRITE_TOOLS=true`;
- raw API requires `NEXUS_MCP_ENABLE_RAW_API=true`;
- raw API paths are decoded, canonicalized, and restricted to `/service/rest/`;
- configured source and target hosts are checked against `NEXUS_ALLOWED_HOSTS`;
- admin path parameters are URL encoded;
- tool/resource outputs are recursively redacted for common secret-bearing keys and configured password values.

Not security boundaries:

- AI agent judgment;
- prompt wording;
- documentation warnings;
- redaction as a replacement for least-privilege credentials.

## Production Guidance

- Prefer a read-only Nexus account.
- Set `NEXUS_ALLOWED_HOSTS` to the exact Nexus hostname.
- Keep `NEXUS_VERIFY_TLS=true`.
- Keep `NEXUS_MCP_ENABLE_RAW_API=false` unless needed for a reviewed task.
- Keep `NEXUS_MCP_ENABLE_WRITE_TOOLS=false` unless an operator is intentionally using admin tools.
