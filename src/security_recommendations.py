def generate_recommendations(findings):
    """
    Generate security recommendations from detected findings.
    """

    recommendations = []

    for finding in findings:
        risk = finding.get("risk", "low")
        category = finding.get("category", "unknown")
        message = finding.get(
            "message",
            finding.get("reason", "Security issue detected."),
        )

        recommendation = _get_recommendation(category, message, risk)

        recommendations.append(
            {
                "risk": risk,
                "category": category,
                "reason": message,
                "recommendation": recommendation,
            }
        )

    return recommendations


def _get_recommendation(category, message, risk):
    """
    Return a recommendation adapted to the finding category.
    """

    recommendations = {
        "firewall": (
            "Enable Windows Firewall on all network profiles "
            "and verify that required firewall rules remain functional."
        ),

        "uac": (
            "Enable User Account Control (UAC) to reduce the risk "
            "of unauthorized privilege escalation."
        ),

        "antivirus": (
            "Install or enable a trusted antivirus/endpoint protection "
            "solution and verify that its protection is active."
        ),

        "bitlocker": (
            "Enable BitLocker protection on unprotected volumes "
            "and verify that recovery keys are securely stored."
        ),

        "password_policy": (
            "Review the affected account and disable the "
            "'password never expires' setting unless there is "
            "a documented business requirement."
        ),

        "service": (
            "Verify whether the service is required. "
            "If it is legitimate, investigate its configuration "
            "and ensure its executable path and startup configuration "
            "are secure."
        ),

        "scheduled_task": (
            "Verify the scheduled task, its executable path, "
            "execution account and trigger. Disable or remove it "
            "if it is not legitimate."
        ),

        "process": (
            "Investigate the process, verify its executable path, "
            "parent process and associated account. "
            "Terminate or isolate it only if it is confirmed malicious."
        ),
    }

    recommendation = recommendations.get(category)

    if recommendation:
        return recommendation

    if risk == "high":
        return (
            "Investigate and remediate this security issue immediately."
        )

    if risk == "medium":
        return (
            "Review this security issue and apply appropriate "
            "corrective measures."
        )

    return (
        "Review this finding during the next security audit."
    )