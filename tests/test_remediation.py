import pytest
from datetime import datetime, timezone

from src.remediation import (
    Remediation,
    RemediationResult,
    RemediationLog,
)

def test_remediation_creation():
    remediation = Remediation(
        id="TEST-001",
        title="Test remediation",
        description="Test description",
        severity="medium",
        category="system",
    )

    assert remediation.id == "TEST-001"
    assert remediation.title == "Test remediation"
    assert remediation.severity == "medium"
    assert remediation.category == "system"
    assert remediation.requires_admin is False
    assert remediation.reversible is False
    assert remediation.approved is False


def test_remediation_execute_requires_approval():
    executed = []

    def action():
        executed.append(True)
        return True

    remediation = Remediation(
        id="TEST-002",
        title="Protected remediation",
        description="Test approval requirement",
        severity="high",
        category="security",
        action=action,
    )

    with pytest.raises(PermissionError):
        remediation.execute()

    assert executed == []


def test_remediation_execute_after_approval():
    executed = []

    def action():
        executed.append(True)
        return True

    remediation = Remediation(
        id="TEST-003",
        title="Approved remediation",
        description="Test approved action",
        severity="medium",
        category="system",
        action=action,
    )

    remediation.approve()

    assert remediation.approved is True

    result = remediation.execute()

    assert isinstance(result, RemediationResult)
    assert result.remediation_id == "TEST-003"
    assert result.success is True
    assert executed == [True]


def test_remediation_revoke_approval():
    remediation = Remediation(
        id="TEST-004",
        title="Revocable remediation",
        description="Test approval revocation",
        severity="low",
        category="system",
        action=lambda: True,
    )

    remediation.approve()
    assert remediation.approved is True

    remediation.revoke_approval()
    assert remediation.approved is False

    with pytest.raises(PermissionError):
        remediation.execute()


def test_remediation_without_action():
    remediation = Remediation(
        id="TEST-005",
        title="No action",
        description="Remediation without action",
        severity="low",
        category="system",
    )

    remediation.approve()

    with pytest.raises(RuntimeError):
        remediation.execute()


def test_success_result():
    result = RemediationResult.success_result(
        "TEST-006",
        "Test successful remediation.",
    )

    assert result.remediation_id == "TEST-006"
    assert result.success is True
    assert result.message == "Test successful remediation."
    assert isinstance(result.executed_at, datetime)
    assert result.executed_at.tzinfo == timezone.utc


def test_failure_result():
    result = RemediationResult.failure_result(
        "TEST-007",
        "Test remediation failed.",
    )

    assert result.remediation_id == "TEST-007"
    assert result.success is False
    assert result.message == "Test remediation failed."
    assert isinstance(result.executed_at, datetime)
    assert result.executed_at.tzinfo == timezone.utc


def test_execute_returns_success_result():
    remediation = Remediation(
        id="TEST-008",
        title="Successful remediation",
        description="Test result integration",
        severity="medium",
        category="system",
        action=lambda: True,
    )

    remediation.approve()

    result = remediation.execute()

    assert isinstance(result, RemediationResult)
    assert result.remediation_id == "TEST-008"
    assert result.success is True


def test_execute_returns_failure_result():
    remediation = Remediation(
        id="TEST-009",
        title="Failed remediation",
        description="Test failure result integration",
        severity="high",
        category="security",
        action=lambda: False,
    )

    remediation.approve()

    result = remediation.execute()

    assert isinstance(result, RemediationResult)
    assert result.remediation_id == "TEST-009"
    assert result.success is False

def test_preconditions_satisfied_with_action():
    remediation = Remediation(
        id="TEST-010",
        title="Valid remediation",
        description="Remediation with an action",
        severity="medium",
        category="system",
        action=lambda: True,
    )

    assert remediation.check_preconditions() is True


