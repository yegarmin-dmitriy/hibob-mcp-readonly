import os
import functools
from fastmcp import FastMCP
from .api_client import HiBobClient, HiBobAPIError
from .field_filter import filter_response
from .constants import ALLOWED_FIELD_PREFIXES, DEFAULT_SEARCH_FIELDS, ERROR_MESSAGES

SERVER_INSTRUCTIONS = """You are connected to airSlate's HiBob HRIS system in READ-ONLY mode.

Rules:
- You can look up employee information, time off, tasks, and goals.
- You CANNOT modify any data. If asked to change, update, or create employee records, explain that this is a read-only integration and direct the user to HiBob UI.
- Never display raw API responses. Format data in readable tables or summaries.
- If a query returns no results, suggest alternative search terms.
- When discussing employees, use their display name and work email only.
- Do not speculate about data you cannot access (salaries, personal details, performance reviews)."""

mcp = FastMCP(
    name="HiBob-ReadOnly",
    instructions=SERVER_INSTRUCTIONS,
)


@functools.lru_cache(maxsize=1)
def _get_client() -> HiBobClient:
    return HiBobClient(
        service_user_id=os.environ.get("HIBOB_SERVICE_USER_ID", ""),
        api_token=os.environ.get("HIBOB_API_TOKEN", ""),
    )


def _safe_call(fn):
    try:
        result = fn()
        if not result:
            return {"error": ERROR_MESSAGES["empty"]}
        if isinstance(result, dict) and "error" not in result:
            return filter_response(result)
        return result
    except HiBobAPIError as e:
        return {"error": str(e)}
    except Exception:
        return {"error": ERROR_MESSAGES[500]}


def _validate_filters(filters: list) -> list:
    if not filters:
        return filters
    return [
        f for f in filters
        if "fieldPath" not in f
        or any(f["fieldPath"].startswith(prefix) for prefix in ALLOWED_FIELD_PREFIXES)
    ]


def _apply_client_filters(employees: list, filters: list) -> list:
    filtered = employees
    for f in filters:
        field_path = f.get("fieldPath", "")
        operator = f.get("operator", "equals")
        values = [v.lower() for v in f.get("values", [])]
        parts = field_path.split(".")

        def get_nested(obj, keys):
            for k in keys:
                if isinstance(obj, dict):
                    obj = obj.get(k)
                else:
                    return None
            return obj

        if operator == "equals":
            filtered = [e for e in filtered if str(get_nested(e, parts) or "").lower() in values]
        elif operator == "contains":
            filtered = [e for e in filtered if any(v in str(get_nested(e, parts) or "").lower() for v in values)]
    return filtered


@mcp.tool()
def search_employees(filters: list = None, fields: list = None) -> dict:
    """
    Search for employees in HiBob.

    Parameters:
        filters: Optional list of filters (e.g. [{"fieldPath": "work.department", "operator": "equals", "values": ["Engineering"]}])
        fields: Ignored — always uses the safe default field list.
    """
    client = _get_client()
    api_filters = []
    client_filters = []
    if filters:
        validated = _validate_filters(filters)
        for f in validated:
            fp = f.get("fieldPath", "")
            if fp in ("root.id", "root.email"):
                api_filters.append(f)
            else:
                client_filters.append(f)

    body = {"fields": DEFAULT_SEARCH_FIELDS, "humanReadable": "REPLACE"}
    if api_filters:
        body["filters"] = api_filters

    result = _safe_call(lambda: client.post("people/search", body))
    if isinstance(result, dict) and "error" not in result and client_filters:
        result["employees"] = _apply_client_filters(result.get("employees", []), client_filters)
    return result


@mcp.tool()
def get_employee(employee_id: str) -> dict:
    """Get details for a specific employee by their HiBob ID."""
    client = _get_client()
    body = {"fields": DEFAULT_SEARCH_FIELDS, "humanReadable": "REPLACE"}
    return _safe_call(lambda: client.post(f"people/{employee_id}", body))


@mcp.tool()
def get_employee_fields() -> dict:
    """Get metadata about all employee fields in HiBob."""
    return _safe_call(lambda: _get_client().get("company/people/fields"))


@mcp.tool()
def get_whos_out_today() -> dict:
    """Get a list of employees who are out of office today."""
    return _safe_call(lambda: _get_client().get("timeoff/outtoday"))


@mcp.tool()
def get_whos_out(from_date: str, to_date: str) -> dict:
    """
    Get employees who are out in a date range.

    Parameters:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    """
    return _safe_call(lambda: _get_client().get(f"timeoff/whosout?from={from_date}&to={to_date}"))


@mcp.tool()
def list_timeoff_requests(employee_id: str) -> dict:
    """List time-off requests for a specific employee."""
    return _safe_call(lambda: _get_client().get(f"timeoff/employees/{employee_id}/requests"))


@mcp.tool()
def get_timeoff_balance(employee_id: str) -> dict:
    """Get time-off balance for a specific employee."""
    return _safe_call(lambda: _get_client().get(f"timeoff/employees/{employee_id}/balance"))


@mcp.tool()
def get_timeoff_policy_types() -> dict:
    """Get a list of all time-off policy types."""
    return _safe_call(lambda: _get_client().get("timeoff/policy-types"))


@mcp.tool()
def get_employee_tasks(employee_id: str) -> dict:
    """Get all tasks assigned to a specific employee."""
    return _safe_call(lambda: _get_client().get(f"tasks/people/{employee_id}"))


@mcp.tool()
def get_report(report_id: str) -> dict:
    """Run an existing saved report by its ID. Returns report data."""
    return _safe_call(lambda: _get_client().get(f"company/reports/{report_id}"))


@mcp.tool()
def search_goals(filters: dict = None) -> dict:
    """
    Search for goals in HiBob.

    Parameters:
        filters: Optional filter object (e.g. {"status": "active", "typeId": "..."})
    """
    return _safe_call(lambda: _get_client().post("goals/goals/search", filters or {}))


@mcp.tool()
def search_key_results(filters: dict = None) -> dict:
    """Search for key results linked to goals."""
    return _safe_call(lambda: _get_client().post("goals/goals/key-results/search", filters or {}))


@mcp.tool()
def search_goal_cycles(filters: dict = None) -> dict:
    """Search for goal cycles (time periods for goal tracking)."""
    return _safe_call(lambda: _get_client().post("goals/goals/goal-cycles/search", filters or {}))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
