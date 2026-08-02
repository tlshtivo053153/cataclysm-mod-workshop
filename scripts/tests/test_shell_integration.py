import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def _run_sh(script, *args):
    result = subprocess.run(
        ["bash", str(SCRIPTS_DIR / script), *args],
        capture_output=True,
        text=True,
        cwd=SCRIPTS_DIR.parent,
    )
    return result


def _run_validate_mods(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "validate_mods.py"), *args],
        capture_output=True,
        text=True,
        cwd=SCRIPTS_DIR.parent,
    )
    return result


class TestValidateSh:
    def test_valid_json_passes(self, tmp_path):
        (tmp_path / "test.json").write_text('{"key": "value"}')
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 0
        assert "All files passed" in result.stdout

    def test_invalid_json_fails(self, tmp_path):
        (tmp_path / "bad.json").write_text("{bad json")
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 1
        assert "NG:" in result.stdout

    def test_zero_json_files_fails(self, tmp_path):
        (tmp_path / "not_json.txt").write_text("hello")
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 1
        assert "No JSON files found" in result.stdout

    def test_mixed_valid_invalid_reports_errors(self, tmp_path):
        (tmp_path / "good.json").write_text('{"a": 1}')
        (tmp_path / "bad.json").write_text("{bad")
        result = _run_sh("validate.sh", str(tmp_path))
        assert result.returncode == 1
        assert "OK:" in result.stdout
        assert "NG:" in result.stdout


class TestValidateMods:
    def test_finds_mods_and_validates(self, tmp_path):
        mod_dir = tmp_path / "test_mod"
        mod_dir.mkdir()
        mod_dir.joinpath("data").mkdir()
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps([{"type": "MOD_INFO", "id": "test_mod", "name": "Test Mod"}]))
        (mod_dir / "data" / "items.json").write_text('{"id": "item1"}')
        (mod_dir / "data" / "recipes.json").write_text('[{"id": "recipe1"}]')

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "All 1 mod(s) passed" in result.stdout

    def test_zero_mods_exits_error(self, tmp_path):
        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "No mod directories found" in result.stderr

    def test_duplicate_mod_id_detected(self, tmp_path):
        for name in ("mod_a", "mod_b"):
            mod_dir = tmp_path / name
            mod_dir.mkdir(parents=True)
            modinfo = mod_dir / "modinfo.json"
            modinfo.write_text(
                json.dumps([{"type": "MOD_INFO", "id": "duplicate_id", "name": name}])
            )

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "Duplicate mod ID" in result.stderr

    def test_missing_modinfo_field_detected(self, tmp_path):
        mod_dir = tmp_path / "bad_mod"
        mod_dir.mkdir(parents=True)
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps([{"type": "MOD_INFO", "id": "bad"}]))

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "missing fields" in result.stderr

    def test_invalid_json_in_mod_detected(self, tmp_path):
        mod_dir = tmp_path / "broken_mod"
        mod_dir.mkdir(parents=True)
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps([{"type": "MOD_INFO", "id": "broken_mod", "name": "Broken"}]))
        (mod_dir / "data.json").write_text("{bad json")

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "NG:" in result.stdout

    def test_nested_mods_found_recursively(self, tmp_path):
        for sub in ("small", "medium"):
            mod_dir = tmp_path / sub / "test_mod"
            mod_dir.mkdir(parents=True)
            modinfo = mod_dir / "modinfo.json"
            modinfo.write_text(json.dumps([{"type": "MOD_INFO", "id": f"mod_{sub}", "name": sub}]))

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "All 2 mod(s) passed" in result.stdout
        assert "test_mod" in result.stdout

    def test_dict_format_modinfo(self, tmp_path):
        mod_dir = tmp_path / "dict_mod"
        mod_dir.mkdir()
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps({"type": "MOD_INFO", "id": "dict_mod", "name": "Dict Mod"}))

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "dict_mod" in result.stdout

    def test_non_modinfo_type_detected(self, tmp_path):
        mod_dir = tmp_path / "bad_type"
        mod_dir.mkdir(parents=True)
        modinfo = mod_dir / "modinfo.json"
        modinfo.write_text(json.dumps([{"type": "RECIPE", "id": "bad", "name": "Bad"}]))

        result = _run_validate_mods("--base-dir", str(tmp_path))
        assert result.returncode == 1
        assert "expected MOD_INFO" in result.stderr

    def test_nonexistent_base_dir(self, tmp_path):
        result = _run_validate_mods("--base-dir", str(tmp_path / "nonexistent"))
        assert result.returncode == 1
        assert "not found" in result.stderr
