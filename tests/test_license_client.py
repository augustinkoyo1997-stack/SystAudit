import json
from urllib.error import HTTPError, URLError

from src.license_client import (
    get_device_id,
    submit_audit_report,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.payload

    def close(self):
        pass

def test_get_device_id(monkeypatch):
    monkeypatch.setattr(
        "src.license_client.uuid.getnode",
        lambda: 123456789,
    )

    assert get_device_id() == "123456789"


def test_submit_audit_report_success(monkeypatch):
    def fake_urlopen(request, timeout):
        assert request.full_url.endswith("/api/license/audit/report/")
        assert timeout == 5

        body = json.loads(request.data.decode("utf-8"))

        assert body["key"] == "TEST-LICENSE"
        assert body["device_id"] == "DEVICE-123"
        assert body["score"] == 90
        assert body["summary"]["medium"] == 1
        assert len(body["findings"]) == 1
        assert len(body["recommendations"]) == 1

        return FakeResponse(
            {
                "saved": True,
                "message": "Audit report saved successfully.",
                "report_id": 42,
                "device_id": "DEVICE-123",
                "score": 90,
                "created_at": "2026-08-28T22:00:00Z",
            }
        )

    monkeypatch.setattr(
        "src.license_client.urlopen",
        fake_urlopen,
    )

    report = {
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

    result = submit_audit_report(
        "TEST-LICENSE",
        "DEVICE-123",
        report,
    )

    assert result["saved"] is True
    assert result["report_id"] == 42
    assert result["device_id"] == "DEVICE-123"
    assert result["score"] == 90


def test_submit_audit_report_http_error(monkeypatch):
    def fake_urlopen(request, timeout):
        raise HTTPError(
            request.full_url,
            403,
            "Forbidden",
            {},
            FakeResponse(
                {
                    "saved": False,
                    "error": "Device is not authorized for this license.",
                }
            ),
        )

    monkeypatch.setattr(
        "src.license_client.urlopen",
        fake_urlopen,
    )

    result = submit_audit_report(
        "TEST-LICENSE",
        "DEVICE-123",
        {"score": 90},
    )

    assert result["saved"] is False
    assert (
        result["error"]
        == "Device is not authorized for this license."
    )


def test_submit_audit_report_connection_error(monkeypatch):
    def fake_urlopen(request, timeout):
        raise URLError("server unavailable")

    monkeypatch.setattr(
        "src.license_client.urlopen",
        fake_urlopen,
    )

    result = submit_audit_report(
        "TEST-LICENSE",
        "DEVICE-123",
        {"score": 90},
    )

    assert result["saved"] is False
    assert (
        result["error"]
        == "Unable to connect to the license server."
    )