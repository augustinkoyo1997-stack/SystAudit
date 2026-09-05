from src.remediation_factory import create_remediation_from_finding
from src.remediation_engine import RemediationEngine


def test_security_finding_creates_controlled_remediation():
    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    assert remediation.category == "firewall"
    assert remediation.severity == "high"
    assert remediation.requires_admin is True
    assert remediation.reversible is True

    engine = RemediationEngine(remediation)

    assert engine.state == RemediationEngine.PROPOSED
    assert remediation.approved is False

def test_remediation_requires_explicit_approval_before_execution():
    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)
    engine = RemediationEngine(remediation)

    assert remediation.approved is False

    try:
        engine.run()
        assert False, "Execution should require explicit approval."
    except PermissionError:
        pass

    assert engine.state == RemediationEngine.PROPOSED

def test_approved_remediation_executes_and_is_verified():
    execution = []
    verification = []

    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    remediation.action = lambda: execution.append("executed") or True
    remediation.verify_action = lambda: verification.append("verified") or True

    remediation.approve()

    engine = RemediationEngine(remediation)

    result = engine.run()

    assert result.success is True
    assert execution == ["executed"]
    assert verification == ["verified"]

    assert remediation.approved is True
    assert engine.state == RemediationEngine.VERIFIED

def test_failed_verification_triggers_rollback():
    execution = []
    rollback = []

    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    remediation.action = lambda: execution.append("executed") or True
    remediation.verify_action = lambda: False
    remediation.rollback_action = lambda: rollback.append("rolled_back") or True

    remediation.approve()

    engine = RemediationEngine(remediation)

    result = engine.run()

    assert result.success is False
    assert execution == ["executed"]
    assert rollback == ["rolled_back"]

    assert engine.state == RemediationEngine.ROLLED_BACK


def test_remediation_workflow_creates_audit_logs():
    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    remediation.action = lambda: True
    remediation.verify_action = lambda: True

    remediation.approve()

    engine = RemediationEngine(remediation)
    result = engine.run()

    assert result.success is True

    statuses = [log.status for log in remediation.logs]

    assert "approved" in statuses
    assert "success" in statuses

def test_failed_execution_is_recorded_and_stops_workflow():
    finding = {
        "risk": "high",
        "category": "firewall",
        "message": "Windows Firewall is disabled.",
    }

    remediation = create_remediation_from_finding(finding)

    remediation.action = lambda: False
    remediation.verify_action = lambda: True

    remediation.approve()

    engine = RemediationEngine(remediation)

    result = engine.run()

    assert result.success is False
    assert engine.state == RemediationEngine.EXECUTION_FAILED

    statuses = [log.status for log in remediation.logs]

    assert "approved" in statuses
    assert "failure" in statuses
    