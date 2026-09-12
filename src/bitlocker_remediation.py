"""
Read-only BitLocker diagnostic helpers.

This module MUST NOT modify BitLocker configuration.
Actual remediation will be implemented only after
a secure key-protector workflow is available.
"""

from src.security import get_bitlocker_status


def analyze_bitlocker_state():
    """
    Analyze the current BitLocker state without changing the system.

    Returns:
        dict containing the global diagnostic status and
        the state of each BitLocker volume.
    """

    volumes = get_bitlocker_status()

    if not volumes:
        return {
            "ready": False,
            "needs_remediation": False,
            "reason": "Unable to retrieve BitLocker status.",
            "volumes": [],
        }

    analyzed_volumes = []
    needs_remediation = False

    for volume in volumes:
        mount_point = volume.get("mount_point")

        encryption_percentage = volume.get(
            "encryption_percentage",
            0,
        )

        protection_status = volume.get(
            "protection_status",
            0,
        )

        key_protector_count = volume.get(
            "key_protector_count",
            0,
        )

        encrypted = encryption_percentage == 100
        protection_enabled = protection_status == 1

        if encrypted and protection_enabled and key_protector_count > 0:
            reason = "BitLocker protection is active."

        elif encrypted and not protection_enabled and key_protector_count == 0:
            reason = "No BitLocker key protector found."
            needs_remediation = True

        elif encrypted and not protection_enabled:
            reason = (
                "BitLocker protection is disabled "
                "and requires further analysis."
            )
            needs_remediation = True

        elif not encrypted:
            reason = "Volume is not fully encrypted."
            needs_remediation = True

        else:
            reason = "BitLocker state requires further analysis."
            needs_remediation = True

        analyzed_volumes.append(
            {
                "mount_point": mount_point,
                "encrypted": encrypted,
                "encryption_percentage": encryption_percentage,
                "protection_enabled": protection_enabled,
                "key_protectors": key_protector_count,
                "reason": reason,
            }
        )

    return {
        "ready": not needs_remediation,
        "needs_remediation": needs_remediation,
        "volumes": analyzed_volumes,
    }