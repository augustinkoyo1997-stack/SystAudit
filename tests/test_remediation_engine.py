import pytest

from src.remediation import Remediation, RemediationResult
from src.remediation_engine import RemediationEngine


def test_engine_executes_and_verifies_remediation():
    executed = []
    verified = []

    remediation = Remediation(
        id="ENGINE-001",
        title="Test remediation",
        description="Test engine workflow",
        severity="high",
        category="security",
        action=lambda: executed.append(True) or True,
        verify_action=lambda: verified.append(True) or True,
    )

    engine = RemediationEngine(remediation)
    remediation.approve()

    result = engine.run()

    assert isinstance(result, RemediationResult)
    assert result.success is True
    assert executed == [True]
    assert verified == [True]


def test_engine_requires_approval():
    remediation = Remediation(
        id="ENGINE-002",
        title="Protected remediation",
        description="Test approval",
        severity="high",
        category="security",
        action=lambda: True,
        verify_action=lambda: True,
    )

    engine = RemediationEngine(remediation)

    with pytest.raises(PermissionError):
        engine.run()


def test_engine_rolls_back_when_verification_fails():
    executed = []
    rolled_back = []

    remediation = Remediation(
        id="ENGINE-003",
        title="Rollback remediation",
        description="Test automatic rollback",
        severity="critical",
        category="security",
        action=lambda: executed.append(True) or True,
        verify_action=lambda: False,
        reversible=True,
        rollback_action=lambda: rolled_back.append(True) or True,
    )

    engine = RemediationEngine(remediation)
    remediation.approve()

    result = engine.run()

    assert isinstance(result, RemediationResult)
    assert result.success is False
    assert executed == [True]
    assert rolled_back == [True]


def test_engine_does_not_rollback_non_reversible_remediation():
    remediation = Remediation(
        id="ENGINE-004",
        title="Non reversible remediation",
        description="Test failed verification",
        severity="high",
        category="system",
        action=lambda: True,
        verify_action=lambda: False,
        reversible=False,
    )

    engine = RemediationEngine(remediation)
    remediation.approve()

    result = engine.run()

    assert isinstance(result, RemediationResult)
    assert result.success is False

def test_engine_starts_with_proposed_state():
    remediation = Remediation(
        id="ENGINE-005",
        title="State test",
        description="Test initial state",
        severity="medium",
        category="system",
        action=lambda: True,
        verify_action=lambda: True,
    )

    engine = RemediationEngine(remediation)

    assert engine.state == "PROPOSED"


def test_engine_moves_to_approved_state():
    remediation = Remediation(
        id="ENGINE-006",
        title="Approval state",
        description="Test approved state",
        severity="medium",
        category="security",
        action=lambda: True,
        verify_action=lambda: True,
    )

    engine = RemediationEngine(remediation)

    remediation.approve()

    engine.sync_state()

    assert engine.state == "APPROVED"


def test_engine_moves_to_verified_state():
    remediation = Remediation(
        id="ENGINE-007",
        title="Verification state",
        description="Test verified state",
        severity="high",
        category="security",
        action=lambda: True,
        verify_action=lambda: True,
    )

    engine = RemediationEngine(remediation)

    remediation.approve()
    result = engine.run()

    assert result.success is True
    assert engine.state == "VERIFIED"


def test_engine_moves_to_verify_failed_state():
    remediation = Remediation(
        id="ENGINE-008",
        title="Verification failure state",
        description="Test verification failure",
        severity="high",
        category="security",
        action=lambda: True,
        verify_action=lambda: False,
        reversible=False,
    )

    engine = RemediationEngine(remediation)

    remediation.approve()
    result = engine.run()

    assert result.success is False
    assert engine.state == "VERIFY_FAILED"


