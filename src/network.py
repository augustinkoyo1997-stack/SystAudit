import socket


def get_network_info():
    """Return basic network information about the current system."""
    hostname = socket.gethostname()

    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        ip_address = "Unknown"

    return {
        "hostname": hostname,
        "ip_address": ip_address,
    }