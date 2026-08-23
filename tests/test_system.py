from src.system import get_system_info
def test_get_system_info():
  info =get_system_info()
  assert isinstance(info,dict)
  assert "hostname" in info
  assert "operating_system" in info
  assert "os_release" in info
  assert "architecture" in info
  assert "python_version" in info