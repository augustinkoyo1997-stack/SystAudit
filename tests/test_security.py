from src.security import (
    is_administrator,
    get_security_info,
    get_local_administrators,
)


def test_is_administrator():
    result = is_administrator()
    assert isinstance(result, bool)


def test_get_security_info():
    result = get_security_info()

    assert isinstance(result, dict)
    assert "operating_system" in result
    assert "hostname" in result
    assert "administrator" in result

    assert isinstance(result["operating_system"], str)
    assert isinstance(result["hostname"], str)
    assert isinstance(result["administrator"], bool)

def test_get_local_administrators():
    result = get_local_administrators()

    assert isinstance(result, list)

    for administrator in result:
        assert isinstance(administrator, str)