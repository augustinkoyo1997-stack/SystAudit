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


def _finding(title, severity, description, category):
    """Build a normalized audit finding."""

    severity = severity.upper()

    return {
        # Nouveau format canonique
        "risk": severity.lower(),
        "category": category,
        "message": description,
        # Compatibilité temporaire avec l'ancien code
        "title": title,
        "severity": severity,
        "description": description,
        "status": "failed",
    }


def _unknown_finding(category, message):
    return {
        "risk": "unknown",
        "severity": "UNKNOWN",
        "status": "unknown",
        "category": category,
        "title": "Vérification indisponible",
        "message": message,
        "description": message,
    }


def _evaluate_firewall():
    """Evaluate Windows Firewall configuration."""
    firewall = get_firewall_status()

    if not firewall:
        return _unknown_finding(
            "firewall",
            "Windows n’a pas fourni l’état des profils du pare-feu.",
        )

    disabled_profiles = [
        profile for profile, enabled in firewall.items() if not enabled
    ]

    if disabled_profiles:
        return _finding(
            "Pare-feu désactivé",
            "HIGH",
            f"Le pare-feu est désactivé pour : " f"{', '.join(disabled_profiles)}.",
            "firewall",
        )

    return None


def _evaluate_antivirus():
    """Evaluate antivirus protection."""
    antivirus = get_antivirus_status()

    if antivirus is None:
        return _unknown_finding(
            "antivirus",
            "Windows n’a pas permis de lire l’état de l’antivirus.",
        )

    if not antivirus:
        return _finding(
            "Antivirus non détecté",
            "HIGH",
            "Aucun antivirus actif n'a été détecté.",
            "antivirus",
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
            "Un antivirus est présent mais aucun état actif " "n'a été détecté.",
            "antivirus",
        )

    return None


def _evaluate_uac():
    """Evaluate User Account Control."""
    uac_enabled = get_uac_status()

    if uac_enabled is None:
        return _unknown_finding(
            "uac",
            "Windows n’a pas permis de lire la configuration UAC.",
        )

    if not uac_enabled:
        return _finding(
            "UAC désactivé",
            "HIGH",
            "Le contrôle de compte utilisateur (UAC) est désactivé.",
            "uac",
        )

    return None


def _evaluate_bitlocker():
    """Evaluate BitLocker protection."""
    bitlocker = get_bitlocker_status()

    if not bitlocker:
        return _unknown_finding(
            "bitlocker",
            "Windows n’a pas fourni d’état de chiffrement exploitable pour les volumes.",
        )
    unprotected = []

    for volume in bitlocker:
        protection = str(volume.get("protection_status", "")).lower()

        if protection not in {"on", "protected", "1"}:
            unprotected.append(volume.get("mount_point", "volume inconnu"))

    if unprotected:
        return _finding(
            "Volumes non protégés par BitLocker",
            "MEDIUM",
            "Certains volumes ne semblent pas bénéficier "
            "d'une protection BitLocker active.",
            "bitlocker",
        )

    return None


def _evaluate_password_expiration():
    """Evaluate accounts whose passwords never expire."""
    users = get_password_never_expires_users()

    if users is None:
        return _unknown_finding(
            "password_policy",
            "Windows n’a pas permis de lire la politique des comptes locaux.",
        )

    if users:
        return _finding(
            "Mots de passe sans expiration",
            "MEDIUM",
            f"{len(users)} compte(s) local(aux) ont un mot de passe "
            "configuré sans expiration.",
            "password_policy",
        )

    return None


def _evaluate_suspicious_services():
    """Evaluate suspicious Windows services."""
    services = get_suspicious_services()

    if services is None:
        return _unknown_finding(
            "suspicious_services",
            "Windows n’a pas fourni la liste des services à examiner.",
        )

    if services:
        return _finding(
            "Services suspects détectés",
            "HIGH",
            f"{len(services)} service(s) présentent "
            "des caractéristiques nécessitant une vérification.",
            "suspicious_services",
        )

    return None


def _evaluate_suspicious_tasks():
    """Evaluate suspicious scheduled tasks."""
    tasks = get_suspicious_scheduled_tasks()

    if tasks is None:
        return _unknown_finding(
            "suspicious_tasks",
            "Windows n’a pas fourni la liste des tâches planifiées à examiner.",
        )

    if tasks:
        return _finding(
            "Tâches planifiées suspectes",
            "HIGH",
            f"{len(tasks)} tâche(s) planifiée(s) présentent "
            "des caractéristiques suspectes.",
            "suspicious_tasks",
        )

    return None


def _evaluate_suspicious_processes():
    """Evaluate suspicious processes."""
    processes = get_suspicious_processes()

    if processes is None:
        return _unknown_finding(
            "suspicious_processes",
            "Windows n’a pas fourni les processus nécessaires à cette vérification.",
        )

    if processes:
        return _finding(
            "Processus suspects détectés",
            "HIGH",
            f"{len(processes)} processus présentent "
            "des caractéristiques nécessitant une vérification.",
            "suspicious_processes",
        )

    return None


