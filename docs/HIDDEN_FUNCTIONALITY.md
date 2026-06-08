# Hidden Functionality Audit

This table covers implemented functions that are not directly registered as MCP tools or resources.

| Function | Purpose | Test Coverage | Version Compatibility | Safe To Expose | Recommendation |
| --- | --- | --- | --- | --- | --- |
| `tools.components.search_components` | Search components through `/v1/components`. | None. | Inferred; endpoint is common but response shapes may vary by format. | Not yet; needs limit bounds and tests. | Keep internal. |
| `tools.components.get_component` | Fetch a component by id. | None. | Inferred; direct id endpoint is common. | Not yet; broad exception hides failures. | Keep internal. |
| `tools.assets.search_assets` | Search assets through `/v1/assets`. | None. | Inferred; endpoint is common but metadata differs by format. | Not yet; needs limit bounds and tests. | Keep internal. |
| `tools.compare.compare_instances` | Compare repositories/blobstores between source and target Nexus. | None. | Inferred; depends on repository/blobstore list compatibility on both instances. | Not yet; target client lifecycle and docs need validation. | Keep internal. |
| `tools.system.get_system_metrics` | Read `/v1/status/check`. | None. | Unverified; endpoint/permissions may differ. | No; optional endpoint handling needed. | Keep internal. |
| `tools.system.readiness_basic_check` | Basic API reachability check. | None. | Inferred; uses status and repositories. | No; broad exception hides failure reason. | Keep internal. |
| `tools.tasks.get_task` | Fetch a task by id. | None. | Inferred; id endpoint may differ by version/permissions. | No; broad exception hides failures. | Keep internal. |
| `tools.config_objects.get_routing_rule` | Fetch a routing rule by name. | None. | Unverified; routing rules may be absent. | No; broad exception hides failures. | Keep internal. |
| `tools.migration.generate_migration_readiness_report` | Basic migration readiness summary. | None. | Inferred; uses repositories/blobstores/tasks. | Not yet; output is shallow and not graph-tolerant. | Keep internal. |
| `tools.migration.generate_cutover_checklist` | Static migration checklist. | None. | Version-independent static text. | No; not live Nexus functionality. | Keep internal or delete. |
| `tools.migration.generate_repository_inventory_report` | Repository inventory Markdown. | None. | Inferred; overlaps exposed inventory/catalog tools. | No; duplicate value. | Delete or keep internal. |
| `tools.migration.generate_hosted_repository_activity_report` | Hosted repository activity proxy using assets. | None. | Unverified; activity inference is weak. | No; could mislead users. | Keep internal or delete. |
| `tools.security.get_anonymous_status` | Read anonymous access status. | None. | Inferred; may require privileges. | Not yet; useful audit input after tests. | Keep internal. |
| `tools.security.list_realms` | Read active security realms. | None. | Inferred; may require privileges/edition differences. | Not yet; useful audit input after tests. | Keep internal. |
| `tools.blobstores.get_blobstore` | Fetch blobstore details by name. | None. | Inferred; details vary by blobstore type. | No; broad exception hides failures. | Keep internal. |
| `tools.blobstores.generate_blobstore_usage_report` | Markdown blobstore usage report. | None. | Inferred; overlaps graph storage tools. | No; output uses limited REST fields. | Keep internal. |
| `tools.repositories.get_repository` | Find repository by name from list. | None. | Verified indirectly through repository list behavior. | No; internal convenience wrapper. | Keep internal. |
| `tools.repositories.find_repositories_by_type` | Filter repository list by type. | None. | Verified indirectly through repository list behavior. | No; too small for public tool. | Keep internal. |
| `tools.repositories.find_hosted_repositories` | Group hosted repositories by format. | None. | Verified indirectly through repository list behavior. | No; too small for public tool. | Keep internal. |
| `tools.repositories.find_proxy_repositories` | Filter proxy repositories. | None. | Verified indirectly through repository list behavior. | No; too small for public tool. | Keep internal. |
| `tools.repositories.find_group_repositories` | Filter group repositories. | None. | Verified indirectly through repository list behavior. | No; too small for public tool. | Keep internal. |
| `openapi.OpenApiHelper.find_operations` | Search OpenAPI operations. | None. | Inferred; depends on swagger availability. | Yes after tests; useful but not currently exposed. | Keep internal. |
| `openapi.OpenApiHelper.get_operation_schema` | Return request/response schema for an OpenAPI operation. | None. | Inferred; depends on swagger availability. | Yes after tests; useful but not currently exposed. | Keep internal. |

Release decision:

- Do not expose additional hidden functions for GitHub beta.
- Hidden functions either need tests, clearer failure behavior, or documentation before becoming MCP tools.
- Functions that duplicate exposed tools should be deleted or left internal, not exposed.
