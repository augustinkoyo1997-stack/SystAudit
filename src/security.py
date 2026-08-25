import ctypes
import json
import platform
import subprocess


def is_administrator():
    """Check whether the current process has administrator/root privileges."""
    if platform.system() == "Windows":
        return bool(ctypes.windll.shell32.IsUserAnAdmin())

    try:
        import os
        return os.geteuid() == 0
    except AttributeError:
        return False


def get_security_info():
    """Return basic security information about the current system."""
    return {
        "operating_system": platform.system(),
        "hostname": platform.node(),
        "administrator": is_administrator(),
    }



def get_local_administrators():
    """Return local members of the Windows Administrators group."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-LocalGroupMember -SID 'S-1-5-32-544' | "
                "Select-Object -ExpandProperty Name",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0:
            return []

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    except (OSError, subprocess.SubprocessError):
        return []
    

def get_local_users():
    """Return local Windows user accounts."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-LocalUser | Select-Object -ExpandProperty Name",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0:
            return []

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    except (OSError, subprocess.SubprocessError):
        return []
    


def get_disabled_users():
    """Return disabled local Windows user accounts."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-LocalUser | "
                "Where-Object {$_.Enabled -eq $false} | "
                "Select-Object -ExpandProperty Name",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0:
            return []

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    except (OSError, subprocess.SubprocessError):
        return []


def get_firewall_status():
    """Return the Windows Firewall status for all network profiles."""
    if platform.system() != "Windows":
        return {}

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetFirewallProfile | "
                "Select-Object Name, Enabled | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if not result.stdout.strip():
            return {}

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        return {
            profile["Name"]: bool(profile["Enabled"])
            for profile in data
            if "Name" in profile and "Enabled" in profile
        }

    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        return {}


def get_antivirus_status():
    """Return the status of installed antivirus products."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance -Namespace root/SecurityCenter2 "
                "-ClassName AntivirusProduct | "
                "Select-Object displayName, productState | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        return [
            {
                "name": antivirus.get("displayName", ""),
                "state": antivirus.get("productState"),
            }
            for antivirus in data
            if antivirus.get("displayName")
        ]

    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        return []


def get_windows_updates():
    """Return recently installed Windows updates."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-HotFix | "
                "Sort-Object InstalledOn -Descending | "
                "Select-Object -First 20 HotFixID, Description, InstalledOn | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        return [
            {
                "id": update.get("HotFixID", ""),
                "description": update.get("Description", ""),
                "installed_on": update.get("InstalledOn"),
            }
            for update in data
            if update.get("HotFixID")
        ]

    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        return []


def get_password_policy():
    """Return the local Windows password and account lockout policy."""
    if platform.system() != "Windows":
        return {}

    try:
        result = subprocess.run(
            ["net", "accounts"],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace",
            check=False,
        )

        policy = {}

        for line in result.stdout.splitlines():
            line = line.strip()

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                policy[key] = value

        return policy

    except (OSError, subprocess.SubprocessError):
        return {}


def get_logged_in_users():
    """Return users currently logged into the Windows system."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            ["quser"],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace",
            check=False,
        )

        if result.returncode != 0:
            return []

        users = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line:
                continue

            if line.lower().startswith("nom_utilisateur"):
                continue

            line = line.lstrip(">")

            parts = line.split()

            if parts:
                username = parts[0]

                if username not in users:
                    users.append(username)

        return users

    except (OSError, subprocess.SubprocessError):
        return []


def get_bitlocker_status():
    """Return BitLocker encryption status for Windows drives."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-BitLockerVolume | "
                "Select-Object MountPoint, VolumeStatus, "
                "ProtectionStatus, EncryptionPercentage | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        return [
            {
                "mount_point": volume.get("MountPoint"),
                "volume_status": volume.get("VolumeStatus"),
                "protection_status": volume.get("ProtectionStatus"),
                "encryption_percentage": volume.get("EncryptionPercentage"),
            }
            for volume in data
            if volume.get("MountPoint")
        ]

    except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        return []




def get_password_never_expires_users():
    """Return local users whose passwords are configured to never expire."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-LocalUser | "
                "Where-Object {$_.PasswordNeverExpires -eq $true} | "
                "Select-Object -ExpandProperty Name",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0:
            return []

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    except (OSError, subprocess.SubprocessError):
        return []


def get_uac_status():
    """Return whether Windows User Account Control (UAC) is enabled."""
    if platform.system() != "Windows":
        return False

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-ItemProperty "
                "-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
                "-Name EnableLUA).EnableLUA",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0:
            return False

        value = result.stdout.strip()

        return value == "1"

    except (OSError, subprocess.SubprocessError):
        return False


