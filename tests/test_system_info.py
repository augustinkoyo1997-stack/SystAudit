def test_import_system_info():
    import sys
    sys.path.insert(0,"src")
    import system
    assert system is not None