"""Short-lived, token-authenticated endpoints for future WinPE deployment clients."""

import hashlib
import json
import re

from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from accounts.models import DeploymentRun


MAX_REQUEST_BYTES = 8192


def _json_body(request):
    if len(request.body) > MAX_REQUEST_BYTES:
        return None
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _run_for_token(token):
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32,80}", token):
        return None
    digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    return DeploymentRun.objects.select_related("batch__profile").filter(token_hash=digest).first()


def _bearer_token(request):
    value = request.headers.get("Authorization", "")
    scheme, _, token = value.partition(" ")
    return token.strip() if scheme.casefold() == "bearer" else ""


def _expired(run):
    return run.expires_at <= timezone.now()


@csrf_exempt
def deployment_claim(request):
    """Enroll a WinPE session and wait for an operator to approve its selected disk."""
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)
    payload = _json_body(request)
    if payload is None:
        return JsonResponse({"error": "Corps JSON invalide ou trop volumineux."}, status=400)
    candidate = _run_for_token(payload.get("token"))
    if candidate is None:
        return JsonResponse({"error": "Code de connexion invalide."}, status=401)
    with transaction.atomic():
        run = DeploymentRun.objects.select_for_update().select_related("batch__profile").get(pk=candidate.pk)
        if _expired(run):
            return JsonResponse({"error": "Ce code temporaire a expiré."}, status=410)
        if run.status != DeploymentRun.STATUS_WAITING:
            return JsonResponse({"error": "Ce code a déjà été utilisé."}, status=409)
        machine_name = payload.get("machine_name")
        machine_model = payload.get("machine_model", "")
        target_disk = payload.get("target_disk")
        try:
            disk_size_gb = int(payload.get("target_disk_size_gb"))
        except (TypeError, ValueError):
            disk_size_gb = 0
        if (
            not isinstance(machine_name, str) or not machine_name.strip()
            or not isinstance(machine_model, str)
            or not isinstance(target_disk, str)
            or not re.fullmatch(r"[\w .:\\\\()\-]{1,120}", target_disk.strip(), re.UNICODE)
            or not 1 <= disk_size_gb <= 100000
        ):
            return JsonResponse({"error": "Nom du poste, disque cible et capacité du disque requis."}, status=400)

        run.machine_name = machine_name.strip()[:100]
        run.machine_model = machine_model.strip()[:160]
        run.target_disk = target_disk.strip()[:120]
        run.target_disk_size_gb = disk_size_gb
        run.status = DeploymentRun.STATUS_CONFIRMATION
        run.current_step = "En attente de la confirmation du technicien"
        run.last_seen = timezone.now()
        run.save(update_fields=[
            "machine_name", "machine_model", "target_disk", "target_disk_size_gb",
            "status", "current_step", "last_seen",
        ])

    profile = run.batch.profile
    return JsonResponse({
        "run_id": run.pk,
        "status": run.status,
        "operator_confirmation_required": True,
        "profile": {
            "name": profile.name,
            "windows_iso": profile.windows_iso,
            "image_index": profile.image_index,
            "language": profile.language,
            "applications": profile.applications,
            "office_product_id": profile.office_product_id,
        },
        "message": "Attendre la confirmation du PC central avant toute modification du disque.",
    }, status=201)


@csrf_exempt
def deployment_poll(request):
    if request.method != "GET":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)
    run = _run_for_token(_bearer_token(request))
    if run is None:
        return JsonResponse({"error": "Code de connexion invalide."}, status=401)
    if _expired(run) and run.status not in {DeploymentRun.STATUS_COMPLETED, DeploymentRun.STATUS_FAILED}:
        return JsonResponse({"error": "Ce code temporaire a expiré."}, status=410)
    run.last_seen = timezone.now()
    run.save(update_fields=["last_seen"])
    return JsonResponse({
        "run_id": run.pk,
        "status": run.status,
        "operator_authorized": run.operator_confirmed_at is not None,
        "target_disk": run.target_disk,
        "target_disk_size_gb": run.target_disk_size_gb,
    })


@csrf_exempt
def deployment_progress(request):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)
    payload = _json_body(request)
    if payload is None:
        return JsonResponse({"error": "Corps JSON invalide ou trop volumineux."}, status=400)
    run = _run_for_token(_bearer_token(request))
    if run is None:
        return JsonResponse({"error": "Code de connexion invalide."}, status=401)
    if _expired(run):
        return JsonResponse({"error": "Ce code temporaire a expiré."}, status=410)
    if run.status in {DeploymentRun.STATUS_COMPLETED, DeploymentRun.STATUS_FAILED}:
        return JsonResponse({"error": "Cette opération est déjà terminée."}, status=409)

    status = payload.get("status", run.status)
    allowed = {
        DeploymentRun.STATUS_CONFIRMATION,
        DeploymentRun.STATUS_INSTALLING,
        DeploymentRun.STATUS_COMPLETED,
        DeploymentRun.STATUS_FAILED,
    }
    if not isinstance(status, str) or status not in allowed:
        return JsonResponse({"error": "État de déploiement invalide."}, status=400)
    if status in {DeploymentRun.STATUS_INSTALLING, DeploymentRun.STATUS_COMPLETED} and not run.operator_confirmed_at:
        return JsonResponse({"error": "Le PC central doit confirmer le disque avant de poursuivre."}, status=403)
    try:
        progress = int(payload.get("progress", run.progress))
    except (TypeError, ValueError):
        progress = -1
    current_step = payload.get("current_step", "")
    failure_summary = payload.get("failure_summary", "")
    if (
        not 0 <= progress <= 100
        or not isinstance(current_step, str)
        or not isinstance(failure_summary, str)
    ):
        return JsonResponse({"error": "Progression ou description invalide."}, status=400)

    run.status = status
    run.progress = progress
    run.current_step = current_step.strip()[:120]
    run.failure_summary = failure_summary.strip()[:240] if status == DeploymentRun.STATUS_FAILED else ""
    run.last_seen = timezone.now()
    if status in {DeploymentRun.STATUS_COMPLETED, DeploymentRun.STATUS_FAILED}:
        run.finished_at = run.last_seen
    run.save(update_fields=[
        "status", "progress", "current_step", "failure_summary", "last_seen", "finished_at",
    ])
    return JsonResponse({"run_id": run.pk, "status": run.status, "progress": run.progress})
