from nexus_mcp_server.models import Privilege


def test_privilege_properties_defaults_to_empty_dict() -> None:
    privilege = Privilege(
        name="nx-all",
        description="All permissions",
        type="wildcard",
        readOnly=True,
    )

    assert privilege.properties == {}


def test_privilege_accepts_sparse_response() -> None:
    privilege = Privilege(name="nx-repository-view")

    assert privilege.type == "unknown"
    assert privilege.readOnly is False
    assert privilege.properties == {}
