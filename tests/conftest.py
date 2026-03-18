import pytest
import os


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Set required env vars for all tests."""
    monkeypatch.setenv("HIBOB_SERVICE_USER_ID", "test-service-user-id")
    monkeypatch.setenv("HIBOB_API_TOKEN", "test-api-token")
