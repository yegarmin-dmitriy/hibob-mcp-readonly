import os
import json
import functools
from typing import List, Literal, Optional

from pydantic import BaseModel, Field
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

mcp = FastMCP("HiBob-ReadOnly")

_ALLOWED_API_FIELDS = {"root.id", "root.email"}


class EmployeeFilter(BaseModel):
    fieldPath: str = Field(description='Field to filter on (e.g. "work.department")')
    operator: Literal["equals", "contains"] = Field(description="Filter operator")
    values: List[str] = Field(description="Values to match")


@functools.lru_cache(maxsize=1)
def _client() -> HiBobClient:
    return HiBobClient(
        os.environ.get("HIBOB_SERVICE_USER_ID", ""),
        os.environ.get("HIBOB_API_TOKEN", ""),
    )


def _safe(data) -> str:
    if not data:
        data = {"error": ERROR_MESSAGES["empty"]}
    elif isinstance(data, dict) and "error" not in data:
        data = filter_response(data)
    return json.dumps(data, indent=2, ensure_ascii=False)


def _wrap(fn) -> str:
    try:
        return _safe(fn())
    except HiBobAPIError as e:
        return json.dumps({"error": str(e)})
    except Exception:
        return json.dumps({"error": ERROR_MESSAGES[500]})


def _validate_filters(filters: list):
    allowed = set(ALLOWED_FIELD_PREFIXES)
    api_f, client_f = [], []
    for f in filters:
        fp = f.get("fieldPath", "")
        if fp and not (fp in allowed or any(fp.startswith(p) for p in allowed)):
            continue
        (api_f if fp in _ALLOWED_API_FIELDS else client_f).append(f)
    return api_f, client_f


def _apply_client_filters(employees: list, filters: list) -> list:
    def get_nested(obj, keys):
        cur = obj
        for k in keys:
            cur = cur.get(k) if isinstance(cur, dict) else None
        return cur

    for f in filters:
        parts = (f.get("fieldPath") or "").split(".")
        operator = f.get("operator", "equals")
        values = [v.lower() for v in f.get("values", [])]
        if operator == "equals":
            employees = [e for e in employees if str(get_nested(e, parts) or "").lower() in values]
        elif operator == "contains":
            employees = [e for e in employees if any(v in str(get_nested(e, parts) or "").lower() for v in values)]
    return employees


@mcp.tool()
def search_employees(filters: Optional[List[EmployeeFilter]] = None) -> str:
    """Search for employees in HiBob. Supports optional filters on fields like work.department, work.title, root.email, etc."""
    c = _client()
    raw = [f.model_dump() for f in (filters or [])]
    api_f, client_f = _validate_filters(raw)
    body: dict = {"fields": DEFAULT_SEARCH_FIELDS, "humanReadable": "REPLACE"}
    if api_f:
        body["filters"] = api_f

    def call():
        result = c.post("people/search", body)
        if client_f and isinstance(result.get("employees"), list):
            result["employees"] = _apply_client_filters(result["employees"], client_f)
        return result

    return _wrap(call)


@mcp.tool()
def get_employee(employee_id: str) -> str:
    """Get details for a specific employee by their HiBob ID."""
    c = _client()
    body = {"fields": DEFAULT_SEARCH_FIELDS, "humanReadable": "REPLACE"}
    return _wrap(lambda: c.post(f"people/{employee_id}", body))


@mcp.tool()
def get_employee_fields() -> str:
    """Get metadata about all employee fields available in HiBob."""
    return _wrap(lambda: _client().get("company/people/fields"))


@mcp.tool()
def get_whos_out_today() -> str:
    """Get a list of employees who are out of office today."""
    return _wrap(lambda: _client().get("timeoff/outtoday"))


@mcp.tool()
def get_whos_out(from_date: str, to_date: str) -> str:
    """Get employees who are out of office in a specific date range."""
    return _wrap(lambda: _client().get(f"timeoff/whosout?from={from_date}&to={to_date}"))


@mcp.tool()
def list_timeoff_requests(employee_id: str) -> str:
    """List all time-off requests for a specific employee."""
    return _wrap(lambda: _client().get(f"timeoff/employees/{employee_id}/requests"))


@mcp.tool()
def get_timeoff_balance(employee_id: str) -> str:
    """Get the remaining time-off balance for a specific employee."""
    return _wrap(lambda: _client().get(f"timeoff/employees/{employee_id}/balance"))


@mcp.tool()
def get_timeoff_policy_types() -> str:
    """Get a list of all time-off policy types configured in HiBob."""
    return _wrap(lambda: _client().get("timeoff/policy-types"))


@mcp.tool()
def get_employee_tasks(employee_id: str) -> str:
    """Get all tasks assigned to a specific employee."""
    return _wrap(lambda: _client().get(f"tasks/people/{employee_id}"))


@mcp.tool()
def get_report(report_id: str) -> str:
    """Run an existing saved report by its ID and return the report data."""
    return _wrap(lambda: _client().get(f"company/reports/{report_id}"))


@mcp.tool()
def search_goals(
    status: Optional[str] = Field(None, description='Goal status filter, e.g. "active" or "completed"'),
    type_id: Optional[str] = Field(None, description="Goal type ID"),
) -> str:
    """Search for goals in HiBob. Optionally filter by status ('active', 'completed') or type_id."""
    filters = {k: v for k, v in {"status": status, "typeId": type_id}.items() if v is not None}
    return _wrap(lambda: _client().post("goals/goals/search", filters))


@mcp.tool()
def search_key_results(
    status: Optional[str] = Field(None, description="Key result status filter"),
    goal_id: Optional[str] = Field(None, description="Filter by parent goal ID"),
) -> str:
    """Search for key results linked to goals in HiBob."""
    filters = {k: v for k, v in {"status": status, "goalId": goal_id}.items() if v is not None}
    return _wrap(lambda: _client().post("goals/goals/key-results/search", filters))


@mcp.tool()
def search_goal_cycles(
    status: Optional[str] = Field(None, description="Cycle status filter"),
) -> str:
    """Search for goal cycles (time periods used for goal tracking) in HiBob."""
    filters = {k: v for k, v in {"status": status}.items() if v is not None}
    return _wrap(lambda: _client().post("goals/goals/goal-cycles/search", filters))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
