"""
Controlled remediation engine for SystAudit.

This module defines the safe foundation for remediation actions.
Actual system-changing actions will be added later.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional


@dataclass
class RemediationResult:
    """Store the result of a remediation execution."""

    remediation_id: str
    success: bool
    message: str
    executed_at: datetime

    @classmethod
    def success_result(
        cls,
        remediation_id: str,
        message: str = "Remediation executed successfully.",
    ) -> "RemediationResult":
        """Create a successful remediation result."""
        return cls(
            remediation_id=remediation_id,
            success=True,
            message=message,
            executed_at=datetime.now(timezone.utc),
        )

    @classmethod
    def failure_result(
        cls,
        remediation_id: str,
        message: str,
    ) -> "RemediationResult":
        """Create a failed remediation result."""
        return cls(
            remediation_id=remediation_id,
            success=False,
            message=message,
            executed_at=datetime.now(timezone.utc),
        )

@dataclass
class RemediationLog:
    """Store an audit log entry for a remediation."""

    remediation_id: str
    status: str
    message: str
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def approval(cls, remediation_id: str) -> "RemediationLog":
        """Create an approval log entry."""
        return cls(
            remediation_id=remediation_id,
            status="approved",
            message="Remediation approved.",
        )

    @classmethod
    def success(
        cls,
        remediation_id: str,
        message: str,
    ) -> "RemediationLog":
        """Create a successful execution log entry."""
        return cls(
            remediation_id=remediation_id,
            status="success",
            message=message,
        )

    @classmethod
    def failure(
        cls,
        remediation_id: str,
        message: str,
    ) -> "RemediationLog":
        """Create a failed execution log entry."""
        return cls(
            remediation_id=remediation_id,
            status="failure",
            message=message,
        )

@dataclass
class Remediation:
    """Describe a controlled security remediation."""

    id: str
    title: str
    description: str
    severity: str
    category: str
    action: Optional[Callable[[], bool]] = None
    rollback_action: Optional[Callable[[], bool]] = None
    verify_action: Optional[Callable[[], bool]] = None
    requires_admin: bool = False
    reversible: bool = False
    approved: bool = False
    logs: list[RemediationLog] = field(default_factory=list)
    logs: list[RemediationLog] = field(default_factory=list)

    def approve(self) -> None:
        """Explicitly approve this remediation."""
        self.approved = True
        self.logs.append(
            RemediationLog.approval(self.id)
        )

    def revoke_approval(self) -> None:
        """Revoke approval for this remediation."""
        self.approved = False

    def check_preconditions(self) -> bool:
        """
        Check whether the remediation is allowed to execute.

        This is intentionally a safe foundation.
        Real system checks will be added later.
        """
        if self.action is None:
            return False

        return True

    def is_admin(self) -> bool:
        """
        Check whether the current process has administrator privileges.

        Returns:
            True if the current process is running with administrator
            privileges, otherwise False.
        """
        try:
            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False

    def execute(self) -> RemediationResult:
        """
        Execute the remediation action only if it was approved
        and its preconditions are satisfied.

        Returns:
            A RemediationResult describing the execution.

        Raises:
            PermissionError: If the remediation has not been approved.
            RuntimeError: If the preconditions are not satisfied.
        """
        if not self.approved:
            raise PermissionError(
                f"Remediation '{self.id}' has not been approved."
            )

        if self.requires_admin and not self.is_admin():
            raise PermissionError(
                f"Administrator privileges are required for remediation "
                f"'{self.id}'."
            )

        if not self.check_preconditions():
            raise RuntimeError(
                f"Preconditions not satisfied for remediation '{self.id}'."
            )

        try:
            success = bool(self.action())

            if success:
                message = "Remediation executed successfully."

                self.logs.append(
                    RemediationLog.success(
                        self.id,
                        message,
                    )
                )

                return RemediationResult.success_result(
                    self.id,
                    message,
                )

            message = "Remediation action failed."

            self.logs.append(
                RemediationLog.failure(
                    self.id,
                    message,
                )
            )

            return RemediationResult.failure_result(
                self.id,
                message,
            )

            return RemediationResult.failure_result(
                self.id,
                "Remediation action failed.",
            )

        except Exception as exc:
            message = f"Remediation execution failed: {exc}"

            self.logs.append(
                RemediationLog.failure(
                    self.id,
                    message,
                )
            )

            return RemediationResult.failure_result(
                self.id,
                message,
            )

    def rollback(self) -> RemediationResult:
        """
        Roll back an executed remediation.

        Returns:
            RemediationResult describing the rollback operation.

        Raises:
            PermissionError: If the remediation was not approved.
            RuntimeError: If the remediation is not reversible or has no
                rollback action.
        """
        if not self.approved:
            raise PermissionError(
                "Remediation must be approved before rollback."
            )

        if not self.reversible:
            raise RuntimeError(
                "This remediation is not reversible."
            )

        if self.rollback_action is None:
            raise RuntimeError(
                "No rollback action is defined."
            )

        try:
            success = bool(self.rollback_action())

            if success:
                result = RemediationResult.success_result(
                    self.id,
                    "Remediation rollback completed successfully.",
                )
                self.logs.append(
                    RemediationLog.success(
                        self.id,
                        result.message,
                    )
                )
                return result

            result = RemediationResult.failure_result(
                self.id,
                "Remediation rollback failed.",
            )
            self.logs.append(
                RemediationLog.failure(
                    self.id,
                    result.message,
                )
            )
            return result

        except Exception as exc:
            result = RemediationResult.failure_result(
                self.id,
                f"Remediation rollback failed: {exc}",
            )
            self.logs.append(
                RemediationLog.failure(
                    self.id,
                    result.message,
                )
            )
            return result

    def verify(self) -> RemediationResult:
        """
        Verify that the remediation was successfully applied.

        Returns:
            RemediationResult describing the verification.

        Raises:
            PermissionError: If the remediation was not approved.
            RuntimeError: If no verification action is defined.
        """
        if not self.approved:
            raise PermissionError(
                "Remediation must be approved before verification."
            )

        if self.verify_action is None:
            raise RuntimeError(
                "No verification action is defined."
            )

        try:
            success = bool(self.verify_action())

            if success:
                result = RemediationResult.success_result(
                    self.id,
                    "Remediation verification completed successfully.",
                )
                self.logs.append(
                    RemediationLog.success(
                        self.id,
                        result.message,
                    )
                )
                return result

            result = RemediationResult.failure_result(
                self.id,
                "Remediation verification failed.",
            )
            self.logs.append(
                RemediationLog.failure(
                    self.id,
                    result.message,
                )
            )
            return result

        except Exception as exc:
            result = RemediationResult.failure_result(
                self.id,
                f"Remediation verification failed: {exc}",
            )
            self.logs.append(
                RemediationLog.failure(
                    self.id,
                    result.message,
                )
            )
            return result