"""
Field filter module for HiBob MCP readonly extension.

Implements whitelist-based filtering of API responses, ensuring only
whitelisted fields pass through to Claude. Handles both flat employee
dicts and search results with employee lists.
"""

from .constants import ALLOWED_FIELD_PREFIXES


def _allowed_top_level_keys():
    """Derive allowed top-level keys from the prefix whitelist."""
    keys = set()
    for prefix in ALLOWED_FIELD_PREFIXES:
        keys.add(prefix.split(".")[0])
    return keys


def _allowed_subkeys(top_key: str):
    """Derive allowed subkeys for a given top-level key."""
    subkeys = set()
    for prefix in ALLOWED_FIELD_PREFIXES:
        parts = prefix.split(".", 1)
        if parts[0] == top_key and len(parts) > 1:
            subkeys.add(parts[1].split(".")[0])
    return subkeys


def _is_allowed_field(key: str) -> bool:
    """Check if a flat dotted field key matches any allowed prefix."""
    return any(key.startswith(prefix) for prefix in ALLOWED_FIELD_PREFIXES)


def _filter_employee_nested(employee: dict) -> dict:
    """Filter a nested employee dict (humanReadable format), keeping only whitelisted fields."""
    allowed_top = _allowed_top_level_keys()
    result = {}
    for key, value in employee.items():
        if key not in allowed_top:
            continue
        if isinstance(value, dict):
            allowed_sub = _allowed_subkeys(key)
            if allowed_sub:
                result[key] = {k: v for k, v in value.items() if k in allowed_sub}
            else:
                result[key] = value
        else:
            result[key] = value
    return result


def _filter_employee_flat(employee: dict) -> dict:
    """Filter a flat employee dict (dotted keys), keeping only whitelisted fields."""
    return {k: v for k, v in employee.items() if _is_allowed_field(k)}


def _filter_employee_dict(employee: dict) -> dict:
    """Filter an employee dict, auto-detecting nested vs flat key format."""
    if any("." in k for k in employee.keys()):
        return _filter_employee_flat(employee)
    return _filter_employee_nested(employee)


def filter_response(data: dict) -> dict:
    """
    Filter API response, keeping only whitelisted fields in employee records.

    Handles three response shapes:
    1. Nested employee dict: {"work": {"department": ...}, "financial": {"salary": ...}}
    2. Flat employee dict: {"root.displayName": ..., "financial.salary": ...}
    3. Search result: {"employees": [...], "totalCount": N}

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

    # Shape: single employee record — detect by checking for known top-level keys
    known_employee_keys = _allowed_top_level_keys() | {"root", "work", "employment", "internal", "financial", "personal", "payroll"}
    if any(k in known_employee_keys for k in data.keys()):
        return _filter_employee_dict(data)

    # Shape: other responses (timeoff, tasks, goals) — pass through
    return data
