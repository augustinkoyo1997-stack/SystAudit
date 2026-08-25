import ctypes
import platform


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