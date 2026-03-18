import pytest
import responses
from hibob_mcp_readonly.constants import HIBOB_API_BASE, DEFAULT_SEARCH_FIELDS
from hibob_mcp_readonly.server import mcp


class TestSearchEmployees:
    @responses.activate
    def test_returns_filtered_employee_data(self):
        """search_employees should return only whitelisted fields."""
        responses.add(
            responses.POST,
            f"{HIBOB_API_BASE}/people/search",
            json={
                "employees": [
                    {
                        "root.displayName": "Jane Doe",
                        "root.email": "jane@airslate.com",
                        "financial.salary": 120000,
                        "identification.ssn": "123-45-6789",
                    }
                ]
            },
            status=200,
        )
        # Call the tool function directly
        from hibob_mcp_readonly.server import search_employees
        result = search_employees()
        assert len(result["employees"]) == 1
        emp = result["employees"][0]
        assert emp["root.displayName"] == "Jane Doe"
        assert "financial.salary" not in emp
        assert "identification.ssn" not in emp

    @responses.activate
    def test_enforces_default_search_fields(self):
        """search_employees should always use DEFAULT_SEARCH_FIELDS, ignoring custom fields."""
        responses.add(
            responses.POST,
            f"{HIBOB_API_BASE}/people/search",
            json={"employees": []},
            status=200,
        )
        from hibob_mcp_readonly.server import search_employees
        search_employees(fields=["financial.salary", "identification.ssn"])
        # Verify the actual POST body used DEFAULT_SEARCH_FIELDS
        sent_body = responses.calls[0].request.body
        import json
        body = json.loads(sent_body)
        assert body["fields"] == DEFAULT_SEARCH_FIELDS


class TestGetEmployee:
    @responses.activate
    def test_returns_filtered_single_employee(self):
        responses.add(
            responses.GET,
            f"{HIBOB_API_BASE}/people/123",
            json={
                "root.displayName": "John Smith",
                "root.email": "john@airslate.com",
                "payroll.bankAccount": "XXXX-1234",
            },
            status=200,
        )
        from hibob_mcp_readonly.server import get_employee
        result = get_employee(employee_id="123")
        assert result["root.displayName"] == "John Smith"
        assert "payroll.bankAccount" not in result


class TestTimeOffTools:
    @responses.activate
    def test_get_whos_out_today(self):
        responses.add(
            responses.GET,
            f"{HIBOB_API_BASE}/timeoff/outtoday",
            json={"outs": [{"employeeId": "1", "employeeDisplayName": "Jane"}]},
            status=200,
        )
        from hibob_mcp_readonly.server import get_whos_out_today
        result = get_whos_out_today()
        assert len(result["outs"]) == 1
