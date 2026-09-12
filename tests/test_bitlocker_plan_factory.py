from src.bitlocker_plan_factory import create_bitlocker_plans


def test_create_plans_for_unprotected_volumes():
    diagnostic = {
        "ready": False,
        "needs_remediation": True,
        "volumes": [
            {
                "mount_point": "C:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": False,
                "key_protectors": 0,
                "reason": "No BitLocker key protector found.",
            },
            {
                "mount_point": "D:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": False,
                "key_protectors": 0,
                "reason": "No BitLocker key protector found.",
            },
            {
                "mount_point": "E:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": False,
                "key_protectors": 0,
                "reason": "No BitLocker key protector found.",
            },
        ],
    }

    plans = create_bitlocker_plans(diagnostic)

    assert len(plans) == 3

    assert [plan.volume for plan in plans] == [
        "C:",
        "D:",
        "E:",
    ]

    assert all(
        plan.action == "CREATE_KEY_PROTECTOR"
        for plan in plans
    )

    assert all(
        plan.protection_type == "TPM"
        for plan in plans
    )

    assert all(
        plan.approved is False
        for plan in plans
    )

    assert all(
        plan.execution_allowed is False
        for plan in plans
    )


def test_no_plans_when_remediation_is_not_needed():
    diagnostic = {
        "ready": True,
        "needs_remediation": False,
        "volumes": [
            {
                "mount_point": "C:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": True,
                "key_protectors": 1,
            }
        ],
    }

    plans = create_bitlocker_plans(diagnostic)

    assert plans == []


def test_protected_volume_is_skipped():
    diagnostic = {
        "ready": False,
        "needs_remediation": True,
        "volumes": [
            {
                "mount_point": "C:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": True,
                "key_protectors": 1,
            },
            {
                "mount_point": "D:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": False,
                "key_protectors": 0,
            },
        ],
    }

    plans = create_bitlocker_plans(diagnostic)

    assert len(plans) == 1
    assert plans[0].volume == "D:"


def test_volume_with_existing_key_protector_is_skipped():
    diagnostic = {
        "ready": False,
        "needs_remediation": True,
        "volumes": [
            {
                "mount_point": "C:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": False,
                "key_protectors": 1,
            },
            {
                "mount_point": "D:",
                "encrypted": True,
                "encryption_percentage": 100,
                "protection_enabled": False,
                "key_protectors": 0,
            },
        ],
    }

    plans = create_bitlocker_plans(diagnostic)

    assert len(plans) == 1
    assert plans[0].volume == "D:"