def test_preconditions_fail_without_action():
    remediation = Remediation(
        id="TEST-011",
        title="Invalid remediation",
        description="Remediation without an action",
        severity="medium",
        category="system",
    )

    assert remediation.check_preconditions() is False


def test_execute_rejects_failed_preconditions():
    remediation = Remediation(
        id="TEST-012",
        title="Invalid remediation",
        description="Remediation without an action",
        severity="high",
        category="security",
    )

    remediation.approve()

    with pytest.raises(RuntimeError):
        remediation.execute()

def test_is_admin_returns_boolean():
    remediation = Remediation(
        id="TEST-013",
        title="Admin check",
        description="Test administrator detection",
        severity="high",
        category="security",
    )

    result = remediation.is_admin()

    assert isinstance(result, bool)


def test_requires_admin_is_false_by_default():
    remediation = Remediation(
        id="TEST-014",
        title="No admin required",
        description="Test default admin requirement",
        severity="low",
        category="system",
    )

    assert remediation.requires_admin is False


def test_admin_required_blocks_non_admin(monkeypatch):
    remediation = Remediation(
        id="TEST-015",
        title="Admin remediation",
        description="Test admin requirement",
        severity="high",
        category="security",
        action=lambda: True,
        requires_admin=True,
    )

    remediation.approve()

    monkeypatch.setattr(
        remediation,
        "is_admin",
        lambda: False,
    )

    with pytest.raises(PermissionError):
        remediation.execute()


def test_admin_required_allows_admin(monkeypatch):
    executed = []

    def action():
        executed.append(True)
        return True

    remediation = Remediation(
        id="TEST-016",
        title="Admin remediation",
        description="Test administrator execution",
        severity="high",
        category="security",
        action=action,
        requires_admin=True,
    )

    remediation.approve()

    monkeypatch.setattr(
        remediation,
        "is_admin",
        lambda: True,
    )

    result = remediation.execute()

    assert isinstance(result, RemediationResult)
    assert result.success is True
    assert executed == [True]

def test_remediation_log_creation():
    log = RemediationLog(
        remediation_id="TEST-017",
        status="approved",
        message="Remediation approved.",
    )

    assert log.remediation_id == "TEST-017"
    assert log.status == "approved"
    assert log.message == "Remediation approved."
    assert isinstance(log.created_at, datetime)
    assert log.created_at.tzinfo == timezone.utc


def test_remediation_log_success():
    log = RemediationLog.success(
        remediation_id="TEST-018",
        message="Remediation completed.",
    )

    assert log.remediation_id == "TEST-018"
    assert log.status == "success"
    assert log.message == "Remediation completed."


def test_remediation_log_failure():
    log = RemediationLog.failure(
        remediation_id="TEST-019",
        message="Remediation failed.",
    )

    assert log.remediation_id == "TEST-019"
    assert log.status == "failure"
    assert log.message == "Remediation failed."


def test_remediation_log_approval():
    log = RemediationLog.approval(
        remediation_id="TEST-020",
    )

    assert log.remediation_id == "TEST-020"
    assert log.status == "approved"
    assert log.message == "Remediation approved."

def test_remediation_has_empty_logs_by_default():
    remediation = Remediation(
        id="TEST-021",
        title="Log test",
        description="Test default logs",
        severity="low",
        category="system",
    )

    assert remediation.logs == []


def test_approve_creates_approval_log():
    remediation = Remediation(
        id="TEST-022",
        title="Approval logging",
        description="Test approval log",
        severity="medium",
        category="security",
    )

    remediation.approve()

    assert len(remediation.logs) == 1
    assert remediation.logs[0].remediation_id == "TEST-022"
    assert remediation.logs[0].status == "approved"


def test_execute_creates_success_log():
    remediation = Remediation(
        id="TEST-023",
        title="Success logging",
        description="Test success log",
        severity="medium",
        category="system",
        action=lambda: True,
    )

    remediation.approve()
    result = remediation.execute()

    assert result.success is True
    assert len(remediation.logs) == 2
    assert remediation.logs[0].status == "approved"
    assert remediation.logs[1].status == "success"


