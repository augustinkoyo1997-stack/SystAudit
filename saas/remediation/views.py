from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import RemediationRequest

from src.remediation_factory import create_remediation_from_finding
from src.remediation_engine import RemediationEngine


@login_required
@require_POST
def approve_remediation_request(request, request_id):
    remediation_request = get_object_or_404(
        RemediationRequest,
        pk=request_id,
    )

    remediation_request.approve()

    return redirect("dashboard")

@login_required
@require_POST
def execute_remediation_request(request, request_id):
    remediation_request = get_object_or_404(
        RemediationRequest,
        pk=request_id,
    )

    # Une remédiation doit obligatoirement être approuvée
    # avant de pouvoir être exécutée.
    if remediation_request.status != RemediationRequest.APPROVED:
        return redirect("dashboard")

    try:
        # Reconstruire le finding à partir de la demande Django.
        category = (
            remediation_request.remediation_id
            .replace("REM-", "")
            .lower()
        )

        finding = {
            "risk": remediation_request.severity,
            "category": category,
            "message": remediation_request.description,
        }

        # Créer la remédiation contrôlée.
        remediation = create_remediation_from_finding(
            finding
        )

        # L'approbation Django doit être propagée
        # vers l'objet Remediation.
        remediation.approve()

        # Passage APPROVED -> EXECUTING
        remediation_request.start_execution()

        # Exécution contrôlée :
        # execute -> verify -> rollback si nécessaire.
        engine = RemediationEngine(remediation)
        result = engine.run()

        # Récupérer le message réel produit par le moteur.
        result_message = getattr(
            result,
            "message",
            "",
        )

        # Succès uniquement si l'exécution ET
        # la vérification ont réussi.
        if engine.state == RemediationEngine.VERIFIED:
            remediation_request.mark_success(
                result_message
                or "Remediation executed and verified successfully."
            )

        # Si la vérification échoue et que le rollback
        # réussit, on conserve la trace du rollback.
        elif engine.state == RemediationEngine.ROLLED_BACK:
            remediation_request.mark_failed(
                result_message
                or "Remediation verification failed and rollback was performed."
            )
            remediation_request.rollback()

        else:
            remediation_request.mark_failed(
                result_message
                or f"Remediation failed with engine state: {engine.state}"
            )

    except PermissionError as exc:
        if remediation_request.status == RemediationRequest.EXECUTING:
            remediation_request.mark_failed(
                str(exc) or "Administrator privileges are required."
            )

    except Exception as exc:
        if remediation_request.status == RemediationRequest.EXECUTING:
            remediation_request.mark_failed(
                str(exc) or "Unexpected remediation execution error."
            )

    return redirect("dashboard")

