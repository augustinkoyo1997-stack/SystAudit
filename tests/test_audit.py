from src.audit import run_security_audit


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
        