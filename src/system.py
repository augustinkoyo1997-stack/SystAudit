import platform
import socket
import psutil


def get_system_info():
    """Return basic information about the current system."""

    memory = psutil.virtual_memory()

    return {
        "hostname": socket.gethostname(),
        "operating_system": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),

        # CPU information
        "cpu_count": psutil.cpu_count(),
        "cpu_usage_percent": psutil.cpu_percent(interval=0.1),

        # RAM information
        "memory_total": memory.total,
        "memory_used": memory.used,
        "memory_percent": memory.percent,
    }


if __name__ == "__main__":
    print(get_system_info())

