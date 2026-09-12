"""
Read-only BitLocker preflight checks.

This module MUST NOT modify BitLocker or TPM configuration.
"""


def check_bitlocker_preflight():
    """
    Check whether the system appears ready for a future
    controlled BitLocker key-protector workflow.

    No system-changing command is executed.
    """

    result = {
        "ready": False,
        "tpm_present": False,
        "tpm_ready": False,
        "tpm_enabled": False,
        "tpm_activated": False,
        "tpm_owned": False,
        "volumes": [],
        "reason": "",
    }

    try:
        import platform
        import subprocess

        if platform.system() != "Windows":
            result["reason"] = "BitLocker requires Windows."
            return result

        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-Tpm | "
                "Select-Object TpmPresent, TpmReady, "
                "TpmEnabled, TpmActivated, TpmOwned | "
                "ConvertTo-Json -Compress"
            ),
        ]

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if completed.returncode != 0:
            result["reason"] = "Unable to retrieve TPM status."
            return result

        import json

        data = json.loads(completed.stdout)

        result["tpm_present"] = bool(
            data.get("TpmPresent", False)
        )
        result["tpm_ready"] = bool(
            data.get("TpmReady", False)
        )
        result["tpm_enabled"] = bool(
            data.get("TpmEnabled", False)
        )
        result["tpm_activated"] = bool(
            data.get("TpmActivated", False)
        )
        result["tpm_owned"] = bool(
            data.get("TpmOwned", False)
        )

        result["ready"] = all(
            [
                result["tpm_present"],
                result["tpm_ready"],
                result["tpm_enabled"],
                result["tpm_activated"],
                result["tpm_owned"],
            ]
        )

        if result["ready"]:
            result["reason"] = (
                "TPM prerequisites are satisfied. "
                "A controlled BitLocker key-protector workflow "
                "may be prepared."
            )
        else:
            result["reason"] = (
                "TPM prerequisites are not fully satisfied."
            )

        return result

    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
    ):
        result["reason"] = "Unable to complete TPM preflight."
        return result