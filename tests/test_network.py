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