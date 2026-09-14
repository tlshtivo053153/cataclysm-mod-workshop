# B-2: no sys.path hack here. Test imports resolve via
# [tool.pytest.ini_options] pythonpath = ["scripts"] in pyproject.toml,
# which puts scripts/ (common.py + mapgen/) on sys.path for pytest runs.
