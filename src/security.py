import ctypes
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
            ["net", "localgroup", "Administrators"],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace",
            check=False,
        )

        administrators = []
        collecting = False

        for line in result.stdout.splitlines():
            line = line.strip()

            if line.startswith("---"):
                collecting = True
                continue

            if collecting:
                if line.lower().startswith("the command"):
                    break

                if line:
                    administrators.append(line)

        return administrators

    except (OSError, subprocess.SubprocessError):
        return []
    


def get_local_users():
    """Return local Windows user accounts."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            ["net", "user"],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace",
            check=False,
        )

        users = []
        collecting = False

        for line in result.stdout.splitlines():
            line = line.strip()

            if line.startswith("---"):
                collecting = True
                continue

            if collecting:
                if line.lower().startswith("the command"):
                    break

                if line:
                    users.extend(line.split())

        return users

    except (OSError, subprocess.SubprocessError):
        return []


def get_disabled_users():
    """Return disabled local Windows user accounts."""
    if platform.system() != "Windows":
        return []

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-LocalUser | Where-Object {$_.Enabled -eq $false} | Select-Object -ExpandProperty Name"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

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

        import json

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

        import json

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
