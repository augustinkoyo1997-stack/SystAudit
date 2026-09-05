from src.remediation import Remediation
from src.firewall_remediation import (
    enable_windows_firewall,
    verify_windows_firewall,
    disable_windows_firewall,
)
def test_firewall_remediation_is_defined_correctly():
    remediation = Remediation(
        id="REM-FIREWALL",
        title="Enable Windows Firewall",
        description="Enable Windows Firewall on all network profiles.",
        severity="high",
        category="firewall",
        requires_admin=True,
        reversible=True,
    )

    assert remediation.id == "REM-FIREWALL"
    assert remediation.category == "firewall"
    assert remediation.requires_admin is True
    assert remediation.reversible is True
    assert remediation.approved is False

def test_firewall_remediation_has_an_action():
    remediation = Remediation(
        id="REM-FIREWALL",
        title="Enable Windows Firewall",
        description="Enable Windows Firewall on all network profiles.",
        severity="high",
        category="firewall",
        action=lambda: True,
        requires_admin=True,
        reversible=True,
    )

    assert remediation.action is not None
    assert remediation.action() is True

from unittest.mock import patch

from src.firewall_remediation import enable_windows_firewall


def test_enable_windows_firewall_runs_expected_command():
    with patch("src.firewall_remediation.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        result = enable_windows_firewall()

    assert result is True

    mock_run.assert_called_once_with(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_verify_windows_firewall_returns_true_when_all_profiles_are_enabled():
    with patch("src.firewall_remediation.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "False\r\n"

        result = verify_windows_firewall()

    assert result is True


from src.remediation_engine import RemediationEngine


def test_firewall_remediation_runs_through_engine():
    remediation = Remediation(
        id="REM-FIREWALL",
        title="Enable Windows Firewall",
        description="Enable Windows Firewall on all network profiles.",
        severity="high",
        category="firewall",
        action=enable_windows_firewall,
        verify_action=verify_windows_firewall,
        requires_admin=True,
        reversible=True,
    )

    with patch("src.firewall_remediation.subprocess.run") as mock_run:
        mock_run.side_effect = [
            type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
            type("Result", (), {"returncode": 0, "stdout": "False\r\n", "stderr": ""})(),
        ]

        remediation.is_admin = lambda: True
        remediation.approve()

        engine = RemediationEngine(remediation)
        result = engine.run()

    assert result.success is True
    assert engine.state == RemediationEngine.VERIFIED
    assert remediation.approved is True

def test_disable_windows_firewall_runs_expected_command():
    with patch("src.firewall_remediation.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        result = disable_windows_firewall()

    assert result is True

    mock_run.assert_called_once_with(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_firewall_remediation_rolls_back_when_verification_fails():
    remediation = Remediation(
        id="REM-FIREWALL",
        title="Enable Windows Firewall",
        description="Enable Windows Firewall on all network profiles.",
        severity="high",
        category="firewall",
        action=enable_windows_firewall,
        verify_action=verify_windows_firewall,
        rollback_action=disable_windows_firewall,
        requires_admin=True,
        reversible=True,
    )

    with patch("src.firewall_remediation.subprocess.run") as mock_run:
        mock_run.side_effect = [
            type(
                "Result",
                (),
                {"returncode": 0, "stdout": "", "stderr": ""},
            )(),
            type(
                "Result",
                (),
                {"returncode": 0, "stdout": "True\r\n", "stderr": ""},
            )(),
            type(
                "Result",
                (),
                {"returncode": 0, "stdout": "", "stderr": ""},
            )(),
        ]

        remediation.is_admin = lambda: True
        remediation.approve()

        engine = RemediationEngine(remediation)
        result = engine.run()

    assert result.success is False
    assert engine.state == RemediationEngine.ROLLED_BACK

    assert [log.status for log in remediation.logs] == [
        "approved",
        "success",
        "failure",
        "success",
    ]
    