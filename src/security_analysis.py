from src.security import (
    get_firewall_status,
    get_uac_status,
    get_antivirus_status,
    get_bitlocker_status,
    get_password_never_expires_users,
    get_suspicious_services,
    get_suspicious_scheduled_tasks,
    get_suspicious_processes,
)


def analyze_security():
    """Analyze Windows security configuration and return security findings."""

    findings = []

    # Firewall
    firewall = get_firewall_status()

    if firewall and not all(firewall.values()):
        findings.append({
            "risk": "high",
            "category": "firewall",
            "message": "Windows Firewall is disabled on one or more profiles.",
        })

    # UAC
    if not get_uac_status():
        findings.append({
            "risk": "high",
            "category": "uac",
            "message": "User Account Control (UAC) is disabled.",
        })

    # Antivirus
    antivirus = get_antivirus_status()

    if not antivirus:
        findings.append({
            "risk": "high",
            "category": "antivirus",
            "message": "No antivirus product was detected.",
        })

    # BitLocker
    bitlocker = get_bitlocker_status()

    if bitlocker:
        unprotected = [
            volume
            for volume in bitlocker
            if volume.get("protection_status") != 1
        ]

        if unprotected:
            findings.append({
                "risk": "medium",
                "category": "bitlocker",
                "message": "One or more BitLocker volumes are not protected.",
            })

    # Passwords that never expire
    never_expires = get_password_never_expires_users()

    for username in never_expires:
        findings.append({
            "risk": "medium",
            "category": "password_policy",
            "message": f"User '{username}' has a password configured to never expire.",
        })

    # Suspicious services
    for service in get_suspicious_services():
        findings.append({
            "risk": "medium",
            "category": "service",
            "message": service.get("reason", "Suspicious Windows service detected."),
        })

    # Suspicious scheduled tasks
    for task in get_suspicious_scheduled_tasks():
        findings.append({
            "risk": "medium",
            "category": "scheduled_task",
            "message": task.get(
                "reason",
                "Suspicious scheduled task detected.",
            ),
        })

    # Suspicious processes
    for process in get_suspicious_processes():
        findings.append({
            "risk": process.get("risk", "medium"),
            "category": "process",
            "message": process.get(
                "reason",
                "Suspicious process detected.",
            ),
        })

    return findings