# Compatibility Matrix

Compatibility is based on implemented behavior and available test evidence. Do not treat inferred support as verified production support.

## Nexus Versions

| Nexus Version | Status | Evidence |
| --- | --- | --- |
| Nexus OSS 3.70 | Partially verified | Mock compatibility tests cover sparse repository lists, missing optional endpoints, task `currentState`, and repository detail enrichment. Live validation was performed against a 3.70.1-02 instance during development. |
| Nexus Pro 3.96.1-01 (HA) | Used in production (read-only) | The maintainer runs read-only mode with the GET-only raw API against two production instances: inventory, graph, audit, repository content audit and raw `GET` tools. Admin write tools were not exercised. No fixtures in this repository yet. |
| Nexus OSS 3.90 | Inferred | No live or fixture validation in this repository yet. Capability discovery and optional collectors should reduce version-specific failures. |
| Nexus OSS 3.92 | Inferred | No live or fixture validation in this repository yet. Capability discovery and optional collectors should reduce version-specific failures. |
| Future Nexus versions | Unverified | The server relies on `/service/rest/swagger.json` and optional collector handling, but future API changes must be tested. |

## Feature Compatibility

| Feature | 3.70 | 3.90 | 3.92 | Notes |
| --- | --- | --- | --- | --- |
| Repository inventory | Partially verified | Inferred | Inferred | Sparse 3.70 list response is tested. |
| Blobstore inventory | Partially verified | Inferred | Inferred | Basic list response is tested through graph fixtures. |
| Task inventory | Partially verified | Inferred | Inferred | `currentState` is accepted when `status` is absent. |
| Cleanup policies | Partially verified | Inferred | Inferred | Missing endpoint is handled as a limitation. |
| Routing rules | Partially verified | Inferred | Inferred | Missing endpoint is handled as a limitation. |
| Content selectors | Partially verified | Inferred | Inferred | Missing endpoint is handled as a limitation. |
| Security users/roles/privileges | Partially verified | Inferred | Inferred | Missing endpoints are handled as limitations. Sparse privilege responses are tested. |
| Repository-to-blobstore relationship | Partially verified | Inferred | Inferred | Works when OpenAPI advertises repository detail endpoints and details include `storage.blobStoreName`. |
| Audit report | Partially verified | Inferred | Inferred | Limited to REST-visible graph inventory and operational findings. |
| Terraform/Puppet context | Partially verified | Inferred | Inferred | Basic repository context only. |
| Raw API tool | Partially verified | Inferred | Inferred | Safety behavior is tested; endpoint semantics depend on Nexus version. |
| Admin write tools | Partially verified | Inferred | Inferred | Safety gates and path encoding are tested; production use requires admin opt-in. |

Feature columns above cover OSS. On Nexus Pro 3.96.1-01 every read feature was used in read-only mode; the admin write tools were not exercised.

## Compatibility Rules

- Core collectors may fail graph construction.
- Optional, pro-only, and experimental collectors must record limitations instead of failing graph construction.
- Missing OpenAPI paths are treated as unavailable capabilities.
- Sparse REST responses must use safe defaults instead of failing Pydantic validation.
- Feature output must include limitations when data is unavailable because of version, edition, or permissions.
