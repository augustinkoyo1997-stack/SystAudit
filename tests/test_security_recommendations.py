from src.security_recommendations import generate_recommendations


def test_generate_recommendations_high():
    findings = [
        {
            "risk": "high",
            "reason": "Firewall disabled",
        }
    ]

    result = generate_recommendations(findings)

    assert isinstance(result, list)
    assert len(result) == 1

    recommendation = result[0]

    assert recommendation["risk"] == "high"
    assert recommendation["reason"] == "Firewall disabled"
    assert "recommendation" in recommendation
    assert isinstance(recommendation["recommendation"], str)
    assert recommendation["recommendation"].strip() != ""


def test_generate_recommendations_medium():
    findings = [
        {
            "risk": "medium",
            "reason": "Password never expires",
        }
    ]

    result = generate_recommendations(findings)

    assert len(result) == 1
    assert result[0]["risk"] == "medium"
    assert result[0]["reason"] == "Password never expires"


def test_generate_recommendations_low():
    findings = [
        {
            "risk": "low",
            "reason": "Review firewall rules",
        }
    ]

    result = generate_recommendations(findings)

    assert len(result) == 1
    assert result[0]["risk"] == "low"
    assert result[0]["reason"] == "Review firewall rules"


def test_generate_recommendations_multiple():
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

    result = generate_recommendations(findings)

    assert isinstance(result, list)
    assert len(result) == 3

    assert result[0]["risk"] == "high"
    assert result[1]["risk"] == "medium"
    assert result[2]["risk"] == "low"


def test_generate_recommendations_empty():
    result = generate_recommendations([])

    assert isinstance(result, list)
    assert result == []
    