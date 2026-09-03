import pytest

from src import audit_client


def test_submit_audit_report_requires_api_url():
    with pytest.raises(ValueError, match="api_url is required"):
        audit_client.submit_audit_report(
            api_url="",
            license_key="LICENSE-123",
            device_id="DEVICE-123",
        )


def test_submit_audit_report_requires_license_key():
    with pytest.raises(ValueError, match="license_key is required"):
        audit_client.submit_audit_report(
            api_url="http://example.com/api",
            license_key="",
            device_id="DEVICE-123",
        )


def test_submit_audit_report_requires_device_id():
    with pytest.raises(ValueError, match="device_id is required"):
        audit_client.submit_audit_report(
            api_url="http://example.com/api",
            license_key="LICENSE-123",
            device_id="",
        )


def test_submit_audit_report_sends_correct_payload(monkeypatch):
    audit_result = {
        "score": 85,
        "summary": {
            "passed": 8,
            "critical": 1,
            "warnings": 1,
            "total_checks": 10,
        },
        "findings": [
            {
                "severity": "HIGH",
                "title": "Service suspecte detecte",
            },
        ],
        "recommendations": [
            "Verifier les services suspects",
        ],
    }

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "saved": True,
                "report_id": 1,
            }

    captured = {}

    def fake_run_audit():
        return audit_result

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        audit_client,
        "run_audit",
        fake_run_audit,
    )

    monkeypatch.setattr(
        audit_client.requests,
        "post",
        fake_post,
    )

    result = audit_client.submit_audit_report(
        api_url="http://localhost/api/license/audit/report/",
        license_key="LICENSE-123",
        device_id="DEVICE-123",
        timeout=15,
    )

    assert captured["url"] == (
        "http://localhost/api/license/audit/report/"
    )

    assert captured["timeout"] == 15

    assert captured["json"] == {
        "key": "LICENSE-123",
        "device_id": "DEVICE-123",
        "score": 85,
        "summary": audit_result["summary"],
        "findings": audit_result["findings"],
        "recommendations": audit_result["recommendations"],
    }

    assert result == {
        "saved": True,
        "report_id": 1,
    }


def test_submit_audit_report_propagates_http_error(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            raise RuntimeError("HTTP error")

    monkeypatch.setattr(
        audit_client,
        "run_audit",
        lambda: {
            "score": 100,
            "summary": {},
            "findings": [],
            "recommendations": [],
        },
    )

    monkeypatch.setattr(
        audit_client.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(RuntimeError, match="HTTP error"):
        audit_client.submit_audit_report(
            api_url="http://localhost/api",
            license_key="LICENSE-123",
            device_id="DEVICE-123",
        )