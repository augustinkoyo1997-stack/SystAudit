from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from accounts.models import License
from .models import LicensedDevice


@api_view(["POST"])
def validate_license(request):
    key = request.data.get("key")

    if not key:
        return Response(
            {
                "valid": False,
                "error": "License key is required.",
            },
            status=400,
        )

    try:
        license_obj = License.objects.select_related("user").get(key=key)
    except License.DoesNotExist:
        return Response(
            {
                "valid": False,
                "error": "Invalid license.",
            },
            status=404,
        )
    except (ValidationError, ValueError):
        return Response(
            {
                "valid": False,
                "error": "Invalid license format.",
            },
            status=400,
        )

    if not license_obj.is_active:
        return Response(
            {
                "valid": False,
                "error": "License is inactive.",
            },
            status=403,
        )

    if (
        license_obj.expires_at is not None
        and license_obj.expires_at <= timezone.now()
    ):
        return Response(
            {
                "valid": False,
                "error": "License expired.",
            },
            status=403,
        )

    return Response(
        {
            "valid": True,
            "license": str(license_obj.key),
            "plan": license_obj.plan,
            "max_devices": license_obj.max_devices,
            "expires_at": license_obj.expires_at,
        }
    )


@api_view(["POST"])
def activate_device(request):
    key = request.data.get("key")
    device_id = request.data.get("device_id")

    if not key:
        return Response(
            {
                "activated": False,
                "error": "License key is required.",
            },
            status=400,
        )

    if not device_id:
        return Response(
            {
                "activated": False,
                "error": "Device ID is required.",
            },
            status=400,
        )

    try:
        license_obj = License.objects.get(key=key)
    except License.DoesNotExist:
        return Response(
            {
                "activated": False,
                "error": "Invalid license.",
            },
            status=404,
        )
    except (ValidationError, ValueError):
        return Response(
            {
                "activated": False,
                "error": "Invalid license format.",
            },
            status=400,
        )

    if not license_obj.is_active:
        return Response(
            {
                "activated": False,
                "error": "License is inactive.",
            },
            status=403,
        )

    if (
        license_obj.expires_at is not None
        and license_obj.expires_at <= timezone.now()
    ):
        return Response(
            {
                "activated": False,
                "error": "License expired.",
            },
            status=403,
        )

    existing_device = LicensedDevice.objects.filter(
        license=license_obj,
        device_id=device_id,
    ).first()

    if existing_device:
        existing_device.save(update_fields=["last_seen_at"])

        return Response(
            {
                "activated": True,
                "message": "Device already activated.",
                "device_id": device_id,
                "devices_used": license_obj.devices.count(),
                "max_devices": license_obj.max_devices,
            }
        )

    devices_used = license_obj.devices.count()

    if devices_used >= license_obj.max_devices:
        return Response(
            {
                "activated": False,
                "error": "Maximum number of devices reached.",
                "devices_used": devices_used,
                "max_devices": license_obj.max_devices,
            },
            status=409,
        )

    device = LicensedDevice.objects.create(
        license=license_obj,
        device_id=device_id,
    )

    return Response(
        {
            "activated": True,
            "message": "Device activated successfully.",
            "device_id": device.device_id,
            "devices_used": license_obj.devices.count(),
            "max_devices": license_obj.max_devices,
        },
        status=201,
    )