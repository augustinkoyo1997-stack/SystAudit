from typing import Callable, Optional

from src.remediation import Remediation, RemediationResult


class RemediationEngine:
    """Orchestrate the controlled remediation workflow."""

    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EXECUTED = "EXECUTED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    VERIFY_FAILED = "VERIFY_FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"

    def __init__(
        self,
        remediation: Remediation,
        execution_handler: Optional[Callable] = None,
    ):
        self.remediation = remediation
        self.execution_handler = execution_handler
        self.state = self.PROPOSED

    def sync_state(self) -> str:
        """Synchronize the engine state with the remediation approval."""
        if self.remediation.approved:
            self.state = self.APPROVED
        else:
            self.state = self.PROPOSED

        return self.state

    def _execute(self) -> RemediationResult:
        """
        Execute the remediation.

        A custom execution handler can be supplied for remediation types
        that require a specialized workflow. Otherwise, the standard
        Remediation.execute() method is used.
        """
        if self.execution_handler is not None:
            result = self.execution_handler(self.remediation)

            if isinstance(result, RemediationResult):
                return result

            return RemediationResult(
                success=False,
                remediation_id=self.remediation.id,
                message=(
                    "Custom execution handler returned an invalid result."
                ),
            )

        return self.remediation.execute()

    def run(self) -> RemediationResult:
        """
        Execute, verify, and optionally roll back a remediation.

        Returns:
            RemediationResult containing the final operation status.

        Raises:
            PermissionError: If the remediation is not approved.
        """
        if not self.remediation.approved:
            raise PermissionError(
                "Remediation must be approved before execution."
            )

        self.state = self.APPROVED

        self.state = self.EXECUTING
        execution_result = self._execute()

        if not execution_result.success:
            self.state = self.EXECUTION_FAILED
            return execution_result

        self.state = self.EXECUTED

        self.state = self.VERIFYING
        verification_result = self.remediation.verify()

        if verification_result.success:
            self.state = self.VERIFIED
            return verification_result

        self.state = self.VERIFY_FAILED

        if self.remediation.reversible:
            self.state = self.ROLLING_BACK

            rollback_result = self.remediation.rollback()

            if rollback_result.success:
                self.state = self.ROLLED_BACK
            else:
                self.state = self.ROLLBACK_FAILED

        return verification_result