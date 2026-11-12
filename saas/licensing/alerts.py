"""Alertes e-mail envoyées au propriétaire de la licence après un audit."""

import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import AuditReport

logger = logging.getLogger(__name__)

# Baisse de score (en points) à partir de laquelle une alerte est envoyée.
SCORE_DROP_THRESHOLD = 10


def device_label(device):
    """Nom lisible d'un appareil sans exposer l'identifiant complet."""
    computer = getattr(device, "managed_computer", None)
    if computer is not None:
        return f"{computer.asset_tag} — {computer.name}"
    return f"Appareil ••••{device.device_id[-4:]}"


def _critical_count(report):
    summary = report.summary if isinstance(report.summary, dict) else {}
    try:
        return int(summary.get("critical", 0))
    except (TypeError, ValueError):
        return 0


def build_alert_reasons(report):
    """Liste des motifs d'alerte pour ce rapport (vide = aucune alerte)."""
    previous = (
        AuditReport.objects.filter(device=report.device)
        .exclude(pk=report.pk)
        .order_by("-created_at")
        .first()
    )
    reasons = []

    if previous is not None and previous.score - report.score >= SCORE_DROP_THRESHOLD:
        reasons.append(
            f"Le score est passé de {previous.score} à {report.score} "
            f"(baisse de {previous.score - report.score} points)."
        )

    critical = _critical_count(report)
    previous_critical = _critical_count(previous) if previous is not None else 0
    if critical > 0 and previous_critical == 0:
        reasons.append(f"{critical} problème(s) critique(s) détecté(s) pour la première fois.")

    return reasons


def notify_audit_alerts(report):
    """Envoie un e-mail au propriétaire de la licence si le rapport mérite une alerte.

    Retourne True si un e-mail a été envoyé. Ne lève jamais d'exception.
    """
    try:
        reasons = build_alert_reasons(report)
        if not reasons:
            return False

        owner = report.device.license.user
        if not owner.email:
            return False

        label = device_label(report.device)
        body = (
            f"Bonjour,\n\n"
            f"Le dernier audit de « {label} » appelle votre attention :\n\n"
            + "\n".join(f"- {reason}" for reason in reasons)
            + "\n\nConnectez-vous à SystAudit pour consulter le rapport et les actions proposées.\n"
            "Ce message est automatique.\n"
        )
        send_mail(
            subject=f"[SystAudit] Alerte de sécurité — {label}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner.email],
            fail_silently=False,
        )
        return True
    except Exception:  # une alerte ne doit jamais empêcher l'enregistrement du rapport
        logger.exception("Envoi de l'alerte d'audit impossible")
        return False
