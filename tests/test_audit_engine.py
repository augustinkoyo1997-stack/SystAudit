from src import audit_engine


def test_calculate_score_without_findings():
    score = audit_engine.calculate_score([], 10)

    assert score == 100


def test_calculate_score_with_high_finding():
    findings = [
        {
            "title": "Test",
            "severity": "HIGH",
            "description": "Test finding",
        }
    ]

    score = audit_engine.calculate_score(findings, 10)

    assert score == 85


def test_build_summary():
    findings = [
        {
            "title": "Critical issue",
            "severity": "HIGH",
            "description": "Test",
        },
        {
            "title": "Warning issue",
            "severity": "MEDIUM",
            "description": "Test",
        },
    ]

    summary = audit_engine.build_summary(
        findings,
        10,
    )

    assert summary["total_checks"] == 10
    assert summary["passed"] == 8
    assert summary["warnings"] == 1
    assert summary["critical"] == 1


def test_build_recommendations():
    findings = [
        {
            "title": "UAC désactivé",
            "severity": "HIGH",
            "description": "Test",
        },
        {
            "title": "Ports sensibles exposés",
            "severity": "MEDIUM",
            "description": "Test",
        },
    ]

    recommendations = audit_engine.build_recommendations(
        findings
    )

    assert len(recommendations) == 2
    assert any("UAC" in item for item in recommendations)
    assert any("ports sensibles" in item for item in recommendations)


def test_run_audit(monkeypatch):
    monkeypatch.setattr(
        audit_engine,
        "get_system_info",
        lambda: {"hostname": "TEST-PC"},
    )

    monkeypatch.setattr(
        audit_engine,
        "get_network_info",
        lambda: {"ip_address": "192.168.1.10"},
    )

    monkeypatch.setattr(
        audit_engine,
        "get_firewall_status",
        lambda: {
            "Domain": True,
            "Private": True,
            "Public": True,
        },
    )

    monkeypatch.setattr(
        audit_engine,
        "get_antivirus_status",
        lambda: [
            {
                "name": "Test Antivirus",
                "state": "active",
            }
        ],
    )

    monkeypatch.setattr(
        audit_engine,
        "get_uac_status",
        lambda: True,
    )

    monkeypatch.setattr(
        audit_engine,
        "get_bitlocker_status",
        lambda: [
            {
                "mount_point": "C:",
                "protection_status": "protected",
            }
        ],
    )

    monkeypatch.setattr(
        audit_engine,
        "get_password_never_expires_users",
        lambda: [],
    )

    monkeypatch.setattr(
        audit_engine,
        "get_suspicious_services",
        lambda: [],
    )

    monkeypatch.setattr(
        audit_engine,
        "get_suspicious_scheduled_tasks",
        lambda: [],
    )

    monkeypatch.setattr(
        audit_engine,
        "get_suspicious_processes",
        lambda: [],
    )

    monkeypatch.setattr(
        audit_engine,
        "get_suspicious_ports",
        lambda: [],
    )

    monkeypatch.setattr(
        audit_engine,
        "get_suspicious_events",
        lambda: [],
    )

    report = audit_engine.run_audit()

    assert isinstance(report, dict)

    assert report["score"] == 100

    assert report["summary"]["total_checks"] == 10
    assert report["summary"]["passed"] == 10
    assert report["summary"]["warnings"] == 0
    assert report["summary"]["critical"] == 0

    assert report["findings"] == []
    assert report["recommendations"] == []

    assert report["system"]["hostname"] == "TEST-PC"
    assert report["network"]["ip_address"] == "192.168.1.10"