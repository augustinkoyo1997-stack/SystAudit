import socket
import uuid
import psutil


def get_network_info():
    """Return basic network information about the current system."""
    hostname = socket.gethostname()
    routes = get_network_routes()

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
                "netmask": address.netmask,
                "broadcast": address.broadcast,
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
        "routes": routes,
    }

def get_network_connections():
    """Return active network connections and listening ports."""
    connections = []

    for connection in psutil.net_connections(kind="inet"):
        local_address = None
        remote_address = None

        if connection.laddr:
            local_address = {
                "ip": connection.laddr.ip,
                "port": connection.laddr.port,
            }

        if connection.raddr:
            remote_address = {
                "ip": connection.raddr.ip,
                "port": connection.raddr.port,
            }

        connections.append({
            "family": str(connection.family),
            "type": str(connection.type),
            "local_address": local_address,
            "remote_address": remote_address,
            "status": connection.status,
            "pid": connection.pid,
        })

    return connections

def get_network_routes():
    """Return the IPv4 routing table on Windows."""
    import subprocess

    routes = []

    try:
        result = subprocess.run(
            ["route", "print", "-4"],
            capture_output=True,
            text=True,
            encoding="cp850",
            errors="replace",
            check=False,
        )

        in_active_routes = False

        for line in result.stdout.splitlines():
            line = line.strip()

            if line.startswith("Itinéraires actifs"):
                in_active_routes = True
                continue

            if not in_active_routes or not line:
                continue

            parts = line.split()

            # Ignore headers and invalid lines
            if len(parts) < 5:
                continue

            destination = parts[0]
            netmask = parts[1]
            gateway = parts[2]
            interface = parts[3]

            try:
                metric = int(parts[4])
            except ValueError:
                continue

            if (
                destination.count(".") == 3
                and netmask.count(".") == 3
            ):
                routes.append({
                    "destination": destination,
                    "netmask": netmask,
                    "gateway": gateway,
                    "interface": interface,
                    "metric": metric,
                })

    except (OSError, subprocess.SubprocessError):
        return []

    return routes

def _get_address_family(address_family):
    """Return a human-readable network address family."""
    family = str(address_family)

    if family == "-1":
        return "MAC"
    if family == "2":
        return "IPv4"
    if family == "23":
        return "IPv6"

    return family


def get_network_interfaces():
    """Return detailed information about network interfaces."""
    interfaces = {}

    addresses = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for interface_name, interface_addresses in addresses.items():
        interface_stats = stats.get(interface_name)

        interfaces[interface_name] = {
            "is_up": interface_stats.isup if interface_stats else False,
            "speed": interface_stats.speed if interface_stats else 0,
            "mtu": interface_stats.mtu if interface_stats else 0,
            "addresses": [],
        }

        for address in interface_addresses:
            interfaces[interface_name]["addresses"].append({
                "address": address.address,
                "family": _get_address_family(address.family),
                "netmask": address.netmask,
                "broadcast": address.broadcast,
            })

    return interfaces