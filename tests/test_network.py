from src.network import get_network_info


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