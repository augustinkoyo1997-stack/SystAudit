import json

from django.db import IntegrityError, transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response

from accounts.models import License
from licensing.models import LicensedDevice
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import Agent


@csrf_exempt
def agent_heartbeat(request):
    """
    Endpoint utilisé par un Agent SystAudit pour signaler
    qu'il est actif auprès du SaaS.
    """

    if request.method != "POST":
        return JsonResponse(
            {"error": "Méthode non autorisée."},
            status=405,
        )

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "JSON invalide."},
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {"error": "Le JSON doit être un objet."},
            status=400,
        )

    agent_id = data.get("agent_id")
    secret = data.get("secret")

    if not agent_id or not secret:
        return JsonResponse(
            {"error": "agent_id et secret sont requis."},
            status=400,
        )

    try:
        agent = Agent.objects.select_related(
        "device__license"
        ).get(agent_id=agent_id)
    except (Agent.DoesNotExist, ValidationError, ValueError):
        return JsonResponse(
            {"error": "Agent inconnu."},
            status=401,
        )

    if agent.status == Agent.REVOKED:
        return JsonResponse(
            {"error": "Agent révoqué."},
            status=403,
        )

    if not agent.check_secret(secret):
        return JsonResponse(
            {"error": "Authentification échouée."},
            status=401,
        )

    if not agent.device.license.is_valid:
        return JsonResponse(
            {"error": "Licence invalide."},
            status=403,
        )

    agent.status = Agent.ONLINE
    agent.last_seen = timezone.now()
    agent.save(update_fields=["status", "last_seen"])

    return JsonResponse(
        {
            "status": "ok",
            "agent_id": str(agent.agent_id),
            "device_id": agent.device.device_id,
            "agent_status": agent.status,
            "last_seen": agent.last_seen.isoformat(),
        }
    )

@api_view(["POST"])
def agent_register(request):
    key = request.data.get("key")
    device_id = request.data.get("device_id")

    if not key or not device_id:
        return Response(
            {
                "registered": False,
                "error": "License key and device ID are required.",
            },
            status=400,
        )

    try:
        license_obj = License.objects.get(key=key)
    except License.DoesNotExist:
        return Response(
            {"registered": False, "error": "Invalid license."},
            status=404,
        )
    except (ValidationError, ValueError):
        return Response(
            {
                "registered": False,
                "error": "Invalid license format.",
            },
            status=400,
        )

    if not license_obj.is_valid:
        return Response(
            {
                "registered": False,
                "error": "License is invalid.",
            },
            status=403,
        )

    try:
        device = LicensedDevice.objects.get(
            license=license_obj,
            device_id=device_id,
        )
    except LicensedDevice.DoesNotExist:
        return Response(
            {
                "registered": False,
                "error": "Device is not activated for this license.",
            },
            status=404,
        )

    secret = Agent.generate_secret()

    try:
        with transaction.atomic():
            if Agent.objects.filter(device=device).exists():
                return Response(
                    {
                        "registered": False,
                        "error": (
                            "Agent already registered. "
                            "The secret cannot be retrieved again."
                        ),
                    },
                    status=409,
                )

            agent = Agent(device=device)
            agent.set_secret(secret)
            agent.save()

    except IntegrityError:
        return Response(
            {
                "registered": False,
                "error": "Agent already registered.",
            },
            status=409,
        )

    return Response(
        {
            "registered": True,
            "agent_id": str(agent.agent_id),
            "device_id": device.device_id,
            "secret": secret,
            "message": "Store this secret securely. It will not be shown again.",
        },
        status=201,
    )
