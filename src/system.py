import platform
import socket
import psutil


def get_system_info():
    """Return basic information about the current system."""

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    partitions = []

    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)

            partitions.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })

        except (PermissionError, OSError):
            continue

    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            process_info = process.info

            processes.append({
                "pid": process_info["pid"],
                "name": process_info["name"],
                "cpu_percent": process_info["cpu_percent"],
                "memory_percent": process_info["memory_percent"],
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    users = []

    for user in psutil.users():
        users.append({
            "name": user.name,
            "terminal": user.terminal,
            "host": user.host,
        })


    services = []

    for service in psutil.win_service_iter():
        try:
            services.append({
                "name": service.name(),
                "display_name": service.display_name(),
                "status": service.status(),
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError, FileNotFoundError):
            continue

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

        # Disk information
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "disk_percent": disk.percent,
        # Partitions information
        "partitions": partitions,
        # Process information
        "processes": processes,
        # User information
        "users": users,
        # Service information
        "services": services,
    }


if __name__ == "__main__":
    print(get_system_info())

