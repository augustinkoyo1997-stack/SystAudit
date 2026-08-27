from src.license_client import validate_license


def check_license(key):
    """
    Check whether a SystAudit license is valid.
    """
    result = validate_license(key)

    if not result.get("valid", False):
        return {
            "allowed": False,
            "reason": result.get("error", "Invalid license."),
        }

    return {
        "allowed": True,
        "license": result.get("license"),
        "plan": result.get("plan"),
        "max_devices": result.get("max_devices"),
        "expires_at": result.get("expires_at"),
    }
