"""
Field filter module for HiBob MCP readonly extension.

Implements whitelist-based filtering of API responses, ensuring only
whitelisted fields pass through to Claude. Handles both flat employee
dicts and search results with employee lists.
"""

from hibob_mcp_readonly.constants import ALLOWED_FIELD_PREFIXES


def _is_allowed_field(key: str) -> bool:
    """Check if a field key matches any allowed prefix."""
    return any(key.startswith(prefix) for prefix in ALLOWED_FIELD_PREFIXES)


def _filter_employee_dict(employee: dict) -> dict:
    """Filter a single employee dict, keeping only whitelisted fields."""
    return {k: v for k, v in employee.items() if _is_allowed_field(k)}


def filter_response(data: dict) -> dict:
    """
    Filter API response, keeping only whitelisted fields in employee records.

    Handles two response shapes:
    1. Flat employee dict: {"root.displayName": ..., "financial.salary": ...}
    2. Search result: {"employees": [...], "totalCount": N}

    Args:
        data: API response dict to filter.

    Returns:
        Filtered dict with only whitelisted fields preserved.
    """
    if not data:
        return data

    # Shape: search results with "employees" list
    if "employees" in data:
        filtered = {k: v for k, v in data.items() if k != "employees"}
        filtered["employees"] = [
            _filter_employee_dict(emp) for emp in data["employees"]
        ]
        return filtered

    # Shape: single employee record (flat dict with dotted keys)
    if any("." in k for k in data.keys()):
        return _filter_employee_dict(data)

    # Shape: other responses (timeoff, tasks, goals) — pass through
    return data
