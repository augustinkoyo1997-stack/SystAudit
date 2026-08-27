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
