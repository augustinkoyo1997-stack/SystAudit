from src.security_analysis import analyze_security


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