"""
Controlled BitLocker remediation planning.

This module only creates a remediation plan.
It MUST NOT modify BitLocker or TPM configuration.
"""

from dataclasses import dataclass


@dataclass
class BitLockerRemediationPlan:
    """Describe a future BitLocker remediation without executing it."""

    volume: str
    action: str
    protection_type: str
    requires_admin: bool = True
    approved: bool = False
    execution_allowed: bool = False

    def approve(self) -> None:
        """Approve the plan without executing it."""
        self.approved = True

    def can_execute(self) -> bool:
        """
        Determine whether execution is allowed.

        Actual execution remains disabled until the secure
        BitLocker workflow is explicitly enabled.
        """
        return (
            self.approved
            and self.requires_admin is True
            and self.execution_allowed is True
        )