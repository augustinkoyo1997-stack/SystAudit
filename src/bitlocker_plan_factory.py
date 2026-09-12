"""
Create controlled BitLocker remediation plans.

This module only creates plans.
It MUST NOT modify BitLocker or TPM configuration.
"""

from src.bitlocker_plan import BitLockerRemediationPlan


def create_bitlocker_plans(diagnostic):
    """
    Create one remediation plan for every BitLocker volume
    requiring remediation.

    No system-changing action is executed.
    """

    if not diagnostic.get("needs_remediation", False):
        return []

    plans = []

    for volume in diagnostic.get("volumes", []):
        if not volume.get("encrypted", False):
            continue

        if volume.get("protection_enabled", False):
            continue

        if volume.get("key_protectors", 0) > 0:
            continue

        volume_name = volume.get("mount_point")

        if not volume_name:
            continue

        plans.append(
            BitLockerRemediationPlan(
                volume=volume_name,
                action="CREATE_KEY_PROTECTOR",
                protection_type="TPM",
            )
        )

    return plans