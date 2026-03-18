from hibob_mcp_readonly.field_filter import filter_response


def test_allows_whitelisted_fields():
    data = {
        "root.displayName": "Jane Doe",
        "root.email": "jane@airslate.com",
        "work.title": "HR Manager",
    }
    result = filter_response(data)
    assert result == data


def test_strips_sensitive_fields():
    data = {
        "root.displayName": "Jane Doe",
        "financial.salary": 120000,
        "identification.ssn": "123-45-6789",
        "home.address": "123 Main St",
        "personal.phone": "+1234567890",
    }
    result = filter_response(data)
    assert result == {"root.displayName": "Jane Doe"}


def test_handles_nested_employee_list():
    """HiBob /people/search returns {"employees": [{"root.displayName": ...}, ...]}"""
    data = {
        "employees": [
            {
                "root.displayName": "Jane Doe",
                "root.email": "jane@airslate.com",
                "financial.salary": 120000,
            },
            {
                "root.displayName": "John Smith",
                "root.email": "john@airslate.com",
                "payroll.bankAccount": "XXXX",
            },
        ]
    }
    result = filter_response(data)
    assert result == {
        "employees": [
            {"root.displayName": "Jane Doe", "root.email": "jane@airslate.com"},
            {"root.displayName": "John Smith", "root.email": "john@airslate.com"},
        ]
    }


def test_handles_empty_response():
    assert filter_response({}) == {}
    assert filter_response({"employees": []}) == {"employees": []}


def test_preserves_non_employee_metadata():
    """Non-employee fields like pagination should pass through."""
    data = {
        "employees": [{"root.displayName": "Jane", "financial.salary": 100}],
        "totalCount": 1,
    }
    result = filter_response(data)
    assert result["totalCount"] == 1
    assert result["employees"] == [{"root.displayName": "Jane"}]


def test_unknown_prefix_is_stripped():
    """Any field not in ALLOWED_FIELD_PREFIXES is removed."""
    data = {
        "root.displayName": "Jane",
        "newCategory.somefield": "surprise",
    }
    result = filter_response(data)
    assert "newCategory.somefield" not in result
