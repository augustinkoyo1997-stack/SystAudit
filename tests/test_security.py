from src.security import (
    is_administrator,
    get_security_info,
    get_local_administrators,
    get_local_users,
    get_disabled_users,
    get_firewall_status,
    get_antivirus_status,
    get_windows_updates,
    get_password_policy,
    get_logged_in_users,
    get_bitlocker_status,
    get_password_never_expires_users,
    get_uac_status,
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


def test_get_local_users():
    result = get_local_users()

    assert isinstance(result, list)

    for user in result:
        assert isinstance(user, str)
        assert user.strip() != ""


def test_get_disabled_users():
    result = get_disabled_users()

    assert isinstance(result, list)

    for user in result:
        assert isinstance(user, str)
        assert user.strip() != ""


def test_get_firewall_status():
    result = get_firewall_status()

    assert isinstance(result, dict)

    for profile, enabled in result.items():
        assert isinstance(profile, str)
        assert isinstance(enabled, bool)


def test_get_antivirus_status():
    result = get_antivirus_status()

    assert isinstance(result, list)

    for antivirus in result:
        assert isinstance(antivirus, dict)
        assert "name" in antivirus
        assert "state" in antivirus
        assert isinstance(antivirus["name"], str)


def test_get_windows_updates():
    result = get_windows_updates()

    assert isinstance(result, list)

    for update in result:
        assert isinstance(update, dict)
        assert "id" in update
        assert "description" in update
        assert "installed_on" in update
        assert isinstance(update["id"], str)


def test_get_password_policy():
    result = get_password_policy()

    assert isinstance(result, dict)


def test_get_logged_in_users():
    result = get_logged_in_users()

    assert isinstance(result, list)

    for user in result:
        assert isinstance(user, str)
        assert user.strip() != ""


def test_get_bitlocker_status():
    result = get_bitlocker_status()

    assert isinstance(result, list)

    for volume in result:
        assert isinstance(volume, dict)
        assert "mount_point" in volume
        assert "volume_status" in volume
        assert "protection_status" in volume
        assert "encryption_percentage" in volume

        assert isinstance(volume["mount_point"], str)
        assert isinstance(volume["encryption_percentage"], (int, float))


def test_get_password_never_expires_users():
    result = get_password_never_expires_users()

    assert isinstance(result, list)

    for user in result:
        assert isinstance(user, str)
        assert user.strip() != ""


def test_get_uac_status():
    result = get_uac_status()

    assert isinstance(result, bool)
