from unittest.mock import patch

from src.bitlocker_recovery_workflow import (
    BitLockerRecoveryWorkflow,
    get_protector_types,
)

def test_workflow_requires_approval():
    workflow = BitLockerRecoveryWorkflow(volume="C:")

    result = workflow.execute()

    assert result.success is False
    assert "approved" in result.message.lower()


def test_workflow_requires_preflight():
    workflow = BitLockerRecoveryWorkflow(volume="C:")
    workflow.approve()

    with patch(
        "src.bitlocker_recovery_workflow.check_bitlocker_preflight",
        return_value={
            "ready": False,
            "reason": "TPM prerequisites are not satisfied.",
        },
    ):
        result = workflow.execute()

    assert result.success is False
    assert "preflight" in result.message.lower()


def test_workflow_dry_run_recovery_then_tpm():
    workflow = BitLockerRecoveryWorkflow(volume="C:")
    workflow.approve()

    with patch(
        "src.bitlocker_recovery_workflow.check_bitlocker_preflight",
        return_value={"ready": True},
    ), patch(
        "src.bitlocker_recovery_workflow.add_recovery_protector",
        return_value=True,
    ) as recovery, patch(
        "src.bitlocker_recovery_workflow.verify_recovery_protector",
        return_value=True,
    ) as verify_recovery, patch(
        "src.bitlocker_recovery_workflow.add_tpm_protector",
        return_value=True,
    ) as tpm, patch(
        "src.bitlocker_recovery_workflow.verify_tpm_protector",
        return_value=True,
    ) as verify_tpm:

        result = workflow.execute(dry_run=True)

    assert result.success is True
    assert recovery.called
    assert verify_recovery.called
    assert tpm.called
    assert verify_tpm.called


def test_workflow_stops_if_recovery_verification_fails():
    workflow = BitLockerRecoveryWorkflow(volume="C:")
    workflow.approve()

    with patch(
        "src.bitlocker_recovery_workflow.check_bitlocker_preflight",
        return_value={"ready": True},
    ), patch(
        "src.bitlocker_recovery_workflow.add_recovery_protector",
        return_value=True,
    ), patch(
        "src.bitlocker_recovery_workflow.verify_recovery_protector",
        return_value=False,
    ), patch(
        "src.bitlocker_recovery_workflow.add_tpm_protector",
        return_value=True,
    ) as tpm:

        result = workflow.execute(dry_run=True)

    assert result.success is False
    assert not tpm.called

def test_workflow_stops_if_tpm_verification_fails():
    workflow = BitLockerRecoveryWorkflow(volume="C:")
    workflow.approve()

    with patch(
        "src.bitlocker_recovery_workflow.check_bitlocker_preflight",
        return_value={"ready": True},
    ), patch(
        "src.bitlocker_recovery_workflow.add_recovery_protector",
        return_value=True,
    ), patch(
        "src.bitlocker_recovery_workflow.verify_recovery_protector",
        return_value=True,
    ), patch(
        "src.bitlocker_recovery_workflow.add_tpm_protector",
        return_value=True,
    ), patch(
        "src.bitlocker_recovery_workflow.verify_tpm_protector",
        return_value=False,
    ):

        result = workflow.execute(dry_run=True)

    assert result.success is False
    assert "TPM protector verification failed" in result.message

def test_get_protector_types():
    with patch(
        "src.bitlocker_recovery_workflow.get_bitlocker_status",
        return_value=[
            {
                "mount_point": "C:",
                "key_protectors": [
                    {"KeyProtectorType": "RecoveryPassword"},
                    {"KeyProtectorType": "Tpm"},
                ],
            }
        ],
    ):
        assert get_protector_types("C:") == [
            "RecoveryPassword",
            "Tpm",
        ]


def test_get_protector_types_empty():
    with patch(
        "src.bitlocker_recovery_workflow.get_bitlocker_status",
        return_value=[
            {
                "mount_point": "C:",
                "key_protectors": [],
            }
        ],
    ):
        assert get_protector_types("C:") == []

def test_workflow_requires_recovery_before_tpm():
    workflow = BitLockerRecoveryWorkflow(volume="C:")
    workflow.approve()

    with patch(
        "src.bitlocker_recovery_workflow.check_bitlocker_preflight",
        return_value={"ready": True},
    ), patch(
        "src.bitlocker_recovery_workflow.add_recovery_protector",
        return_value=True,
    ), patch(
        "src.bitlocker_recovery_workflow.verify_recovery_protector",
        return_value=False,
    ), patch(
        "src.bitlocker_recovery_workflow.add_tpm_protector",
        return_value=True,
    ) as tpm:

        result = workflow.execute(dry_run=True)

    assert result.success is False
    assert not tpm.called