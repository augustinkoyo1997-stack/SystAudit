from src.bitlocker_executor import execute_bitlocker_plan
from src.bitlocker_plan import BitLockerRemediationPlan


def create_plan():
    return BitLockerRemediationPlan(
        volume="C:",
        action="CREATE_KEY_PROTECTOR",
        protection_type="TPM",
    )


def test_unapproved_plan_cannot_execute():
    plan = create_plan()

    result = execute_bitlocker_plan(plan)

    assert result.success is False
    assert result.volume == "C:"
    assert "not approved" in result.message.lower()


def test_approved_but_disabled_plan_cannot_execute():
    plan = create_plan()
    plan.approve()

    result = execute_bitlocker_plan(plan)

    assert result.success is False
    assert "not allowed" in result.message.lower()


def test_approved_plan_can_run_in_dry_run():
    plan = create_plan()
    plan.approve()
    plan.execution_allowed = True

    result = execute_bitlocker_plan(
        plan,
        dry_run=True,
    )

    assert result.success is True
    assert result.volume == "C:"
    assert "DRY-RUN" in result.message
    assert "TPM" in result.message


def test_real_execution_is_always_blocked():
    plan = create_plan()
    plan.approve()
    plan.execution_allowed = True

    result = execute_bitlocker_plan(
        plan,
        dry_run=False,
    )

    assert result.success is False
    assert "intentionally disabled" in result.message.lower()