def _evaluate_suspicious_ports():
    """Evaluate sensitive listening ports."""
    ports = get_suspicious_ports()

    if ports is None:
        return _unknown_finding(
            "suspicious_ports",
            "Windows n’a pas permis de lire les ports en écoute.",
        )

    if ports:
        port_list = ", ".join(str(item["port"]) for item in ports)

        return _finding(
            "Ports sensibles exposés",
            "MEDIUM",
            f"Des ports sensibles sont actuellement en écoute : " f"{port_list}.",
            "suspicious_ports",
        )

    return None


def _evaluate_security_events():
    """Evaluate suspicious Windows security events."""
    events = get_suspicious_events()

    if events is None:
        return _unknown_finding(
            "security_events",
            "Windows n’a pas permis de lire les événements de sécurité.",
        )

    if events:
        return _finding(
            "Événements de sécurité suspects",
            "MEDIUM",
            f"{len(events)} événement(s) de sécurité " "nécessitent une analyse.",
            "security_events",
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
    critical = sum(1 for finding in findings if finding.get("severity") == "HIGH")

    warnings = sum(
        1 for finding in findings if finding.get("severity") in {"MEDIUM", "LOW"}
    )

    unknown = sum(1 for finding in findings if finding.get("status") == "unknown")
    failed = len(findings) - unknown
    passed = max(0, total_checks - failed - unknown)

    return {
        "total_checks": total_checks,
        "passed": passed,
        "warnings": warnings,
        "critical": critical,
        "failed": failed,
        "unknown": unknown,
        "coverage_percent": round((total_checks - unknown) * 100 / total_checks) if total_checks else 0,
    }


def build_recommendations(findings):
    """Generate recommendations from detected findings."""
    recommendations = []

    recommendation_map = {
        "Pare-feu désactivé": "Activer le pare-feu Windows sur tous les profils réseau.",
        "Antivirus non détecté": "Installer et maintenir un antivirus reconnu et à jour.",
        "Antivirus inactif": "Vérifier et réactiver la protection antivirus.",
        "UAC désactivé": "Réactiver le contrôle de compte utilisateur (UAC).",
        "Volumes non protégés par BitLocker": "Activer BitLocker sur les volumes contenant des données sensibles.",
        "Mots de passe sans expiration": "Revoir la politique d'expiration des mots de passe des comptes locaux.",
        "Services suspects détectés": "Analyser les services suspects et vérifier leurs exécutables.",
        "Tâches planifiées suspectes": "Analyser les tâches planifiées suspectes et leurs actions.",
        "Processus suspects détectés": "Analyser les processus suspects et leur origine.",
        "Ports sensibles exposés": "Fermer ou restreindre les ports sensibles qui ne sont pas nécessaires.",
        "Événements de sécurité suspects": "Analyser les événements de sécurité détectés dans les journaux Windows.",
    }

    for finding in findings:
        if finding.get("status", "failed") == "unknown":
            continue
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
        ("firewall", "Pare-feu", _evaluate_firewall),
        ("antivirus", "Antivirus", _evaluate_antivirus),
        ("uac", "Contrôle UAC", _evaluate_uac),
        ("bitlocker", "Chiffrement BitLocker", _evaluate_bitlocker),
        ("password_policy", "Politique des comptes", _evaluate_password_expiration),
        ("suspicious_services", "Services Windows", _evaluate_suspicious_services),
        ("suspicious_tasks", "Tâches planifiées", _evaluate_suspicious_tasks),
        ("suspicious_processes", "Processus", _evaluate_suspicious_processes),
        ("suspicious_ports", "Ports réseau", _evaluate_suspicious_ports),
        ("security_events", "Événements de sécurité", _evaluate_security_events),
    ]

    findings = []
    check_results = []

    for check_id, label, check in checks:
        try:
            finding = check()
        except Exception:
            finding = _unknown_finding(
                check_id,
                "Le contrôle a échoué pendant la collecte; son résultat est inconnu.",
            )

        if finding:
            finding["check_id"] = check_id
            findings.append(finding)
            status = finding.get("status", "failed")
            check_results.append({
                "check_id": check_id,
                "label": label,
                "status": status,
                "message": finding.get("message", ""),
            })
        else:
            check_results.append({
                "check_id": check_id,
                "label": label,
                "status": "passed",
                "message": "Aucun problème détecté par ce contrôle.",
            })

    total_checks = len(checks)

    score = calculate_score(
        findings,
        total_checks,
    )

    summary = build_summary(
        findings,
        total_checks,
    )
    summary["check_results"] = check_results

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
