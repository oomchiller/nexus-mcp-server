# Architecture

This repository implements a Nexus-specific MCP server. The code should stay focused on Sonatype Nexus Repository Manager and should not grow into a generic infrastructure platform.

## Runtime Entry Point

`src/nexus_mcp_server/server.py` creates a FastMCP server, initializes Nexus clients from environment-backed settings, registers tools, registers resources and prompts unless `NEXUS_MCP_ENABLE_RESOURCES` or `NEXUS_MCP_ENABLE_PROMPTS` is `false`, and starts stdio transport through `mcp.run()`.

Current transport:

- stdio only.

Not implemented:

- Streamable HTTP.
- Hosted HTTP service.
- Background worker process.

## Module Responsibilities

### `config`

Owns runtime settings loaded from environment variables and optional `.env`.

Implemented settings include:

- source Nexus URL, Basic Auth credentials, TLS verification, timeout, and allowed hosts;
- optional target Nexus URL and Basic Auth credentials;
- MCP mode and enablement flags for raw API and write tools;
- response-size and page-size limits.

Current limitation:

- Token fields are not implemented.

### `nexus_client`

Owns HTTP communication with Nexus.

Responsibilities:

- normalize base URL;
- validate configured source/target hostnames against `NEXUS_ALLOWED_HOSTS`;
- configure `httpx.AsyncClient`;
- apply Basic Auth when username and password are present;
- retry transient `429`, `502`, `503`, and `504` responses;
- map HTTP status codes to Nexus-specific exceptions;
- enforce maximum response size;
- expose pagination helpers for `continuationToken` endpoints.

Important boundary:

- `request()` rejects absolute URLs. Callers must pass paths relative to the configured Nexus base URL.

### `tools`

Contains low-level Nexus API helpers and admin/raw API wrappers.

Implemented helper areas:

- repositories;
- blob stores;
- components;
- assets;
- tasks;
- system;
- security;
- cleanup policies, routing rules, content selectors;
- documentation/audit reports;
- migration reports;
- source/target comparison;
- raw API;
- admin operations.

Important distinction:

- A function under `src/nexus_mcp_server/tools` is not automatically an MCP tool. Only functions registered in `server.py` are exposed to MCP clients.

### `knowledge_graph`

Builds an in-memory graph of Nexus objects and relationships.

Current entities:

- `NexusInstance`
- `Repository`
- `BlobStore`
- `Task`
- `CleanupPolicy`
- `RoutingRule`
- `Role`
- `Privilege`
- `User`
- `ContentSelector`
- `Capability`

Current relationships:

- `USES_BLOBSTORE`
- `APPLIES_CLEANUP_POLICY`
- `USES_ROUTING_RULE`
- `MEMBER_OF_GROUP`
- `HAS_PRIVILEGE`
- `ASSIGNED_ROLE`
- `AFFECTS_REPOSITORY`
- `AFFECTS_BLOBSTORE`
- `RUNS_TASK`
- `MANAGED_BY`

The graph exists to answer Nexus questions that cross REST endpoints. It should not become a generic infrastructure graph.

Current limitations:

- rebuilt on demand;
- no persistent cache;
- optional collector failures are recorded in graph metadata as limitations;
- core collector failures can still fail graph construction;
- `Capability`, `AFFECTS_REPOSITORY`, and `AFFECTS_BLOBSTORE` are defined but not populated by the current builder.

### `operational`

Contains rule-based risk detection over the graph.

Current findings:

- unused blob stores;
- empty group repositories;
- offline repositories;
- orphaned cleanup policies.

Current limitation:

- findings are useful but shallow; this is not a complete Nexus audit.

### `docs_engine`

Generates Markdown from the graph.

Current outputs:

- architecture overview;
- repository catalog.

Current limitation:

- output is concise and only as complete as the graph.

### `iac`

Generates IaC-oriented context and simple drift results.

Current outputs:

- inventory JSON;
- Terraform-oriented repository JSON;
- Puppet/Hiera-style YAML;
- repository drift comparison.

Current limitation:

