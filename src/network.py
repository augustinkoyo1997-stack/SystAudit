import socket
import uuid


def get_network_info():
    """Return basic network information about the current system."""
    hostname = socket.gethostname()

    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        ip_address = "Unknown"

    mac_address = ":".join(
        f"{byte:02x}" for byte in uuid.getnode().to_bytes(6, "big")
    )

    return {
        "hostname": hostname,
        "ip_address": ip_address,
        "mac_address": mac_address,
    }