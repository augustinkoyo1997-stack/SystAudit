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
    get_firewall_rules,
    get_suspicious_services,
    get_suspicious_scheduled_tasks,
    get_suspicious_processes,
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


def test_get_firewall_rules():
    result = get_firewall_rules()

    assert isinstance(result, list)

    for rule in result:
        assert isinstance(rule, dict)
        assert "name" in rule
        assert "direction" in rule
        assert "action" in rule
        assert "enabled" in rule
        assert "profile" in rule

        assert isinstance(rule["name"], str)
        assert isinstance(rule["direction"], str)
        assert isinstance(rule["action"], str)
        assert isinstance(rule["enabled"], bool)
        assert isinstance(rule["profile"], str)


def test_get_suspicious_services():
    result = get_suspicious_services()

    assert isinstance(result, list)

    for service in result:
        assert isinstance(service, dict)

        assert "name" in service
        assert "display_name" in service
        assert "status" in service
        assert "start_type" in service
        assert "path" in service
        assert "reason" in service

        assert isinstance(service["name"], str)
        assert isinstance(service["display_name"], str)
        assert isinstance(service["status"], str)
        assert isinstance(service["start_type"], str)
        assert isinstance(service["path"], str)
        assert isinstance(service["reason"], str)



def test_get_suspicious_scheduled_tasks():
    result = get_suspicious_scheduled_tasks()

    assert isinstance(result, list)

    for task in result:
        assert isinstance(task, dict)

        assert "name" in task
        assert "path" in task
        assert "state" in task
        assert "action" in task
        assert "reason" in task

        assert isinstance(task["name"], str)
        assert isinstance(task["path"], str)
        assert isinstance(task["state"], str)
        assert isinstance(task["action"], str)
        assert isinstance(task["reason"], str)


def test_get_suspicious_processes():
    result = get_suspicious_processes()

    assert isinstance(result, list)

    for process in result:
        assert isinstance(process, dict)

        assert "pid" in process
        assert "name" in process
        assert "path" in process
        assert "command_line" in process
        assert "reason" in process

        assert isinstance(process["name"], str)
        assert isinstance(process["path"], str)
        assert isinstance(process["command_line"], str)
        assert isinstance(process["reason"], str)
