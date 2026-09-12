"""
Safe BitLocker remediation executor.

This module only supports dry-run execution.
It MUST NOT modify BitLocker or TPM configuration.
"""

from dataclasses import dataclass

from src.bitlocker_plan import BitLockerRemediationPlan


@dataclass
class BitLockerExecutionResult:
    """Result of a BitLocker dry-run execution."""

    success: bool
    volume: str
    message: str


def execute_bitlocker_plan(
    plan: BitLockerRemediationPlan,
    dry_run: bool = True,
) -> BitLockerExecutionResult:
    """
    Execute a BitLocker remediation plan.

    Only dry-run execution is currently supported.
    """

    if not plan.approved:
        return BitLockerExecutionResult(
            success=False,
            volume=plan.volume,
            message="BitLocker remediation plan is not approved.",
        )

    if not plan.can_execute():
        return BitLockerExecutionResult(
            success=False,
            volume=plan.volume,
            message="BitLocker remediation execution is not allowed.",
        )

    if not dry_run:
        return BitLockerExecutionResult(
            success=False,
            volume=plan.volume,
            message=(
                "Real BitLocker execution is intentionally disabled."
            ),
        )

    return BitLockerExecutionResult(
        success=True,
        volume=plan.volume,
        message=(
            f"DRY-RUN: would create a "
            f"{plan.protection_type} key protector on "
            f"{plan.volume}."
        ),
    )