"""
Security verification tests.
These tests ensure the extension maintains its read-only guarantees.
"""
import asyncio
import inspect
from hibob_mcp_readonly import server as server_module
from hibob_mcp_readonly.api_client import HiBobClient
from hibob_mcp_readonly.constants import ALLOWED_FIELD_PREFIXES


class TestNoWriteEndpoints:
    def test_api_client_has_no_put(self):
        assert not hasattr(HiBobClient, "put")

    def test_api_client_has_no_delete(self):
        assert not hasattr(HiBobClient, "delete")

    def test_api_client_has_no_patch(self):
        assert not hasattr(HiBobClient, "patch")


class TestNoWriteHTTPCalls:
    def test_server_source_has_no_put_calls(self):
        """Grep server.py source for PUT/DELETE/PATCH calls."""
        source = inspect.getsource(server_module)
        assert 'method="PUT"' not in source
        assert 'method="DELETE"' not in source
        assert 'method="PATCH"' not in source
        assert "requests.put" not in source
        assert "requests.delete" not in source
        assert "requests.patch" not in source

    def test_api_client_source_has_no_write_methods(self):
        """API client source should have no PUT/DELETE/PATCH."""
        from hibob_mcp_readonly import api_client
        source = inspect.getsource(api_client)
        assert "requests.put" not in source
        assert "requests.delete" not in source
        assert "requests.patch" not in source


class TestWhitelistIntegrity:
    def test_no_sensitive_categories_in_whitelist(self):
        sensitive = [
            "personal.", "identification.", "financial.",
            "payroll.", "home.", "about.socialData",
        ]
        for prefix in ALLOWED_FIELD_PREFIXES:
            for s in sensitive:
                assert not prefix.startswith(s), \
                    f"SECURITY: Sensitive prefix '{s}' found in whitelist via '{prefix}'"

    def test_no_wildcard_in_whitelist(self):
        for prefix in ALLOWED_FIELD_PREFIXES:
            assert "*" not in prefix, \
                f"SECURITY: Wildcard in whitelist: {prefix}"


class TestToolInventory:
    def test_only_expected_tools_registered(self):
        """Verify the exact set of registered tools — no surprises."""
        expected_tools = {
            "search_employees",
            "get_employee",
            "get_employee_fields",
            "get_whos_out_today",
            "get_whos_out",
            "list_timeoff_requests",
            "get_timeoff_balance",
            "get_timeoff_policy_types",
            "get_employee_tasks",
            "get_report",
            "search_goals",
            "search_key_results",
            "search_goal_cycles",
        }
        # FastMCP v3: use async list_tools() — the authoritative public API
        tools = asyncio.run(server_module.mcp.list_tools())
        registered = {t.name for t in tools}
        assert registered == expected_tools, \
            f"Unexpected tools: {registered - expected_tools}, Missing: {expected_tools - registered}"
