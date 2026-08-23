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
        interfaces.setdefault(interface_name, [])

        for address in addresses:
            interfaces[interface_name].append({
                "address": address.address,
                "family": str(address.family),
            })

    interface_status = {}

    for interface_name, stats in psutil.net_if_stats().items():
        interface_status[interface_name] = stats.isup
        
    network_stats = psutil.net_io_counters()

    network_stats_data = {
        "bytes_sent": network_stats.bytes_sent,
        "bytes_recv": network_stats.bytes_recv,
        "packets_sent": network_stats.packets_sent,
        "packets_recv": network_stats.packets_recv,
    }

    return {
        "hostname": hostname,
        "ip_address": ip_address,
        "mac_address": mac_address,
        "interfaces": interfaces,
        "interface_status": interface_status,
        "network_stats": network_stats_data,
    }

