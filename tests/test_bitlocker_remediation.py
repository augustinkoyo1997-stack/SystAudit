from unittest.mock import patch

from src.bitlocker_remediation import analyze_bitlocker_state


def test_no_bitlocker_data():
    with patch(
        "src.bitlocker_remediation.get_bitlocker_status",
        return_value=[],
    ):
        result = analyze_bitlocker_state()

    assert result["ready"] is False
    assert result["needs_remediation"] is False
    assert result["volumes"] == []


def test_all_volumes_protected():
    bitlocker_data = [
        {
            "mount_point": "C:",
            "volume_status": 1,
            "protection_status": 1,
            "encryption_percentage": 100,
            "encryption_method": 6,
            "key_protectors": [{"KeyProtectorType": "Tpm"}],
            "key_protector_count": 1,
        }
    ]

    with patch(
        "src.bitlocker_remediation.get_bitlocker_status",
        return_value=bitlocker_data,
    ):
        result = analyze_bitlocker_state()

    assert result["ready"] is True
    assert result["needs_remediation"] is False
    assert result["volumes"][0]["protection_enabled"] is True
    assert result["volumes"][0]["key_protectors"] == 1


def test_encrypted_without_key_protector_is_unsafe():
    bitlocker_data = [
        {
            "mount_point": "C:",
            "volume_status": 1,
            "protection_status": 0,
            "encryption_percentage": 100,
            "encryption_method": 6,
            "key_protectors": [],
            "key_protector_count": 0,
        }
    ]

    with patch(
        "src.bitlocker_remediation.get_bitlocker_status",
        return_value=bitlocker_data,
    ):
        result = analyze_bitlocker_state()

    assert result["ready"] is False
    assert result["needs_remediation"] is True
    assert result["volumes"][0]["encrypted"] is True
    assert result["volumes"][0]["protection_enabled"] is False
    assert result["volumes"][0]["key_protectors"] == 0
    assert "key protector" in result["volumes"][0]["reason"].lower()


def test_mixed_volume_state_requires_attention():
    bitlocker_data = [
        {
            "mount_point": "C:",
            "volume_status": 1,
            "protection_status": 1,
            "encryption_percentage": 100,
            "encryption_method": 6,
            "key_protectors": [{"KeyProtectorType": "Tpm"}],
            "key_protector_count": 1,
        },
        {
            "mount_point": "D:",
            "volume_status": 1,
            "protection_status": 0,
            "encryption_percentage": 100,
            "encryption_method": 6,
            "key_protectors": [],
            "key_protector_count": 0,
        },
    ]

    with patch(
        "src.bitlocker_remediation.get_bitlocker_status",
        return_value=bitlocker_data,
    ):
        result = analyze_bitlocker_state()

    assert result["ready"] is False
    assert result["needs_remediation"] is True
    assert result["volumes"][0]["protection_enabled"] is True
    assert result["volumes"][1]["protection_enabled"] is False