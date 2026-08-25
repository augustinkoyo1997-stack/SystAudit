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