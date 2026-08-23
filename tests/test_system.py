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

def test_partitions_information():
    info = get_system_info()

    assert "partitions" in info
    assert isinstance(info["partitions"], list)

    for partition in info["partitions"]:
        assert isinstance(partition, dict)

        assert "device" in partition
        assert "mountpoint" in partition
        assert "filesystem" in partition
        assert "total" in partition
        assert "used" in partition
        assert "free" in partition
        assert "percent" in partition

        assert isinstance(partition["device"], str)
        assert isinstance(partition["mountpoint"], str)
        assert isinstance(partition["filesystem"], str)
        assert isinstance(partition["total"], int)
        assert isinstance(partition["used"], int)
        assert isinstance(partition["free"], int)
        assert isinstance(partition["percent"], float)

def test_process_information():
    info = get_system_info()

    assert "processes" in info
    assert isinstance(info["processes"], list)

    for process in info["processes"]:
        assert isinstance(process, dict)
        assert "pid" in process
        assert "name" in process
        assert "cpu_percent" in process
        assert "memory_percent" in process

def test_user_information():
    info = get_system_info()

    assert "users" in info
    assert isinstance(info["users"], list)

    for user in info["users"]:
        assert isinstance(user, dict)
        assert "name" in user
        assert "terminal" in user
        assert "host" in user