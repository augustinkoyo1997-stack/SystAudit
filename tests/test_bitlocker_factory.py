from unittest.mock import patch

from src.remediation_factory import create_remediation_from_finding


def test_bitlocker_factory_creates_safe_remediation():
    finding = {
        "risk": "medium",
        "category": "bitlocker",
        "message": (
            "BitLocker protection is disabled on volume(s): C:, D:, E:."
        ),
    }

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
            }
        ],
    }

    with patch(
        "src.remediation_factory.analyze_bitlocker_state",
        return_value=diagnostic,
    ):
        remediation = create_remediation_from_finding(finding)

    assert remediation.id == "REM-BITLOCKER"
    assert remediation.category == "bitlocker"

    assert remediation.requires_admin is True
    assert remediation.reversible is True

    # BitLocker ne doit pas encore disposer
    # d'une action automatique.
    assert remediation.action is None
    assert remediation.verify_action is None
    assert remediation.rollback_action is None

    # Le diagnostic doit être intégré à la proposition.
    assert "Automatic BitLocker remediation is blocked" in (
        remediation.description
    )


def test_bitlocker_factory_does_not_execute_any_action():
    finding = {
        "risk": "medium",
        "category": "bitlocker",
        "message": "BitLocker protection requires remediation.",
    }

    diagnostic = {
        "ready": False,
        "needs_remediation": True,
        "volumes": [],
    }

    with patch(
        "src.remediation_factory.analyze_bitlocker_state",
        return_value=diagnostic,
    ):
        remediation = create_remediation_from_finding(finding)

    assert remediation.action is None
    assert remediation.verify_action is None
    assert remediation.rollback_action is None