def generate_security_report(findings, recommendations, score):
    """
    Generate a structured security audit report.
    """

    high_risks = [
        finding for finding in findings
        if finding.get("risk") == "high"
    ]

    medium_risks = [
        finding for finding in findings
        if finding.get("risk") == "medium"
    ]

    low_risks = [
        finding for finding in findings
        if finding.get("risk") == "low"
    ]

    return {
        "score": score,
        "summary": {
            "total_findings": len(findings),
            "high": len(high_risks),
            "medium": len(medium_risks),
            "low": len(low_risks),
        },
        "findings": findings,
        "recommendations": recommendations,
    }
