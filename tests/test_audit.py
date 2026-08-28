from src.audit import run_protected_audit, run_security_audit


def test_run_security_audit():
    result = run_security_audit()

    assert isinstance(result, dict)

    assert "score" in result
    assert "summary" in result
    assert "findings" in result
    assert "recommendations" in result

    assert isinstance(result["score"], (int, float))
    assert 0 <= result["score"] <= 100

    assert isinstance(result["summary"], dict)
    assert isinstance(result["findings"], list)
    assert isinstance(result["recommendations"], list)


def test_run_security_audit_score_range():
    result = run_security_audit()

    assert 0 <= result["score"] <= 100


def test_run_security_audit_report_structure():
    result = run_security_audit()

    summary = result["summary"]

    assert "total_findings" in summary
    assert "high" in summary
    assert "medium" in summary
    assert "low" in summary

    assert isinstance(summary["total_findings"], int)
    assert isinstance(summary["high"], int)
    assert isinstance(summary["medium"], int)
    assert isinstance(summary["low"], int)


def test_run_security_audit_findings_and_recommendations():
    result = run_security_audit()

    assert isinstance(result["findings"], list)
    assert isinstance(result["recommendations"], list)

    for finding in result["findings"]:
        assert isinstance(finding, dict)

    for recommendation in result["recommendations"]:
        assert isinstance(recommendation, dict)


def test_run_protected_audit_allows_valid_license(monkeypatch, tmp_path):
    fake_report = {
        "score": 90,
        "summary": {
            "total_findings": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        },
        "findings": [],
        "recommendations": [],
    }

    def fake_check_license(key, activate=False, device_id=None):
        assert key == "TEST-LICENSE"
        assert activate is True

        return {
            "allowed": True,
            "license": key,
            "plan": "premium",
            "max_devices": 2,
            "expires_at": None,
            "device_id": "DEVICE-123",
            "devices_used": 1,
        }

    monkeypatch.setattr(
        "src.audit.check_license",
        fake_check_license,
    )
    monkeypatch.setattr(
        "src.audit.run_security_audit",
        lambda: fake_report,
    )

    output_file = tmp_path / "report.json"

    result = run_protected_audit(
        "TEST-LICENSE",
        output_file=str(output_file),
    )

    assert result == fake_report
    assert output_file.exists()


def test_run_protected_audit_blocks_invalid_license(monkeypatch, tmp_path):
    def fake_check_license(key, activate=False, device_id=None):
        assert activate is True

        return {
            "allowed": False,
            "reason": "Invalid license.",
        }

    def fail_audit():
        raise AssertionError("Audit must not run.")

    monkeypatch.setattr(
        "src.audit.check_license",
        fake_check_license,
    )
    monkeypatch.setattr(
        "src.audit.run_security_audit",
        fail_audit,
    )

    output_file = tmp_path / "report.json"

    result = run_protected_audit(
        "INVALID-LICENSE",
        output_file=str(output_file),
    )

    assert result is None
    assert not output_file.exists()


def test_run_protected_audit_blocks_device_limit(monkeypatch, tmp_path):
    def fake_check_license(key, activate=False, device_id=None):
        assert activate is True

        return {
            "allowed": False,
            "reason": "Maximum number of devices reached.",
            "devices_used": 1,
            "max_devices": 1,
        }

    def fail_audit():
        raise AssertionError("Audit must not run.")

    monkeypatch.setattr(
        "src.audit.check_license",
        fake_check_license,
    )
    monkeypatch.setattr(
        "src.audit.run_security_audit",
        fail_audit,
    )

    output_file = tmp_path / "report.json"

    result = run_protected_audit(
        "TEST-LICENSE",
        output_file=str(output_file),
    )

    assert result is None
    assert not output_file.exists()


def test_run_protected_audit_submits_report(monkeypatch, tmp_path):
    fake_report = {
        "score": 90,
        "summary": {
            "total_findings": 1,
            "high": 0,
            "medium": 1,
            "low": 0,
        },
        "findings": [
            {
                "risk": "medium",
                "reason": "BitLocker disabled.",
            }
        ],
        "recommendations": [
            {
                "risk": "medium",
                "reason": "BitLocker disabled.",
                "recommendation": "Enable BitLocker.",
            }
        ],
    }

    def fake_check_license(key, activate=False, device_id=None):
        assert key == "TEST-LICENSE"
        assert activate is True

        return {
            "allowed": True,
            "license": key,
            "plan": "premium",
            "max_devices": 2,
            "expires_at": None,
            "device_id": "DEVICE-123",
            "devices_used": 1,
        }

    def fake_submit_audit_report(key, device_id, report):
        assert key == "TEST-LICENSE"
        assert device_id == "DEVICE-123"
        assert report == fake_report

        return {
            "saved": True,
            "report_id": 42,
            "device_id": "DEVICE-123",
            "score": 90,
        }

    monkeypatch.setattr(
        "src.audit.check_license",
        fake_check_license,
    )
    monkeypatch.setattr(
        "src.audit.run_security_audit",
        lambda: fake_report,
    )
    monkeypatch.setattr(
        "src.audit.submit_audit_report",
        fake_submit_audit_report,
    )

    output_file = tmp_path / "report.json"

    result = run_protected_audit(
        "TEST-LICENSE",
        output_file=str(output_file),
    )

    assert result == fake_report
    assert output_file.exists()


def test_run_protected_audit_keeps_local_report_when_submission_fails(
    monkeypatch,
    tmp_path,
):
    fake_report = {
        "score": 85,
        "summary": {
            "total_findings": 1,
            "high": 0,
            "medium": 1,
            "low": 0,
        },
        "findings": [],
        "recommendations": [],
    }

    def fake_check_license(key, activate=False, device_id=None):
        return {
            "allowed": True,
            "license": key,
            "plan": "free",
            "max_devices": 1,
            "expires_at": None,
            "device_id": "DEVICE-123",
            "devices_used": 1,
        }

    def fake_submit_audit_report(key, device_id, report):
        return {
            "saved": False,
            "error": "Unable to connect to the license server.",
        }

    monkeypatch.setattr(
        "src.audit.check_license",
        fake_check_license,
    )
    monkeypatch.setattr(
        "src.audit.run_security_audit",
        lambda: fake_report,
    )
    monkeypatch.setattr(
        "src.audit.submit_audit_report",
        fake_submit_audit_report,
    )

    output_file = tmp_path / "report.json"

    result = run_protected_audit(
        "TEST-LICENSE",
        output_file=str(output_file),
    )

    assert result == fake_report
    assert output_file.exists()