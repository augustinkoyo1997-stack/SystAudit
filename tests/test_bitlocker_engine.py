from src.bitlocker_executor import execute_bitlocker_plan
from src.bitlocker_plan import BitLockerRemediationPlan
from src.bitlocker_engine import execute_bitlocker_plan_for_engine
from src.remediation import Remediation
from src.remediation_engine import RemediationEngine


def test_bitlocker_plan_can_complete_dry_run_workflow():
    plan = BitLockerRemediationPlan(
        volume="C:",
        action="CREATE_KEY_PROTECTOR",
        protection_type="TPM",
    )

    assert plan.approved is False
    assert plan.can_execute() is False

    plan.approve()

    assert plan.approved is True
    assert plan.can_execute() is False

    plan.execution_allowed = True

    result = execute_bitlocker_plan(
        plan,
        dry_run=True,
    )

    assert result.success is True
    assert result.volume == "C:"
    assert "DRY-RUN" in result.message


def test_bitlocker_dry_run_does_not_enable_real_execution():
    plan = BitLockerRemediationPlan(
        volume="C:",
        action="CREATE_KEY_PROTECTOR",
        protection_type="TPM",
    )

    plan.approve()
    plan.execution_allowed = True

    result = execute_bitlocker_plan(
        plan,
        dry_run=False,
    )

    assert result.success is False
    assert "intentionally disabled" in result.message.lower()
def test_bitlocker_plan_integrates_with_remediation_engine():
    plan = BitLockerRemediationPlan(
        volume="C:",
        action="CREATE_KEY_PROTECTOR",
        protection_type="TPM",
    )

    plan.approve()
    plan.execution_allowed = True

    remediation = Remediation(
        id="REM-BITLOCKER",
        title="Remediate bitlocker",
        description="BitLocker dry-run",
        severity="medium",
        category="bitlocker",
        action=None,
        verify_action=lambda: True,
        requires_admin=True,
        reversible=False,
    )

    remediation.approve()

    execution_result = {}

    def bitlocker_handler(current_remediation):
        result = execute_bitlocker_plan_for_engine(
            current_remediation,
            plan,
            dry_run=True,
        )

        execution_result["result"] = result
        return result

    engine = RemediationEngine(
        remediation,
        execution_handler=bitlocker_handler,
    )

    result = engine.run()

    assert result.success is True
    assert engine.state == RemediationEngine.VERIFIED
    assert result.remediation_id == "REM-BITLOCKER"

    assert execution_result["result"].success is True
    assert "DRY-RUN" in execution_result["result"].message