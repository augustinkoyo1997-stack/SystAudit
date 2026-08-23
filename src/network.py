import socket
import uuid
import psutil


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
    interfaces = {}

    for interface_name, addresses in psutil.net_if_addrs().items():
        interfaces[interface_name] = []

        for address in addresses:
            interfaces[interface_name].append({
                "address": address.address,
                "family": str(address.family),
            })

    return {
        "hostname": hostname,
        "ip_address": ip_address,
        "mac_address": mac_address,
        "interfaces": interfaces,
    }
