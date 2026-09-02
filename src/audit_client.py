import requests

from .audit_engine import run_audit


def submit_audit_report(
    api_url,
    license_key,
    device_id,
    timeout=10,
):
    """
    Run a local security audit and submit the result to the SaaS API.

    Returns the API response as a dictionary.
    """

    if not api_url:
        raise ValueError("api_url is required")

    if not license_key:
        raise ValueError("license_key is required")

    if not device_id:
        raise ValueError("device_id is required")

    report = run_audit()

    payload = {
        "key": license_key,
        "device_id": device_id,
        "score": report["score"],
        "summary": report["summary"],
        "findings": report["findings"],
        "recommendations": report["recommendations"],
    }

    response = requests.post(
        api_url,
        json=payload,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    result = submit_audit_report(
        api_url="http://127.0.0.1:8000/api/license/audit/report/",
        license_key="YOUR-LICENSE-KEY",
        device_id="YOUR-DEVICE-ID",
    )

    print(result)