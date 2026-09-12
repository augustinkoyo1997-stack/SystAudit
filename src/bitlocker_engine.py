"""
BitLocker integration adapter for RemediationEngine.

This module only supports BitLocker dry-run execution.
It MUST NOT modify BitLocker or TPM configuration.
"""

from src.bitlocker_executor import execute_bitlocker_plan
from src.bitlocker_plan import BitLockerRemediationPlan
from src.remediation import Remediation, RemediationResult


def execute_bitlocker_plan_for_engine(
    remediation: Remediation,
    plan: BitLockerRemediationPlan,
    dry_run: bool = True,
) -> RemediationResult:
    """
    Adapt a BitLocker execution result to the generic remediation engine.
    """

    result = execute_bitlocker_plan(
        plan,
        dry_run=dry_run,
    )

    if result.success:
        return RemediationResult.success_result(
            remediation_id=remediation.id,
            message=result.message,
        )

    return RemediationResult.failure_result(
        remediation_id=remediation.id,
        message=result.message,
    )