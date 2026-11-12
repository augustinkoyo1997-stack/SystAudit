import pytest

from src.deployment.baseline import (
    BaselineError,
    BaselinePolicy,
    generate_baseline_script,
)


def test_script_is_simulation_by_default():
    script = generate_baseline_script(BaselinePolicy(computer_name="PC-COMPTA-01"))
    assert "param([switch]$Apply)" in script
    assert "[SIMULATION]" in script
    assert "Rename-Computer -NewName 'PC-COMPTA-01'" in script


def test_script_never_touches_bitlocker_or_passwords():
    script = generate_baseline_script(BaselinePolicy(applications=("7zip.7zip",)))
    lowered = script.lower()
    assert "enable-bitlocker" not in lowered
    assert "net user" not in lowered
    assert "productkey" not in lowered
    assert "winget install --id '7zip.7zip'" in script


@pytest.mark.parametrize(
    "bad_name",
    ["pc; calc", "PC NAME", "a" * 16, "-bad", "pc'name"],
)
def test_invalid_computer_name_is_rejected(bad_name):
    with pytest.raises(BaselineError):
        generate_baseline_script(BaselinePolicy(computer_name=bad_name))


@pytest.mark.parametrize("bad_app", ["x; rm -rf /", "app'id", "a b", "$(calc)", ""])
def test_invalid_application_id_is_rejected(bad_app):
    with pytest.raises(BaselineError):
        generate_baseline_script(BaselinePolicy(applications=(bad_app,)))


def test_password_and_lockout_bounds():
    with pytest.raises(BaselineError):
        generate_baseline_script(BaselinePolicy(min_password_length=4))
    with pytest.raises(BaselineError):
        generate_baseline_script(BaselinePolicy(lockout_threshold=100))
