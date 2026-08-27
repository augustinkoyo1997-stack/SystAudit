from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view

from accounts.models import License


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
        license = License.objects.select_related("user").get(key=key)
    except License.DoesNotExist:
        return Response(
            {
                "valid": False,
                "error": "Invalid license.",
            },
            status=404,
        )

    if not license.is_active:
        return Response(
            {
                "valid": False,
                "error": "License is inactive.",
            },
            status=403,
        )

    return Response(
        {
            "valid": True,
            "license": str(license.key),
            "plan": license.plan,
            "max_devices": license.max_devices,
            "expires_at": license.expires_at,
        }
    )
