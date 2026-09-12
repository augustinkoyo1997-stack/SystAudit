from unittest.mock import patch

from src.bitlocker_preflight import check_bitlocker_preflight


def test_tpm_ready_for_bitlocker_workflow():
    tpm_data = (
        '{"TpmPresent":true,'
        '"TpmReady":true,'
        '"TpmEnabled":true,'
        '"TpmActivated":true,'
        '"TpmOwned":true}'
    )

    completed = type(
        "CompletedProcess",
        (),
        {
            "returncode": 0,
            "stdout": tpm_data,
        },
    )()

    with patch(
        "subprocess.run",
        return_value=completed,
    ):
        result = check_bitlocker_preflight()

    assert result["ready"] is True
    assert result["tpm_present"] is True
    assert result["tpm_ready"] is True
    assert result["tpm_enabled"] is True
    assert result["tpm_activated"] is True
    assert result["tpm_owned"] is True


def test_tpm_not_ready_blocks_workflow():
    tpm_data = (
        '{"TpmPresent":true,'
        '"TpmReady":false,'
        '"TpmEnabled":true,'
        '"TpmActivated":true,'
        '"TpmOwned":true}'
    )

    completed = type(
        "CompletedProcess",
        (),
        {
            "returncode": 0,
            "stdout": tpm_data,
        },
    )()

    with patch(
        "subprocess.run",
        return_value=completed,
    ):
        result = check_bitlocker_preflight()

    assert result["ready"] is False
    assert result["tpm_present"] is True
    assert result["tpm_ready"] is False


def test_tpm_command_failure():
    completed = type(
        "CompletedProcess",
        (),
        {
            "returncode": 1,
            "stdout": "",
        },
    )()

    with patch(
        "subprocess.run",
        return_value=completed,
    ):
        result = check_bitlocker_preflight()

    assert result["ready"] is False
    assert "Unable to retrieve TPM status" in result["reason"]