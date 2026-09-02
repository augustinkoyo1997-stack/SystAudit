from .system import get_system_info
from .network import get_network_info, get_suspicious_ports
from .security import (
    get_firewall_status,
    get_antivirus_status,
    get_uac_status,
    get_bitlocker_status,
    get_password_never_expires_users,
    get_suspicious_services,
    get_suspicious_scheduled_tasks,
    get_suspicious_processes,
    get_suspicious_events,
)


def _finding(title, severity, description):
    """Build a standardized audit finding."""
    return {
        "title": title,
        "severity": severity,
        "description": description,
    }


def _evaluate_firewall():
    """Evaluate Windows Firewall configuration."""
    firewall = get_firewall_status()

    if not firewall:
        return _finding(
            "Firewall non vérifiable",
            "MEDIUM",
            "Impossible de vérifier l'état du pare-feu Windows.",
        )

    disabled_profiles = [
        profile
        for profile, enabled in firewall.items()
        if not enabled
    ]

    if disabled_profiles:
        return _finding(
            "Pare-feu désactivé",
            "HIGH",
            f"Le pare-feu est désactivé pour : "
            f"{', '.join(disabled_profiles)}.",
        )

    return None


def _evaluate_antivirus():
    """Evaluate antivirus protection."""
    antivirus = get_antivirus_status()

    if not antivirus:
        return _finding(
            "Antivirus non détecté",
            "HIGH",
            "Aucun antivirus actif n'a été détecté.",
        )

    active_antivirus = []

    for item in antivirus:
        state = str(item.get("state", "")).lower()

        if state in {"on", "enabled", "active", "running"}:
            active_antivirus.append(item)

    if not active_antivirus:
        return _finding(
            "Antivirus inactif",
            "HIGH",
            "Un antivirus est présent mais aucun état actif "
            "n'a été détecté.",
        )

    return None


def _evaluate_uac():
    """Evaluate User Account Control."""
    uac_enabled = get_uac_status()

    if not uac_enabled:
        return _finding(
            "UAC désactivé",
            "HIGH",
            "Le contrôle de compte utilisateur (UAC) est désactivé.",
        )

    return None


def _evaluate_bitlocker():
    """Evaluate BitLocker protection."""
    bitlocker = get_bitlocker_status()

    if not bitlocker:
        return _finding(
            "BitLocker non détecté",
            "MEDIUM",
            "Aucune information BitLocker exploitable n'a été détectée.",
        )

    unprotected = []

    for volume in bitlocker:
        protection = str(
            volume.get("protection_status", "")
        ).lower()

        if protection not in {"on", "protected", "1"}:
            unprotected.append(volume.get("mount_point", "volume inconnu"))

    if unprotected:
        return _finding(
            "Volumes non protégés par BitLocker",
            "MEDIUM",
            "Certains volumes ne semblent pas bénéficier "
            "d'une protection BitLocker active.",
        )

    return None


def _evaluate_password_expiration():
    """Evaluate accounts whose passwords never expire."""
    users = get_password_never_expires_users()

    if users:
        return _finding(
            "Mots de passe sans expiration",
            "MEDIUM",
            f"{len(users)} compte(s) local(aux) ont un mot de passe "
            "configuré sans expiration.",
        )

    return None


def _evaluate_suspicious_services():
    """Evaluate suspicious Windows services."""
    services = get_suspicious_services()

    if services:
        return _finding(
            "Services suspects détectés",
            "HIGH",
            f"{len(services)} service(s) présentent "
            "des caractéristiques nécessitant une vérification.",
        )

    return None


def _evaluate_suspicious_tasks():
    """Evaluate suspicious scheduled tasks."""
    tasks = get_suspicious_scheduled_tasks()

    if tasks:
        return _finding(
            "Tâches planifiées suspectes",
            "HIGH",
            f"{len(tasks)} tâche(s) planifiée(s) présentent "
            "des caractéristiques suspectes.",
        )

    return None


def _evaluate_suspicious_processes():
    """Evaluate suspicious processes."""
    processes = get_suspicious_processes()

    if processes:
        return _finding(
            "Processus suspects détectés",
            "HIGH",
            f"{len(processes)} processus présentent "
            "des caractéristiques nécessitant une vérification.",
        )

    return None


