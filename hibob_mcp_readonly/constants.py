"""
Constants for HiBob MCP readonly extension.

This module defines the security whitelist that controls which HiBob employee
fields can be queried and passed to Claude. Only fields matching
ALLOWED_FIELD_PREFIXES are exposed.
"""

HIBOB_API_BASE = "https://api.hibob.com/v1"

# Whitelist: ONLY these field prefixes pass through to Claude.
# If HiBob adds a new field category, it is automatically excluded.
ALLOWED_FIELD_PREFIXES = [
    "root.id",
    "root.fullName",
    "root.firstName",
    "root.surname",
    "root.email",
    "root.avatar",
    # With humanReadable, root. prefix is stripped: root.email -> email, root.fullName -> fullName
    "id",
    "fullName",
    "firstName",
    "surname",
    "email",
    "displayName",
    "work.title",
    "work.department",
    "work.team",
    "work.site",
    "work.reportsTo",
    "work.startDate",
    "work.tenureDuration",
    "work.costCenter",
    "work.product",
    "employment.contract",
    "internal.lifecycleStatus",
    "internal.status",
]

# Fields requested in employee search POST body.
# Constrains what Claude can ask for — even if it requests other fields, they are ignored.
DEFAULT_SEARCH_FIELDS = [
    "root.id",
    "root.fullName",
    "root.firstName",
    "root.surname",
    "root.email",
    "work.title",
    "work.department",
    "work.team",
    "work.site",
    "work.reportsTo.displayName",
    "work.startDate",
    "work.tenureDuration",
    "work.costCenter",
    "work.product",
    "internal.lifecycleStatus",
    "internal.status",
]

# Friendly error messages — no API details or tokens leaked.
ERROR_MESSAGES = {
    401: "HiBob connection failed. Your API token may have expired. Please contact IT (Dima) to get a new token.",
    429: "HiBob is temporarily busy. Please wait a moment and try again.",
    500: "HiBob is currently unavailable. Please try again later.",
    "timeout": "HiBob didn't respond in time. Please try again.",
    "empty": "No data available for this query with current access permissions.",
}

REQUEST_TIMEOUT_SECONDS = 30
