"""
Controlled BitLocker recovery workflow.

This module currently provides a safe dry-run workflow only.
It MUST NOT modify BitLocker or TPM configuration.
"""

from dataclasses import dataclass

from src.bitlocker_preflight import check_bitlocker_preflight
from src.security import get_bitlocker_status

@dataclass
class WorkflowResult:
    success: bool
    volume: str
    message: str


def add_recovery_protector(volume: str, dry_run: bool = True) -> bool:
    """Simulate creation of a recovery protector."""
    if dry_run:
        return True

    raise RuntimeError(
        "Real BitLocker recovery-protector creation is disabled."
    )


def verify_recovery_protector(volume: str) -> bool:
    """Placeholder for recovery-protector verification."""
    return True


def add_tpm_protector(volume: str, dry_run: bool = True) -> bool:
    """Simulate creation of a TPM protector."""
    if dry_run:
        return True

    raise RuntimeError(
        "Real BitLocker TPM-protector creation is disabled."
    )


def verify_tpm_protector(volume: str) -> bool:
    """Placeholder for TPM-protector verification."""
    return True

def get_protector_types(volume: str) -> list[str]:
    """Return BitLocker key-protector types without exposing secrets."""

    for item in get_bitlocker_status():
        if item["mount_point"] != volume:
            continue

        return [
            protector.get("KeyProtectorType", "")
            for protector in item.get("key_protectors", [])
            if isinstance(protector, dict)
        ]

    return []


class BitLockerRecoveryWorkflow:
    """Controlled recovery-then-TPM workflow."""

    def __init__(self, volume: str):
        self.volume = volume
        self.approved = False

    def approve(self) -> None:
        """Approve the workflow without executing it."""
        self.approved = True

    def execute(self, dry_run: bool = True) -> WorkflowResult:
        """Execute the controlled workflow."""
        if not self.approved:
            return WorkflowResult(
                success=False,
                volume=self.volume,
                message="BitLocker workflow is not approved.",
            )

        preflight = check_bitlocker_preflight()

        if not preflight.get("ready", False):
            return WorkflowResult(
                success=False,
                volume=self.volume,
                message="BitLocker preflight failed.",
            )

        if not add_recovery_protector(
            self.volume,
            dry_run=dry_run,
        ):
            return WorkflowResult(
                success=False,
                volume=self.volume,
                message="Recovery protector creation failed.",
            )

        if not verify_recovery_protector(self.volume):
            return WorkflowResult(
                success=False,
                volume=self.volume,
                message="Recovery protector verification failed.",
            )

        if not add_tpm_protector(
            self.volume,
            dry_run=dry_run,
        ):
            return WorkflowResult(
                success=False,
                volume=self.volume,
                message="TPM protector creation failed.",
            )

        if not verify_tpm_protector(self.volume):
            return WorkflowResult(
                success=False,
                volume=self.volume,
                message="TPM protector verification failed.",
            )

        return WorkflowResult(
            success=True,
            volume=self.volume,
            message=(
                "DRY-RUN: recovery protector verified, "
                "then TPM protector verified."
            ),
        )