- drift comparison only checks repository name, format, and type.

### `migration`

Contains helper code for Nexus migration readiness and source/target comparison.

Current limitation:

- most migration helpers are not registered as MCP tools.

## MCP Design

### Resources

Resources expose common read-only context that does not need user input:

- `nexus://instance/summary`
- `nexus://repositories`
- `nexus://blobstores`
- `nexus://tasks`
- `nexus://cleanup-policies`
- `nexus://security/summary`
- `nexus://architecture`
- `nexus://knowledge_graph`

Review result:

- Resource names are clear and Nexus-specific.
- `nexus://knowledge_graph` can be large on real instances and may need pagination or summary variants.
- Resources that depend on graph construction include limitations when optional endpoints are unavailable.

### Tools

Tools expose parameterized reads, generated artifacts, OpenAPI discovery, raw API calls, and guarded actions.

Current exposed tools:

- `nexus_understand_architecture`
- `nexus_explain_repository`
- `nexus_explain_storage_strategy`
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

Review result:

- Tool names are consistently prefixed with `nexus_`.
- Read-only and harmful actions are separated by safety logic, but harmful tools are still visible to agents.
- Several useful implemented helpers are not exposed as tools, including components/assets search, repository type filters, migration readiness, and instance comparison.

### Prompts

Current prompts:

- `nexus_audit_prompt`
- `nexus_iac_drift_prompt`

Review result:

- Prompts are useful as workflows.
- Prompt text should stay factual and should not claim a complete audit when the implementation only covers limited checks.

## Safety Boundaries

`src/nexus_mcp_server/safety.py` enforces operation-level gates:

- raw API disabled unless `NEXUS_MCP_ENABLE_RAW_API=true`;
- `POST`, `PUT`, and `DELETE` rejected in `readonly`;
- `POST`, `PUT`, and `DELETE` rejected in `audit`;
- writes in `admin` require `NEXUS_MCP_ENABLE_WRITE_TOOLS=true`;
- raw API paths are decoded, canonicalized, and restricted to `/service/rest/`;
- admin path parameters are URL encoded;
- tool/resource outputs are passed through recursive secret redaction.

Production review:

- safe enough for read-only observation with a read-only Nexus account;
- not yet strong enough to recommend broad production admin usage;
- needs generic output redaction and stricter internal URL handling before public release.

## Error Handling

The HTTP client maps common HTTP status codes to custom exceptions.

Known problems:

- Several helper functions catch `Exception` and return `None`, hiding permission, server, validation, and connectivity failures.
- Tool outputs do not share a common error/finding schema.

## Knowledge Graph Review

Keep:

- `NexusInstance`
- `Repository`
- `BlobStore`
- `Task`
- `CleanupPolicy`
- `RoutingRule`
- `Role`
- `Privilege`
- `User`
- `ContentSelector`
- `USES_BLOBSTORE`
- `APPLIES_CLEANUP_POLICY`
- `USES_ROUTING_RULE`
- `MEMBER_OF_GROUP`
- `HAS_PRIVILEGE`
- `ASSIGNED_ROLE`
- `RUNS_TASK`

Simplify or remove:

- `Capability`: defined but not populated; remove until there is a concrete Nexus capability reader.
- `AFFECTS_REPOSITORY`: defined but not populated; remove until task/policy impact mapping is implemented.
- `AFFECTS_BLOBSTORE`: defined but not populated; remove until task/blobstore impact mapping is implemented.
- `MANAGED_BY`: currently used from instance to objects, but the name is directionally confusing. Consider replacing with `CONTAINS` or `HAS_OBJECT`.

Do not add:

- cloud resources;
- hosts;
- GitLab projects;
- OpenStack objects;
- Kubernetes objects;
- generic service/application entities.

## Adoption Risks

GitHub users may be confused by:

- stale task prompts if left in the repository;
- unregistered helper tools;
- documentation that implies broader support than code provides;
- failing lint/type checks;
- unsafe-looking default credentials in example config;
- lack of explicit supported Nexus version notes.
