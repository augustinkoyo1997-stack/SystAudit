from src.network import get_network_info


def test_get_network_info():
    info = get_network_info()

    assert isinstance(info, dict)
    assert "hostname" in info
    assert "ip_address" in info
    assert isinstance(info["hostname"], str)
    assert isinstance(info["ip_address"], str)