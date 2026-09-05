import subprocess


def enable_windows_firewall():
    """Enable Windows Firewall on all network profiles."""

    result = subprocess.run(
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

    return result.returncode == 0


def verify_windows_firewall():
    """Verify that Windows Firewall is enabled on all profiles."""

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-NetFirewallProfile -Profile Domain,Public,Private).Enabled -contains $false",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return False

    return result.stdout.strip().lower() == "false"

def disable_windows_firewall():
    """Disable Windows Firewall on all network profiles."""

    result = subprocess.run(
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

    return result.returncode == 0
