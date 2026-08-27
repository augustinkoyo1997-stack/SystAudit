from src.security_analysis import (
    analyze_security,
    calculate_security_score,
)


def test_analyze_security():
    result = analyze_security()

    assert isinstance(result, list)

    for finding in result:
        assert isinstance(finding, dict)

        assert "risk" in finding
        assert "category" in finding
        assert "message" in finding

        assert finding["risk"] in {"low", "medium", "high"}

        assert isinstance(finding["category"], str)
        assert isinstance(finding["message"], str)

        assert finding["category"].strip() != ""
        assert finding["message"].strip() != ""


def test_calculate_security_score():
    assert calculate_security_score([]) == 100

    assert calculate_security_score([
        {"risk": "high"}
    ]) == 75

    assert calculate_security_score([
        {"risk": "medium"}
    ]) == 90

    assert calculate_security_score([
        {"risk": "low"}
    ]) == 95


def test_calculate_security_score_multiple_findings():
    findings = [
        {"risk": "high"},
        {"risk": "medium"},
        {"risk": "low"},
    ]

    assert calculate_security_score(findings) == 60


def test_calculate_security_score_never_negative():
    findings = [
        {"risk": "high"},
        {"risk": "high"},
        {"risk": "high"},
        {"risk": "high"},
        {"risk": "high"},
    ]

    assert calculate_security_score(findings) == 0
