import json
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_BASE_URL = os.environ.get(
    "SYSAUDIT_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

DEFAULT_API_URL = (
    f"{DEFAULT_API_BASE_URL}/api/license/validate/"
)

DEFAULT_ACTIVATE_API_URL = (
    f"{DEFAULT_API_BASE_URL}/api/license/activate/"
)

DEFAULT_AUDIT_REPORT_API_URL = (
    f"{DEFAULT_API_BASE_URL}/api/license/audit/report/"
)


def get_device_id():
    """
    Return a stable device identifier based on the network node ID.
    """
    return str(uuid.getnode())


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


def activate_device(
    key,
    device_id=None,
    api_url=DEFAULT_ACTIVATE_API_URL,
):
    """
    Activate a device for a SystAudit license.
    """

    if device_id is None:
        device_id = get_device_id()

    payload = json.dumps(
        {
            "key": key,
            "device_id": device_id,
        }
    ).encode("utf-8")

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
                "activated": bool(data.get("activated", False)),
                "message": data.get("message"),
                "device_id": data.get("device_id"),
                "devices_used": data.get("devices_used"),
                "max_devices": data.get("max_devices"),
            }

    except HTTPError as error:
        try:
            data = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}

        return {
            "activated": False,
            "error": data.get("error", "Device activation failed."),
            "devices_used": data.get("devices_used"),
            "max_devices": data.get("max_devices"),
        }

    except (URLError, TimeoutError):
        return {
            "activated": False,
            "error": "Unable to connect to the license server.",
        }



def submit_audit_report(
    key,
    device_id,
    report,
    api_url=DEFAULT_AUDIT_REPORT_API_URL,
):
    """
    Submit a completed SystAudit report to the SaaS API.
    """

    payload = json.dumps(
        {
            "key": key,
            "device_id": device_id,
            "score": report.get("score"),
            "summary": report.get("summary", {}),
            "findings": report.get("findings", []),
            "recommendations": report.get("recommendations", []),
        }
    ).encode("utf-8")

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
                "saved": bool(data.get("saved", False)),
                "message": data.get("message"),
                "report_id": data.get("report_id"),
                "device_id": data.get("device_id"),
                "score": data.get("score"),
                "created_at": data.get("created_at"),
            }

    except HTTPError as error:
        try:
            data = json.loads(error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}

        return {
            "saved": False,
            "error": data.get(
                "error",
                "Unable to submit audit report.",
            ),
        }

    except (URLError, TimeoutError):
        return {
            "saved": False,
            "error": "Unable to connect to the license server.",
        }