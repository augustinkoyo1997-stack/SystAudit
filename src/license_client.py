import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_URL = "http://127.0.0.1:8000/api/license/validate/"


def validate_license(key, api_url=DEFAULT_API_URL):
    """
    Validate a SystAudit license through the SaaS API.
    """

    payload = json.dumps({"key": key}).encode("utf-8")

    request = Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

            return {
                "valid": bool(data.get("valid", False)),
                "license": data.get("license"),
                "plan": data.get("plan"),
                "max_devices": data.get("max_devices"),
                "expires_at": data.get("expires_at"),
            }

    except HTTPError as error:
        try:
            data = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}

        return {
            "valid": False,
            "error": data.get("error", "Invalid license."),
        }

    except (URLError, TimeoutError):
        return {
            "valid": False,
            "error": "Unable to connect to the license server.",
        }
    