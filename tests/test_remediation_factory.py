from src.remediation import Remediation
from src.remediation_factory import (
    create_remediation_from_finding,
    create_remediations_from_findings,
)
from src.firewall_remediation import (
    enable_windows_firewall,
    verify_windows_firewall,
    disable_windows_firewall,
)
import pytest


def test_create_remediation_from_finding():
    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    assert isinstance(remediation, Remediation)
    assert remediation.id == "REM-FIREWALL"
    assert remediation.title == "Remediate firewall"
    assert remediation.description == "Windows Firewall is disabled."
    assert remediation.severity == "high"
    assert remediation.category == "firewall"

    # Une remediation n'est jamais approuvée automatiquement.
    assert remediation.approved is False

    # Le Firewall possède maintenant une action contrôlée.
    assert remediation.action is enable_windows_firewall
    assert remediation.verify_action is verify_windows_firewall
    assert remediation.rollback_action is disable_windows_firewall


def test_create_remediations_from_findings():
    findings = [
        {
            "risk": "high",
            "category": "firewall",
            "message": "Windows Firewall is disabled.",
        },
        {
            "risk": "medium",
            "category": "bitlocker",
            "message": "BitLocker protection is disabled.",
        },
    ]

    remediations = create_remediations_from_findings(findings)

    assert len(remediations) == 2

    assert remediations[0].id == "REM-FIREWALL"
    assert remediations[0].category == "firewall"
    assert remediations[0].approved is False

    assert remediations[1].id == "REM-BITLOCKER"
    assert remediations[1].category == "bitlocker"
    assert remediations[1].approved is False


def test_security_findings_can_be_converted_to_remediations(monkeypatch):
    findings = [
        {
            "risk": "high",
            "category": "firewall",
            "message": "Windows Firewall is disabled.",
        },
        {
            "risk": "high",
            "category": "uac",
            "message": "User Account Control (UAC) is disabled.",
        },
    ]

    remediations = create_remediations_from_findings(findings)

    assert len(remediations) == len(findings)

    for remediation in remediations:
        # Aucune remediation n'est approuvée automatiquement.
        assert remediation.approved is False

        # Le Firewall est actuellement exécutable.
        if remediation.category == "firewall":
            assert remediation.action is enable_windows_firewall
            assert remediation.verify_action is verify_windows_firewall
            assert remediation.rollback_action is disable_windows_firewall

        # Les autres catégories ne disposent pas encore
        # d'une action d'exécution.
        else:
            assert remediation.action is None


def test_firewall_remediation_requires_admin_and_is_reversible():
    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    assert remediation.requires_admin is True
    assert remediation.reversible is True


def test_uac_remediation_requires_admin_and_is_reversible():
    finding = {
        "risk": "high",
        "category": "uac",
        "message": "User Account Control (UAC) is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    assert remediation.requires_admin is True
    assert remediation.reversible is True


@pytest.mark.parametrize(
    "category,requires_admin,reversible",
    [
        ("firewall", True, True),
        ("uac", True, True),
        ("antivirus", True, True),
        ("bitlocker", True, True),
        ("password_policy", True, True),
        ("service", True, True),
        ("scheduled_task", True, True),
        ("process", True, False),
    ],
)
def test_remediation_security_properties(
    category,
    requires_admin,
    reversible,
):
    finding = {
        "risk": "high",
        "category": category,
        "message": f"Test finding for {category}.",
    }

    remediation = create_remediation_from_finding(finding)

    assert remediation.requires_admin is requires_admin
    assert remediation.reversible is reversible


def test_firewall_factory_creates_executable_remediation():
    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    assert remediation.action is enable_windows_firewall
    assert remediation.verify_action is verify_windows_firewall
    assert remediation.rollback_action is disable_windows_firewall
