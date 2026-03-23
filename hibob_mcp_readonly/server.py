import os
import functools
from fastmcp import FastMCP
from hibob_mcp_readonly.api_client import HiBobClient, HiBobAPIError
from hibob_mcp_readonly.field_filter import filter_response
from hibob_mcp_readonly.constants import ALLOWED_FIELD_PREFIXES, DEFAULT_SEARCH_FIELDS, ERROR_MESSAGES

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


def _get_client() -> HiBobClient:
    """Create HiBob client from environment variables."""
    return HiBobClient(
        service_user_id=os.environ.get("HIBOB_SERVICE_USER_ID", ""),
        api_token=os.environ.get("HIBOB_API_TOKEN", ""),
    )


def _safe_call(fn):
    """Wrapper that catches API errors and returns friendly messages."""
    try:
        result = fn()
        if not result:
            return {"error": ERROR_MESSAGES["empty"]}
        return result
    except HiBobAPIError as e:
        return {"error": str(e)}
    except Exception:
        return {"error": ERROR_MESSAGES[500]}


def _validate_filters(filters: list) -> list:
    """Remove filter conditions that reference fields outside the whitelist."""
    if not filters:
        return filters
    return [
        f for f in filters
        if "fieldPath" not in f
        or any(f["fieldPath"].startswith(prefix) for prefix in ALLOWED_FIELD_PREFIXES)
    ]


# ── Middleware: auto-filter ALL tool responses ──
# Every tool response passes through filter_response automatically.
# This ensures new tools cannot bypass the filter.

_original_tool_decorator = mcp.tool


def _filtered_tool(*args, **kwargs):
    """Wrap mcp.tool() so every tool's return value is filtered."""
    decorator = _original_tool_decorator(*args, **kwargs)
    def wrapper(fn):
        @functools.wraps(fn)
        def filtered_fn(*a, **kw):
            result = fn(*a, **kw)
            if isinstance(result, dict) and "error" not in result:
                return filter_response(result)
            return result
        # Register the filtered wrapper with FastMCP
        decorator(filtered_fn)
        # Return filtered_fn so that direct calls (e.g. from tests) also go through the filter
        return filtered_fn
    return wrapper


mcp.tool = _filtered_tool


# ── Employee Tools ──

@mcp.tool()
def search_employees(filters: list = None, fields: list = None) -> dict:
    """
    Search for employees in HiBob.

    Parameters:
        filters: Optional list of filters (e.g. [{"fieldPath": "work.department", "operator": "equals", "values": ["Engineering"]}])
        fields: Ignored — always uses the safe default field list.
    """
    client = _get_client()
    # HiBob API only supports filters on root.id and root.email.
    # All other filters (e.g. work.department) are applied client-side.
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


def _apply_client_filters(employees: list, filters: list) -> list:
    """Apply filters client-side for fields HiBob API doesn't support filtering on."""
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
def get_employee(employee_id: str) -> dict:
    """Get details for a specific employee by their HiBob ID."""
    client = _get_client()
    body = {"fields": DEFAULT_SEARCH_FIELDS, "humanReadable": "REPLACE"}
    return _safe_call(lambda: client.post(f"people/{employee_id}", body))


@mcp.tool()
def get_employee_fields() -> dict:
    """Get metadata about all employee fields in HiBob."""
    client = _get_client()
    return _safe_call(lambda: client.get("company/people/fields"))


# ── Time Off Tools ──

@mcp.tool()
def get_whos_out_today() -> dict:
    """Get a list of employees who are out of office today."""
    client = _get_client()
    return _safe_call(lambda: client.get("timeoff/outtoday"))


@mcp.tool()
def get_whos_out(from_date: str, to_date: str) -> dict:
    """
    Get employees who are out in a date range.

    Parameters:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    """
    client = _get_client()
    return _safe_call(lambda: client.get(f"timeoff/whosout?from={from_date}&to={to_date}"))


@mcp.tool()
def list_timeoff_requests(employee_id: str) -> dict:
    """List time-off requests for a specific employee."""
    client = _get_client()
    return _safe_call(lambda: client.get(f"timeoff/employees/{employee_id}/requests"))


@mcp.tool()
def get_timeoff_balance(employee_id: str) -> dict:
    """Get time-off balance for a specific employee."""
    client = _get_client()
    return _safe_call(lambda: client.get(f"timeoff/employees/{employee_id}/balance"))


@mcp.tool()
def get_timeoff_policy_types() -> dict:
    """Get a list of all time-off policy types."""
    client = _get_client()
    return _safe_call(lambda: client.get("timeoff/policy-types"))


# ── Task Tools ──

@mcp.tool()
def get_employee_tasks(employee_id: str) -> dict:
    """Get all tasks assigned to a specific employee."""
    client = _get_client()
    return _safe_call(lambda: client.get(f"tasks/people/{employee_id}"))


# ── Reports Tools ──

@mcp.tool()
def get_report(report_id: str) -> dict:
    """Run an existing saved report by its ID. Returns report data."""
    client = _get_client()
    return _safe_call(lambda: client.get(f"company/reports/{report_id}"))


# ── Goals Tools (Talent Module) ──

@mcp.tool()
def search_goals(filters: dict = None) -> dict:
    """
    Search for goals in HiBob.

    Parameters:
        filters: Optional filter object (e.g. {"status": "active", "typeId": "..."})
    """
    client = _get_client()
    body = filters or {}
    return _safe_call(lambda: client.post("goals/goals/search", body))


@mcp.tool()
def search_key_results(filters: dict = None) -> dict:
    """Search for key results linked to goals."""
    client = _get_client()
    body = filters or {}
    return _safe_call(lambda: client.post("goals/goals/key-results/search", body))


@mcp.tool()
def search_goal_cycles(filters: dict = None) -> dict:
    """Search for goal cycles (time periods for goal tracking)."""
    client = _get_client()
    body = filters or {}
    return _safe_call(lambda: client.post("goals/goals/goal-cycles/search", body))


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