def _evaluate_suspicious_ports():
    """Evaluate sensitive listening ports."""
    ports = get_suspicious_ports()

    if ports:
        port_list = ", ".join(
            str(item["port"])
            for item in ports
        )

        return _finding(
            "Ports sensibles exposés",
            "MEDIUM",
            f"Des ports sensibles sont actuellement en écoute : "
            f"{port_list}.",
        )

    return None


def _evaluate_security_events():
    """Evaluate suspicious Windows security events."""
    events = get_suspicious_events()

    if events:
        return _finding(
            "Événements de sécurité suspects",
            "MEDIUM",
            f"{len(events)} événement(s) de sécurité "
            "nécessitent une analyse.",
        )

    return None


def calculate_score(findings, total_checks):
    """Calculate a security score from audit findings."""
    if total_checks <= 0:
        return 0

    penalties = {
        "HIGH": 15,
        "MEDIUM": 8,
        "LOW": 3,
    }

    score = 100

    for finding in findings:
        severity = finding.get("severity", "LOW")
        score -= penalties.get(severity, 0)

    return max(0, min(100, score))


def build_summary(findings, total_checks):
    """Build the audit summary expected by the SaaS dashboard."""
    critical = sum(
        1 for finding in findings
        if finding.get("severity") == "HIGH"
    )

    warnings = sum(
        1 for finding in findings
        if finding.get("severity") in {"MEDIUM", "LOW"}
    )

    passed = max(
        0,
        total_checks - len(findings),
    )

    return {
        "total_checks": total_checks,
        "passed": passed,
        "warnings": warnings,
        "critical": critical,
    }


def build_recommendations(findings):
    """Generate recommendations from detected findings."""
    recommendations = []

    recommendation_map = {
        "Pare-feu désactivé":
            "Activer le pare-feu Windows sur tous les profils réseau.",
        "Antivirus non détecté":
            "Installer et maintenir un antivirus reconnu et à jour.",
        "Antivirus inactif":
            "Vérifier et réactiver la protection antivirus.",
        "UAC désactivé":
            "Réactiver le contrôle de compte utilisateur (UAC).",
        "Volumes non protégés par BitLocker":
            "Activer BitLocker sur les volumes contenant des données sensibles.",
        "Mots de passe sans expiration":
            "Revoir la politique d'expiration des mots de passe des comptes locaux.",
        "Services suspects détectés":
            "Analyser les services suspects et vérifier leurs exécutables.",
        "Tâches planifiées suspectes":
            "Analyser les tâches planifiées suspectes et leurs actions.",
        "Processus suspects détectés":
            "Analyser les processus suspects et leur origine.",
        "Ports sensibles exposés":
            "Fermer ou restreindre les ports sensibles qui ne sont pas nécessaires.",
        "Événements de sécurité suspects":
            "Analyser les événements de sécurité détectés dans les journaux Windows.",
    }

    for finding in findings:
        title = finding.get("title")

        recommendation = recommendation_map.get(title)

        if recommendation and recommendation not in recommendations:
            recommendations.append(recommendation)

    return recommendations


def run_audit():
    """
    Run a complete local security audit.

    Returns a report compatible with the SaaS AuditReport API.
    """
    system_info = get_system_info()
    network_info = get_network_info()

    checks = [
        _evaluate_firewall,
        _evaluate_antivirus,
        _evaluate_uac,
        _evaluate_bitlocker,
        _evaluate_password_expiration,
        _evaluate_suspicious_services,
        _evaluate_suspicious_tasks,
        _evaluate_suspicious_processes,
        _evaluate_suspicious_ports,
        _evaluate_security_events,
    ]

    findings = []

    for check in checks:
        finding = check()

        if finding:
            findings.append(finding)

    total_checks = len(checks)

    score = calculate_score(
        findings,
        total_checks,
    )

    summary = build_summary(
        findings,
        total_checks,
    )

    recommendations = build_recommendations(
        findings,
    )

    return {
        "score": score,
        "summary": summary,
        "findings": findings,
        "recommendations": recommendations,
        "system": system_info,
        "network": network_info,
    }


if __name__ == "__main__":
    import pprint

    pprint.pp(run_audit())