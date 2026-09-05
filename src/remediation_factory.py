from src.remediation import Remediation
from src.firewall_remediation import (
    enable_windows_firewall,
    verify_windows_firewall,
    disable_windows_firewall,
)


def create_remediation_from_finding(finding):
    """
    Create a controlled remediation proposal from a security finding.

    No system-changing action is executed at this stage.
    """

    risk = finding.get("risk", "low")
    category = finding.get("category", "unknown")
    message = finding.get(
        "message",
        finding.get("reason", "Security issue detected."),
    )

    requires_admin = category in {
        "firewall",
        "uac",
        "antivirus",
        "bitlocker",
        "password_policy",
        "service",
        "scheduled_task",
        "process",
    }

    reversible = category in {
        "firewall",
        "uac",
        "antivirus",
        "bitlocker",
        "password_policy",
        "service",
        "scheduled_task",
    }

    action = None
    verify_action = None
    rollback_action = None

    if category == "firewall":
        action = enable_windows_firewall
        verify_action = verify_windows_firewall
        rollback_action = disable_windows_firewall

    remediation_id = f"REM-{category.upper()}"

    return Remediation(
        id=remediation_id,
        title=f"Remediate {category}",
        description=message,
        severity=risk,
        category=category,
        action=action,
        rollback_action=rollback_action,
        verify_action=verify_action,
        requires_admin=requires_admin,
        reversible=reversible,
    )


def create_remediations_from_findings(findings):
    """
    Create controlled remediation proposals from multiple findings.

    No remediation action is executed.
    """

    return [
        create_remediation_from_finding(finding)
        for finding in findings
    ]