def get_firewall_rules():
    """Return enabled Windows Firewall rules."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetFirewallRule | "
                "Where-Object {$_.Enabled -eq 'True'} | "
                "Select-Object DisplayName, Direction, Action, Enabled, Profile | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        direction_map = {
            1: "Inbound",
            2: "Outbound",
        }

        action_map = {
            1: "NotConfigured",
            2: "Allow",
            3: "Block",
        }

        rules = []

        for rule in data:
            if not rule.get("DisplayName"):
                continue

            direction = rule.get("Direction")
            action = rule.get("Action")

            rules.append(
                {
                    "name": rule.get("DisplayName", ""),
                    "direction": direction_map.get(
                        direction, str(direction)
                    ),
                    "action": action_map.get(
                        action, str(action)
                    ),
                    "enabled": bool(rule.get("Enabled")),
                    "profile": str(rule.get("Profile", "")),
                }
            )

        return rules

    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
    ):
        return []


def get_suspicious_services():
    """Return Windows services with potentially suspicious characteristics."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Service | "
                "Select-Object Name, DisplayName, State, StartMode, PathName | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        suspicious = []

        for service in data:
            name = service.get("Name", "")
            display_name = service.get("DisplayName", "")
            state = service.get("State", "")
            start_mode = service.get("StartMode", "")
            path = service.get("PathName") or ""

            reasons = []

            path_lower = path.lower()

            if start_mode.lower() == "auto" and state.lower() == "stopped":
                reasons.append("Automatic service is stopped")

            if not path:
                reasons.append("Missing executable path")

            if "\\temp\\" in path_lower or "\\tmp\\" in path_lower:
                reasons.append("Executable located in temporary directory")

            if path and " " in path and not path.startswith('"'):
                reasons.append("Executable path containing spaces is not quoted")

            if reasons:
                suspicious.append(
                    {
                        "name": name,
                        "display_name": display_name,
                        "status": state,
                        "start_type": start_mode,
                        "path": path,
                        "reason": "; ".join(reasons),
                    }
                )

        return suspicious

    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
    ):
        return []


def get_suspicious_scheduled_tasks():
    """Return Windows scheduled tasks with potentially suspicious characteristics."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-ScheduledTask | "
                "Select-Object TaskName, TaskPath, State, Actions, Principal | "
                "ConvertTo-Json -Compress -Depth 5",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        suspicious = []

        for task in data:
            task_name = task.get("TaskName", "")
            task_path = task.get("TaskPath", "")
            state = task.get("State", "")

            reasons = []
            action_path = ""

            actions = task.get("Actions")

            if isinstance(actions, dict):
                action_path = actions.get("Execute", "") or ""
            elif isinstance(actions, list):
                for action in actions:
                    if isinstance(action, dict) and action.get("Execute"):
                        action_path = action["Execute"]
                        break

            path_lower = action_path.lower()

            if "\\temp\\" in path_lower or "\\tmp\\" in path_lower:
                reasons.append("Executable located in temporary directory")

            if "\\appdata\\" in path_lower:
                reasons.append("Executable located in AppData")

            if action_path and " " in action_path and not action_path.startswith('"'):
                reasons.append("Executable path containing spaces is not quoted")

            principal = task.get("Principal")

            if isinstance(principal, dict):
                run_level = principal.get("RunLevel", "")

                if str(run_level).lower() == "highest":
                    reasons.append("Task configured with highest privileges")

            if reasons:
                suspicious.append(
                    {
                        "name": task_name,
                        "path": task_path,
                        "state": str(state),
                        "action": str(action_path),
                        "reason": "; ".join(reasons),
                    }
                )

        return suspicious

    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
    ):
        return []


def get_suspicious_processes():
    """Return Windows processes with potentially suspicious characteristics."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process | "
                "Select-Object ProcessId, Name, ExecutablePath, CommandLine | "
                "ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        data = json.loads(result.stdout)

        if isinstance(data, dict):
            data = [data]

        suspicious = []

        for process in data:
            name = process.get("Name", "") or ""
            executable_path = process.get("ExecutablePath") or ""
            command_line = process.get("CommandLine") or ""

            reasons = []
            path_lower = executable_path.lower()

            if "\\temp\\" in path_lower or "\\tmp\\" in path_lower:
                reasons.append("Executable located in temporary directory")

            if "\\appdata\\" in path_lower:
                reasons.append("Executable located in AppData")

            if not executable_path:
                reasons.append("Executable path unavailable")

            if command_line and "powershell" in command_line.lower():
                reasons.append("PowerShell command detected")

            if command_line and " -enc " in command_line.lower():
                reasons.append("Encoded PowerShell command detected")

            if reasons:
                suspicious.append(
                    {
                        "pid": process.get("ProcessId"),
                        "name": name,
                        "path": executable_path,
                        "command_line": command_line,
                        "reason": "; ".join(reasons),
                    }
                )

        return suspicious

    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
    ):
        return []
    