def test_engine_moves_to_rolled_back_state():
    remediation = Remediation(
        id="ENGINE-009",
        title="Rollback state",
        description="Test rollback state",
        severity="critical",
        category="security",
        action=lambda: True,
        verify_action=lambda: False,
        reversible=True,
        rollback_action=lambda: True,
    )

    engine = RemediationEngine(remediation)

    remediation.approve()
    result = engine.run()

    assert result.success is False
    assert engine.state == "ROLLED_BACK"

def test_engine_moves_to_execution_failed_state():
    remediation = Remediation(
        id="ENGINE-010",
        title="Execution failure",
        description="Test execution failure state",
        severity="critical",
        category="security",
        action=lambda: False,
        verify_action=lambda: True,
    )

    engine = RemediationEngine(remediation)

    remediation.approve()
    result = engine.run()

    assert result.success is False
    assert engine.state == "EXECUTION_FAILED"

def test_engine_moves_to_rollback_failed_state():
    remediation = Remediation(
        id="ENGINE-011",
        title="Rollback failure",
        description="Test rollback failure state",
        severity="critical",
        category="security",
        action=lambda: True,
        verify_action=lambda: False,
        reversible=True,
        rollback_action=lambda: False,
    )

    engine = RemediationEngine(remediation)

    remediation.approve()
    result = engine.run()

    assert result.success is False
    assert engine.state == "ROLLBACK_FAILED"


def test_firewall_factory_remediation_rolls_back_after_failed_verification(
    monkeypatch,
):
    from src.remediation_factory import create_remediation_from_finding
    from src.remediation_engine import RemediationEngine
    import src.firewall_remediation as firewall_remediation

    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    # Simule les privilèges administrateur.
    monkeypatch.setattr(
        remediation,
        "is_admin",
        lambda: True,
    )

    # État initial du firewall.
    initial_state = {
        "Domain": True,
        "Public": False,
        "Private": True,
    }

    # Suivi des opérations.
    calls = []

    def fake_capture_state():
        calls.append("capture")
        return initial_state

    def fake_enable_firewall():
        calls.append("enable")
        return True

    def fake_verify_firewall():
        calls.append("verify")
        return False

    def fake_restore_state(state):
        calls.append(("restore", state))
        return True

    monkeypatch.setattr(
        firewall_remediation,
        "get_windows_firewall_state",
        fake_capture_state,
    )
    monkeypatch.setattr(
        firewall_remediation,
        "enable_windows_firewall",
        fake_enable_firewall,
    )
    monkeypatch.setattr(
        firewall_remediation,
        "verify_windows_firewall",
        fake_verify_firewall,
    )
    monkeypatch.setattr(
        firewall_remediation,
        "restore_windows_firewall_state",
        fake_restore_state,
    )

    # Important :
    # les fonctions ont déjà été importées dans remediation_factory.py,
    # donc on doit également les remplacer dans ce module.
    import src.remediation_factory as remediation_factory

    monkeypatch.setattr(
        remediation_factory,
        "get_windows_firewall_state",
        fake_capture_state,
    )
    monkeypatch.setattr(
        remediation_factory,
        "enable_windows_firewall",
        fake_enable_firewall,
    )
    monkeypatch.setattr(
        remediation_factory,
        "verify_windows_firewall",
        fake_verify_firewall,
    )
    monkeypatch.setattr(
        remediation_factory,
        "restore_windows_firewall_state",
        fake_restore_state,
    )

    # Recrée la remediation après le monkeypatch.
    remediation = create_remediation_from_finding(finding)

    monkeypatch.setattr(
        remediation,
        "is_admin",
        lambda: True,
    )

    remediation.approve()

    engine = RemediationEngine(remediation)

    result = engine.run()

    # La vérification échoue...
    assert result.success is False

    # ...mais le rollback restaure l'état initial.
    assert engine.state == RemediationEngine.ROLLED_BACK

    assert remediation.previous_state == initial_state

    assert calls == [
        "capture",
        "enable",
        "verify",
        ("restore", initial_state),
    ]
