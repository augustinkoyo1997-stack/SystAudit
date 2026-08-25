def generate_recommendations(findings):
    """
    Generate security recommendations from detected findings.
    """
    recommendations = []

    for finding in findings:
        risk = finding.get("risk", "low")
        reason = finding.get("reason", "")

        if risk == "high":
            recommendations.append({
                "risk": "high",
                "reason": reason,
                "recommendation": "Investigate and remediate this security issue immediately.",
            })

        elif risk == "medium":
            recommendations.append({
                "risk": "medium",
                "reason": reason,
                "recommendation": "Review this security issue and apply appropriate corrective measures.",
            })

        elif risk == "low":
            recommendations.append({
                "risk": "low",
                "reason": reason,
                "recommendation": "Review this finding during the next security audit.",
            })

    return recommendations
