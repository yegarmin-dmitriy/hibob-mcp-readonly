import pytest
import responses
from requests.exceptions import Timeout
from hibob_mcp_readonly.api_client import HiBobClient, HiBobAPIError
from hibob_mcp_readonly.constants import HIBOB_API_BASE


@pytest.fixture
def client():
    return HiBobClient(service_user_id="test-id", api_token="test-token")


class TestHiBobClientGet:
    @responses.activate
    def test_successful_get(self, client):
        responses.add(
            responses.GET,
            f"{HIBOB_API_BASE}/company/people/fields",
            json={"fields": []},
            status=200,
        )
        result = client.get("company/people/fields")
        assert result == {"fields": []}

    @responses.activate
    def test_get_401_raises_friendly_error(self, client):
        responses.add(
            responses.GET,
            f"{HIBOB_API_BASE}/company/people/fields",
            status=401,
        )
        with pytest.raises(HiBobAPIError, match="API token may have expired"):
            client.get("company/people/fields")

    @responses.activate
    def test_get_429_raises_friendly_error(self, client):
        responses.add(
            responses.GET,
            f"{HIBOB_API_BASE}/company/people/fields",
            status=429,
        )
        with pytest.raises(HiBobAPIError, match="temporarily busy"):
            client.get("company/people/fields")

    @responses.activate
    def test_get_500_raises_friendly_error(self, client):
        responses.add(
            responses.GET,
            f"{HIBOB_API_BASE}/company/people/fields",
            status=500,
        )
        with pytest.raises(HiBobAPIError, match="currently unavailable"):
            client.get("company/people/fields")


class TestHiBobClientPost:
    @responses.activate
    def test_successful_post(self, client):
        responses.add(
            responses.POST,
            f"{HIBOB_API_BASE}/people/search",
            json={"employees": []},
            status=200,
        )
        result = client.post("people/search", body={"fields": ["root.displayName"]})
        assert result == {"employees": []}


class TestNoWriteMethods:
    def test_client_has_no_put_method(self, client):
        assert not hasattr(client, "put")

    def test_client_has_no_delete_method(self, client):
        assert not hasattr(client, "delete")

    def test_client_has_no_patch_method(self, client):
        assert not hasattr(client, "patch")
