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


def test_get_bitlocker_status():
    result = get_bitlocker_status()

    assert isinstance(result, list)

    for volume in result:
        assert isinstance(volume, dict)
        assert "mount_point" in volume
        assert "volume_status" in volume
        assert "protection_status" in volume
        assert "encryption_percentage" in volume

        assert isinstance(volume["mount_point"], str)


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
    