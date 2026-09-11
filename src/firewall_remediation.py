import subprocess
import json

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

def get_windows_firewall_state():
    """Return the enabled state of each Windows Firewall profile."""

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-NetFirewallProfile "
                "-Profile Domain,Public,Private | "
                "Select-Object Name,Enabled | "
                "ConvertTo-Json -Compress"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        return {
            item["Name"]: bool(item["Enabled"])
            for item in data
            if "Name" in item and "Enabled" in item
        }

    except (json.JSONDecodeError, TypeError, KeyError):
        return None

def restore_windows_firewall_state(state):
    """Restore the Windows Firewall state for all network profiles."""

    if not isinstance(state, dict):
        return False

    required_profiles = {"Domain", "Public", "Private"}

    if set(state.keys()) != required_profiles:
        return False

    if not all(isinstance(value, bool) for value in state.values()):
        return False

    commands = []

    for profile, enabled in state.items():
        value = "True" if enabled else "False"

        commands.append(
            f"Set-NetFirewallProfile -Profile {profile} -Enabled {value}"
        )

    powershell_command = "; ".join(commands)

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            powershell_command,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0
