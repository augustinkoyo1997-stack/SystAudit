from src.system import get_system_info


def test_get_system_info():
  info =get_system_info()
  assert isinstance(info,dict)
  assert "hostname" in info
  assert "operating_system" in info
  assert "os_release" in info
  assert "architecture" in info
  assert "python_version" in info

def test_cpu_information():
    info = get_system_info()

    assert "cpu_count" in info
    assert "cpu_usage_percent" in info

    assert isinstance(info["cpu_count"], int)
    assert isinstance(info["cpu_usage_percent"], float)


def test_memory_information():
    info = get_system_info()

    assert "memory_total" in info
    assert "memory_used" in info
    assert "memory_percent" in info

    assert isinstance(info["memory_total"], int)
    assert isinstance(info["memory_used"], int)
    assert isinstance(info["memory_percent"], float)

def test_disk_information():
    info = get_system_info()

    assert "disk_total" in info
    assert "disk_used" in info
    assert "disk_free" in info
    assert "disk_percent" in info

    assert isinstance(info["disk_total"], int)
    assert isinstance(info["disk_used"], int)
    assert isinstance(info["disk_free"], int)
    assert isinstance(info["disk_percent"], float)
