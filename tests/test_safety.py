import pytest
from nexus_mcp_server.safety import redact_secrets, validate_operation, validate_path
from nexus_mcp_server.config import Settings, McpMode
from nexus_mcp_server.errors import SafetyError


def test_validate_operation_readonly() -> None:
    settings = Settings.model_validate(
        {"NEXUS_URL": "http://loc", "NEXUS_MCP_MODE": McpMode.READONLY}
    )

    # GET should pass
    validate_operation(settings, "GET")

    # POST should fail
    with pytest.raises(SafetyError, match="not allowed in readonly mode"):
        validate_operation(settings, "POST")


def test_validate_operation_raw_api_disabled() -> None:
    settings = Settings.model_validate(
        {"NEXUS_URL": "http://loc", "NEXUS_MCP_ENABLE_RAW_API": False}
    )

    with pytest.raises(SafetyError, match="Raw API calls are disabled"):
        validate_operation(settings, "GET", is_raw_api=True)

def test_validate_path_safety() -> None:
    # Valid path
    assert validate_path("/service/rest/v1/repositories") == "/service/rest/v1/repositories"

    # Invalid prefix
    with pytest.raises(SafetyError, match="stay under /service/rest/"):
        validate_path("/other/api")

    # Traversal
    with pytest.raises(SafetyError, match="non-canonical|traversal|stay under"):
        validate_path("/service/rest/../../etc/passwd")

    # Encoded traversal
    with pytest.raises(SafetyError, match="non-canonical|traversal|stay under"):
        validate_path("/service/rest/%2e%2e/%2e%2e/etc/passwd")

    # Absolute URL
    with pytest.raises(SafetyError, match="relative"):
        validate_path("https://evil.example/service/rest/v1/repositories")


def test_validate_operation_write_requires_admin_and_enablement() -> None:
    readonly = Settings.model_validate(
        {"NEXUS_URL": "http://loc", "NEXUS_MCP_MODE": McpMode.READONLY}
    )
    audit = Settings.model_validate(
        {"NEXUS_URL": "http://loc", "NEXUS_MCP_MODE": McpMode.AUDIT}
    )
    admin_disabled = Settings.model_validate(
        {"NEXUS_URL": "http://loc", "NEXUS_MCP_MODE": McpMode.ADMIN}
    )
    admin_enabled = Settings.model_validate(
        {
            "NEXUS_URL": "http://loc",
            "NEXUS_MCP_MODE": McpMode.ADMIN,
            "NEXUS_MCP_ENABLE_WRITE_TOOLS": True,
        }
    )

    with pytest.raises(SafetyError, match="readonly"):
        validate_operation(readonly, "DELETE")
    with pytest.raises(SafetyError, match="audit"):
        validate_operation(audit, "POST")
    with pytest.raises(SafetyError, match="Write operations are disabled"):
        validate_operation(admin_disabled, "PUT")

    validate_operation(admin_enabled, "DELETE")


def test_redact_secrets_recursively() -> None:
    data = {
        "password": "direct",
        "nested": {
            "token": "abc",
            "message": "contains configured-secret here",
        },
        "items": [{"apiKey": "key"}],
    }

    assert redact_secrets(data, ["configured-secret"]) == {
        "password": "********",
        "nested": {
            "token": "********",
            "message": "contains ******** here",
        },
        "items": [{"apiKey": "********"}],
    }
