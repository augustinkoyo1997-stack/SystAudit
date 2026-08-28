from src.license_guard import check_license


def test_check_license_valid(monkeypatch):
    def fake_validate_license(key):
        return {
            "valid": True,
            "license": key,
            "plan": "premium",
            "max_devices": 2,
            "expires_at": None,
        }

    monkeypatch.setattr(
        "src.license_guard.validate_license",
        fake_validate_license,
    )

    result = check_license("TEST-LICENSE")

    assert result["allowed"] is True
    assert result["license"] == "TEST-LICENSE"
    assert result["plan"] == "premium"
    assert result["max_devices"] == 2


def test_check_license_invalid(monkeypatch):
    def fake_validate_license(key):
        return {
            "valid": False,
            "error": "Invalid license.",
        }

    monkeypatch.setattr(
        "src.license_guard.validate_license",
        fake_validate_license,
    )

    result = check_license("INVALID-LICENSE")

    assert result["allowed"] is False
    assert result["reason"] == "Invalid license."


def test_check_license_expired_or_inactive(monkeypatch):
    def fake_validate_license(key):
        return {
            "valid": False,
            "error": "License expired.",
        }

    monkeypatch.setattr(
        "src.license_guard.validate_license",
        fake_validate_license,
    )

    result = check_license("EXPIRED-LICENSE")

    assert result["allowed"] is False
    assert result["reason"] == "License expired."


def test_check_license_activates_device(monkeypatch):
    def fake_validate_license(key):
        return {
            "valid": True,
            "license": key,
            "plan": "premium",
            "max_devices": 2,
            "expires_at": None,
        }

    def fake_activate_device(key, device_id):
        assert key == "TEST-LICENSE"
        assert device_id == "DEVICE-123"

        return {
            "activated": True,
            "device_id": device_id,
            "devices_used": 1,
            "max_devices": 2,
        }

    monkeypatch.setattr(
        "src.license_guard.validate_license",
        fake_validate_license,
    )
    monkeypatch.setattr(
        "src.license_guard.activate_device",
        fake_activate_device,
    )

    result = check_license(
        "TEST-LICENSE",
        activate=True,
        device_id="DEVICE-123",
    )

    assert result["allowed"] is True
    assert result["device_id"] == "DEVICE-123"
    assert result["devices_used"] == 1
    assert result["max_devices"] == 2


def test_check_license_activation_failure(monkeypatch):
    def fake_validate_license(key):
        return {
            "valid": True,
            "license": key,
            "plan": "free",
            "max_devices": 1,
            "expires_at": None,
        }

    def fake_activate_device(key, device_id):
        return {
            "activated": False,
            "error": "Maximum number of devices reached.",
            "devices_used": 1,
            "max_devices": 1,
        }

    monkeypatch.setattr(
        "src.license_guard.validate_license",
        fake_validate_license,
    )
    monkeypatch.setattr(
        "src.license_guard.activate_device",
        fake_activate_device,
    )

    result = check_license(
        "TEST-LICENSE",
        activate=True,
        device_id="DEVICE-456",
    )

    assert result["allowed"] is False
    assert result["reason"] == "Maximum number of devices reached."
    assert result["devices_used"] == 1
    assert result["max_devices"] == 1