def test_execute_creates_failure_log():
    remediation = Remediation(
        id="TEST-024",
        title="Failure logging",
        description="Test failure log",
        severity="high",
        category="security",
        action=lambda: False,
    )

    remediation.approve()
    result = remediation.execute()

    assert result.success is False
    assert len(remediation.logs) == 2
    assert remediation.logs[0].status == "approved"
    assert remediation.logs[1].status == "failure"

def test_rollback_requires_approval():
    remediation = Remediation(
        id="TEST-025",
        title="Rollback test",
        description="Test approval requirement for rollback",
        severity="high",
        category="security",
        reversible=True,
        action=lambda: True,
        rollback_action=lambda: True,
    )

    with pytest.raises(PermissionError):
        remediation.rollback()


def test_rollback_requires_reversible_remediation():
    remediation = Remediation(
        id="TEST-026",
        title="Non reversible remediation",
        description="Test reversible requirement",
        severity="medium",
        category="system",
        action=lambda: True,
        reversible=False,
        rollback_action=lambda: True,
    )

    remediation.approve()

    with pytest.raises(RuntimeError):
        remediation.rollback()


def test_rollback_executes_successfully():
    rollback_executed = []

    def rollback_action():
        rollback_executed.append(True)
        return True

    remediation = Remediation(
        id="TEST-027",
        title="Reversible remediation",
        description="Test successful rollback",
        severity="high",
        category="security",
        action=lambda: True,
        reversible=True,
        rollback_action=rollback_action,
    )

    remediation.approve()
    remediation.execute()

    result = remediation.rollback()

    assert isinstance(result, RemediationResult)
    assert result.remediation_id == "TEST-027"
    assert result.success is True
    assert rollback_executed == [True]


def test_rollback_failure_returns_failure_result():
    remediation = Remediation(
        id="TEST-028",
        title="Failed rollback",
        description="Test failed rollback",
        severity="high",
        category="security",
        action=lambda: True,
        reversible=True,
        rollback_action=lambda: False,
    )

    remediation.approve()
    remediation.execute()

    result = remediation.rollback()

    assert isinstance(result, RemediationResult)
    assert result.remediation_id == "TEST-028"
    assert result.success is False

def test_verify_requires_approval():
    remediation = Remediation(
        id="TEST-029",
        title="Verification test",
        description="Test verification approval requirement",
        severity="high",
        category="security",
        action=lambda: True,
        reversible=True,
        rollback_action=lambda: True,
        verify_action=lambda: True,
    )

    with pytest.raises(PermissionError):
        remediation.verify()


def test_verify_requires_verify_action():
    remediation = Remediation(
        id="TEST-030",
        title="Missing verification",
        description="Test missing verification action",
        severity="medium",
        category="system",
        action=lambda: True,
    )

    remediation.approve()

    with pytest.raises(RuntimeError):
        remediation.verify()


def test_verify_returns_success_result():
    remediation = Remediation(
        id="TEST-031",
        title="Successful verification",
        description="Test successful verification",
        severity="medium",
        category="system",
        action=lambda: True,
        verify_action=lambda: True,
    )

    remediation.approve()
    remediation.execute()

    result = remediation.verify()

    assert isinstance(result, RemediationResult)
    assert result.remediation_id == "TEST-031"
    assert result.success is True


def test_verify_returns_failure_result():
    remediation = Remediation(
        id="TEST-032",
        title="Failed verification",
        description="Test failed verification",
        severity="high",
        category="security",
        action=lambda: True,
        verify_action=lambda: False,
    )

    remediation.approve()
    remediation.execute()

    result = remediation.verify()

    assert isinstance(result, RemediationResult)
    assert result.remediation_id == "TEST-032"
    assert result.success is False
    