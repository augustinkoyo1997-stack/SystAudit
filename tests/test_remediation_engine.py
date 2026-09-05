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
    