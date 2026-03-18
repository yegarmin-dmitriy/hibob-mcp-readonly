import base64
import requests
from hibob_mcp_readonly.constants import (
    HIBOB_API_BASE,
    ERROR_MESSAGES,
    REQUEST_TIMEOUT_SECONDS,
)


class HiBobAPIError(Exception):
    """Friendly error raised when HiBob API returns an error."""
    pass


class HiBobClient:
    """Read-only HTTP client for HiBob API. No PUT/DELETE/PATCH methods exist."""

    def __init__(self, service_user_id: str, api_token: str):
        # HiBob uses Basic auth: base64(service_user_id:api_token)
        credentials = base64.b64encode(
            f"{service_user_id}:{api_token}".encode()
        ).decode()
        self._headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "X-Request-Source": "airslate-hibob-mcp-readonly",
        }

    def _handle_error(self, status_code: int):
        """Raise a friendly error based on HTTP status code."""
        if status_code in ERROR_MESSAGES:
            raise HiBobAPIError(ERROR_MESSAGES[status_code])
        if status_code >= 500:
            raise HiBobAPIError(ERROR_MESSAGES[500])
        raise HiBobAPIError(f"HiBob API returned status {status_code}")

    def _parse_response(self, response: requests.Response) -> dict:
        """Parse response JSON, handling non-JSON error pages gracefully."""
        if not response.ok:
            self._handle_error(response.status_code)
        try:
            return response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            raise HiBobAPIError(ERROR_MESSAGES[500])

    def get(self, endpoint: str) -> dict:
        """Make a GET request. Returns parsed JSON."""
        url = f"{HIBOB_API_BASE}/{endpoint}"
        try:
            response = requests.get(
                url, headers=self._headers, timeout=REQUEST_TIMEOUT_SECONDS
            )
        except requests.exceptions.Timeout:
            raise HiBobAPIError(ERROR_MESSAGES["timeout"])
        except requests.exceptions.RequestException:
            raise HiBobAPIError(ERROR_MESSAGES[500])
        return self._parse_response(response)

    def post(self, endpoint: str, body: dict) -> dict:
        """Make a POST request (for search endpoints only). Returns parsed JSON."""
        url = f"{HIBOB_API_BASE}/{endpoint}"
        try:
            response = requests.post(
                url, json=body, headers=self._headers, timeout=REQUEST_TIMEOUT_SECONDS
            )
        except requests.exceptions.Timeout:
            raise HiBobAPIError(ERROR_MESSAGES["timeout"])
        except requests.exceptions.RequestException:
            raise HiBobAPIError(ERROR_MESSAGES[500])
        return self._parse_response(response)
