from src.bitlocker_plan import BitLockerRemediationPlan


def test_bitlocker_plan_is_not_executable_by_default():
    plan = BitLockerRemediationPlan(
        volume="C:",
        action="CREATE_KEY_PROTECTOR",
        protection_type="TPM",
    )

    assert plan.volume == "C:"
    assert plan.action == "CREATE_KEY_PROTECTOR"
    assert plan.protection_type == "TPM"

    assert plan.requires_admin is True
    assert plan.approved is False
    assert plan.execution_allowed is False

    assert plan.can_execute() is False


def test_approval_alone_does_not_enable_execution():
    plan = BitLockerRemediationPlan(
        volume="C:",
        action="CREATE_KEY_PROTECTOR",
        protection_type="TPM",
    )

    plan.approve()

    assert plan.approved is True
    assert plan.execution_allowed is False
    assert plan.can_execute() is False


def test_execution_requires_explicit_enablement():
    plan = BitLockerRemediationPlan(
        volume="C:",
        action="CREATE_KEY_PROTECTOR",
        protection_type="TPM",
    )

    plan.approve()

    plan.execution_allowed = True

    assert plan.can_execute() is True


def test_each_volume_has_its_own_plan():
    volumes = ["C:", "D:", "E:"]

    plans = [
        BitLockerRemediationPlan(
            volume=volume,
            action="CREATE_KEY_PROTECTOR",
            protection_type="TPM",
        )
        for volume in volumes
    ]

    assert [plan.volume for plan in plans] == [
        "C:",
        "D:",
        "E:",
    ]

    assert all(
        plan.execution_allowed is False
        for plan in plans
    )