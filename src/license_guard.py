from src.license_client import activate_device, get_device_id, validate_license


def check_license(key, activate=False, device_id=None):
    """
    Check whether a SystAudit license is valid.

    Activation of the current device is optional so that license
    validation remains independently testable.
    """

    result = validate_license(key)

    if not result.get("valid", False):
        return {
            "allowed": False,
            "reason": result.get("error", "Invalid license."),
        }

    response = {
        "allowed": True,
        "license": result.get("license"),
        "plan": result.get("plan"),
        "max_devices": result.get("max_devices"),
        "expires_at": result.get("expires_at"),
    }

    if not activate:
        return response

    if device_id is None:
        device_id = get_device_id()

    activation = activate_device(
        key,
        device_id=device_id,
    )

    if not activation.get("activated", False):
        return {
            **response,
            "allowed": False,
            "reason": activation.get(
                "error",
                "Device activation failed.",
            ),
            "device_id": device_id,
            "devices_used": activation.get("devices_used"),
        }

    response.update(
        {
            "device_id": activation.get("device_id"),
            "devices_used": activation.get("devices_used"),
        }
    )

    return response