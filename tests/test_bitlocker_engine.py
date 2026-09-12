from src.bitlocker_executor import execute_bitlocker_plan
from src.bitlocker_plan import BitLockerRemediationPlan


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