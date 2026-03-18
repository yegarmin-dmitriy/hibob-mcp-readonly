from hibob_mcp_readonly.constants import ALLOWED_FIELD_PREFIXES, DEFAULT_SEARCH_FIELDS


def test_allowed_fields_has_no_sensitive_prefixes():
    """No sensitive field categories should be in the whitelist."""
    sensitive = ["personal.", "identification.", "financial.", "payroll.", "home.", "about.socialData"]
    for prefix in ALLOWED_FIELD_PREFIXES:
        for s in sensitive:
            assert not prefix.startswith(s), f"Sensitive prefix {s} found in whitelist: {prefix}"


def test_allowed_fields_has_no_wildcards():
    """No wildcards — every prefix must be specific."""
    for prefix in ALLOWED_FIELD_PREFIXES:
        assert "*" not in prefix, f"Wildcard found in whitelist: {prefix}"


def test_default_search_fields_are_subset_of_allowed():
    """Every default search field must match at least one allowed prefix."""
    for field in DEFAULT_SEARCH_FIELDS:
        assert any(field.startswith(prefix) for prefix in ALLOWED_FIELD_PREFIXES), \
            f"Search field {field} not covered by whitelist"
