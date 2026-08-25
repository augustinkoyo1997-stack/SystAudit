from src.network import get_network_info, get_network_connections


def test_get_network_info():
    info = get_network_info()

    assert isinstance(info, dict)
    assert "hostname" in info
    assert "ip_address" in info
    assert isinstance(info["hostname"], str)
    assert isinstance(info["ip_address"], str)
    assert "mac_address" in info


def test_get_network_interfaces():
    info = get_network_info()

    assert "interfaces" in info
    assert isinstance(info["interfaces"], dict)

    for interface_name, interface_data in info["interfaces"].items():
        assert isinstance(interface_name, str)
        assert isinstance(interface_data, list)


def test_network_interface_status():
    info = get_network_info()

    assert "interface_status" in info
    assert isinstance(info["interface_status"], dict)


def test_network_stats():
    info = get_network_info()

    assert "network_stats" in info
    assert isinstance(info["network_stats"], dict)

    assert "bytes_sent" in info["network_stats"]
    assert "bytes_recv" in info["network_stats"]
    assert "packets_sent" in info["network_stats"]
    assert "packets_recv" in info["network_stats"]

def test_network_interface_addresses():
    info = get_network_info()

    assert "interfaces" in info

    for interface_name, interface_data in info["interfaces"].items():
        assert isinstance(interface_name, str)
        assert isinstance(interface_data, list)

        for address in interface_data:
            assert isinstance(address, dict)
            assert "address" in address
            assert "family" in address
            assert "netmask" in address
            assert "broadcast" in address

def test_network_connections():
    connections = get_network_connections()

    assert isinstance(connections, list)

    for connection in connections:
        assert isinstance(connection, dict)
        assert "family" in connection
        assert "type" in connection
        assert "local_address" in connection
        assert "remote_address" in connection
        assert "status" in connection
        assert "pid" in connection

def test_network_routes():
    """Test network routing table information."""
    from src.network import get_network_routes

    routes = get_network_routes()

    assert isinstance(routes, list)

    for route in routes:
        assert isinstance(route, dict)
        assert "destination" in route
        assert "netmask" in route
        assert "gateway" in route
        assert "interface" in route
        assert "metric" in route

        assert isinstance(route["destination"], str)
        assert isinstance(route["netmask"], str)
        assert isinstance(route["gateway"], str)
        assert isinstance(route["interface"], str)
        assert isinstance(route["metric"], int)

def test_network_interface_details():
    """Test detailed network interface information."""
    from src.network import get_network_interfaces

    interfaces = get_network_interfaces()

    assert isinstance(interfaces, dict)

    for interface_name, interface_data in interfaces.items():
        assert isinstance(interface_name, str)
        assert isinstance(interface_data, dict)

        assert "is_up" in interface_data
        assert "speed" in interface_data
        assert "mtu" in interface_data
        assert "addresses" in interface_data

        assert isinstance(interface_data["is_up"], bool)
        assert isinstance(interface_data["speed"], int)
        assert isinstance(interface_data["mtu"], int)
        assert isinstance(interface_data["addresses"], list)

def test_network_interface_address_families():
    """Test human-readable network address families."""
    from src.network import get_network_interfaces

    interfaces = get_network_interfaces()

    valid_families = {"MAC", "IPv4", "IPv6"}

    for interface_data in interfaces.values():
        for address in interface_data["addresses"]:
            assert address["family"] in valid_families

def test_network_connection_process_name():
    """Test that network connections include process information."""
    from src.network import get_network_connections

    connections = get_network_connections()

    assert isinstance(connections, list)

    for connection in connections:
        assert "pid" in connection
        assert "process_name" in connection

        assert connection["pid"] is None or isinstance(
            connection["pid"], int
        )

        assert connection["process_name"] is None or isinstance(
            connection["process_name"], str
        )


def test_get_listening_ports():
    from src.network import get_listening_ports

    result = get_listening_ports()

    assert isinstance(result, list)

    for port in result:
        assert isinstance(port, dict)
        assert "local_address" in port
        assert "port" in port
        assert "protocol" in port
        assert "pid" in port

        assert isinstance(port["local_address"], str)
        assert isinstance(port["port"], int)
        assert port["protocol"] == "TCP"
        assert port["pid"] is None or isinstance(port["pid"], int)



def test_get_network_processes():
    from src.network import get_network_processes

    result = get_network_processes()

    assert isinstance(result, list)

    for connection in result:
        assert isinstance(connection, dict)

        assert "local_address" in connection
        assert "local_port" in connection
        assert "remote_address" in connection
        assert "remote_port" in connection
        assert "status" in connection
        assert "pid" in connection
        assert "process_name" in connection

        assert isinstance(connection["local_address"], str)
        assert isinstance(connection["local_port"], int)
        assert connection["pid"] is None or isinstance(connection["pid"], int)
        assert (
            connection["process_name"] is None
            or isinstance(connection["process_name"], str)
        )
