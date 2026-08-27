from src.security_report import generate_security_report


def test_generate_security_report():
    findings = [
        {
            "risk": "high",
            "reason": "Firewall disabled",
        }
    ]

    recommendations = [
        {
            "risk": "high",
            "reason": "Firewall disabled",
            "recommendation": "Enable firewall",
        }
    ]

    result = generate_security_report(
        findings,
        recommendations,
        75,
    )

    assert isinstance(result, dict)

    assert result["score"] == 75

    assert "summary" in result
    assert "findings" in result
    assert "recommendations" in result

    assert result["summary"]["total_findings"] == 1
    assert result["summary"]["high"] == 1
    assert result["summary"]["medium"] == 0
    assert result["summary"]["low"] == 0


def test_generate_security_report_multiple_risks():
    findings = [
        {
            "risk": "high",
            "reason": "Firewall disabled",
        },
        {
            "risk": "medium",
            "reason": "Weak password policy",
        },
        {
            "risk": "low",
            "reason": "Old update",
        },
    ]

    recommendations = [
        {
            "risk": "high",
            "reason": "Firewall disabled",
            "recommendation": "Enable firewall",
        },
        {
            "risk": "medium",
            "reason": "Weak password policy",
            "recommendation": "Strengthen password policy",
        },
        {
            "risk": "low",
            "reason": "Old update",
            "recommendation": "Review updates",
        },
    ]

    result = generate_security_report(
        findings,
        recommendations,
        70,
    )

    assert result["score"] == 70

    assert result["summary"]["total_findings"] == 3
    assert result["summary"]["high"] == 1
    assert result["summary"]["medium"] == 1
    assert result["summary"]["low"] == 1

    assert len(result["findings"]) == 3
    assert len(result["recommendations"]) == 3


def test_generate_security_report_empty():
    result = generate_security_report([], [], 100)

    assert isinstance(result, dict)

    assert result["score"] == 100

    assert result["summary"]["total_findings"] == 0
    assert result["summary"]["high"] == 0
    assert result["summary"]["medium"] == 0
    assert result["summary"]["low"] == 0

    assert result["findings"] == []
    assert result["recommendations"] == []
    