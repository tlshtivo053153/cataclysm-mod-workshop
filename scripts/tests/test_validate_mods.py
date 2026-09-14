"""Unit tests for validate_mods.py Level1 content rules (C-1).

Covers CORE.md-derived checks beyond JSON syntax:
- recipe `activity_level` required (ERROR)
- modinfo `dependencies` must include `dda` (ERROR)
- `copy-from` target not defined in-mod (WARNING only)
"""

import json
import subprocess

import validate_mods
from validate_mods import (
    check_copy_from_references,
    check_modinfo_dependencies,
    check_recipe_activity_level,
    run_validate,
)


def _write_mod(tmp_path, name="mymod", files=None):
    mod_dir = tmp_path / name
    mod_dir.mkdir(parents=True, exist_ok=True)
    (mod_dir / "modinfo.json").write_text(
        json.dumps([{"type": "MOD_INFO", "id": name, "name": name}])
    )
    for rel, data in (files or {}).items():
        p = mod_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data))
    return mod_dir


class TestRecipeActivityLevel:
    def test_valid_recipe_passes(self, tmp_path):
        mod_dir = _write_mod(
            tmp_path,
            files={
                "recipes.json": [
                    {"type": "recipe", "result": "x", "activity_level": "LIGHT_EXERCISE"}
                ]
            },
        )
        assert check_recipe_activity_level(mod_dir) == []

    def test_missing_activity_level_detected(self, tmp_path):
        mod_dir = _write_mod(
            tmp_path, files={"recipes.json": [{"type": "recipe", "result": "my_item"}]}
        )
        errors = check_recipe_activity_level(mod_dir)
        assert len(errors) == 1
        assert "my_item" in errors[0]
        assert "activity_level" in errors[0]

    def test_empty_activity_level_detected(self, tmp_path):
        mod_dir = _write_mod(
            tmp_path,
            files={"recipes.json": [{"type": "recipe", "result": "x", "activity_level": ""}]},
        )
        assert len(check_recipe_activity_level(mod_dir)) == 1

    def test_non_recipe_ignored(self, tmp_path):
        mod_dir = _write_mod(tmp_path, files={"items.json": [{"type": "ITEM", "id": "my_item"}]})
        assert check_recipe_activity_level(mod_dir) == []

    def test_bak_recipe_ignored(self, tmp_path):
        mod_dir = _write_mod(tmp_path)
        bak = mod_dir / ".bak"
        bak.mkdir()
        (bak / "recipes.json").write_text(json.dumps([{"type": "recipe", "result": "x"}]))
        assert check_recipe_activity_level(mod_dir) == []

    def test_invalid_json_skipped(self, tmp_path):
        mod_dir = _write_mod(tmp_path)
        (mod_dir / "broken.json").write_text("{bad")
        assert check_recipe_activity_level(mod_dir) == []


class TestModinfoDependencies:
    def test_dda_dependency_passes(self, tmp_path):
        mod_dir = _write_mod(tmp_path)
        (mod_dir / "modinfo.json").write_text(
            json.dumps([{"type": "MOD_INFO", "id": "m", "name": "M", "dependencies": ["dda"]}])
        )
        assert check_modinfo_dependencies(mod_dir) == []

    def test_missing_dependencies_detected(self, tmp_path):
        mod_dir = _write_mod(tmp_path)
        assert len(check_modinfo_dependencies(mod_dir)) == 1

    def test_missing_dda_detected(self, tmp_path):
        mod_dir = _write_mod(tmp_path)
        (mod_dir / "modinfo.json").write_text(
            json.dumps([{"type": "MOD_INFO", "id": "m", "name": "M", "dependencies": ["other"]}])
        )
        errors = check_modinfo_dependencies(mod_dir)
        assert len(errors) == 1
        assert "dda" in errors[0]

    def test_unparseable_modinfo_skipped(self, tmp_path):
        mod_dir = _write_mod(tmp_path)
        (mod_dir / "modinfo.json").write_text("{bad")
        assert check_modinfo_dependencies(mod_dir) == []

    def test_non_dict_entry_skipped(self, tmp_path):
        import json as _json

        d = tmp_path / "nd"
        d.mkdir()
        (d / "modinfo.json").write_text(_json.dumps(["just-a-string"]))
        assert check_modinfo_dependencies(d) == []


class TestCopyFromReferences:
    def test_local_target_passes(self, tmp_path):
        mod_dir = _write_mod(
            tmp_path,
            files={
                "items.json": [
                    {"type": "ITEM", "id": "base_item"},
                    {"type": "ITEM", "id": "child", "copy-from": "base_item"},
                ]
            },
        )
        assert check_copy_from_references(mod_dir) == []

    def test_vanilla_target_warns(self, tmp_path):
        mod_dir = _write_mod(
            tmp_path,
            files={"items.json": [{"type": "ITEM", "id": "child", "copy-from": "crowbar"}]},
        )
        warnings = check_copy_from_references(mod_dir)
        assert len(warnings) == 1
        assert "crowbar" in warnings[0]

    def test_no_copy_from_no_warning(self, tmp_path):
        mod_dir = _write_mod(tmp_path, files={"items.json": [{"type": "ITEM", "id": "plain"}]})
        assert check_copy_from_references(mod_dir) == []


class TestRunValidateErrorCapture:
    def test_missing_script_returns_false(self, tmp_path, monkeypatch, capsys):
        def boom(*a, **k):
            raise FileNotFoundError("no bash")

        monkeypatch.setattr(subprocess, "run", boom)
        assert run_validate(tmp_path) is False
        assert "not found" in capsys.readouterr().err

    def test_timeout_returns_false(self, tmp_path, monkeypatch, capsys):
        def boom(*a, **k):
            raise subprocess.TimeoutExpired(cmd="bash", timeout=120)

        monkeypatch.setattr(subprocess, "run", boom)
        assert run_validate(tmp_path) is False
        assert "timed out" in capsys.readouterr().err

    def test_oserror_returns_false(self, tmp_path, monkeypatch, capsys):
        def boom(*a, **k):
            raise OSError("injected failure")

        monkeypatch.setattr(subprocess, "run", boom)
        assert run_validate(tmp_path) is False
        assert "Cannot run validation" in capsys.readouterr().err

    def test_uses_timeout(self, tmp_path, monkeypatch):
        seen = {}

        class R:
            stdout = ""
            stderr = ""
            returncode = 0

        def fake_run(*a, **k):
            seen.update(k)
            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)
        assert run_validate(tmp_path) is True
        assert seen.get("timeout") == 120
        assert validate_mods.run_validate.__defaults__ == (120,)

    def test_success_echoes_output(self, tmp_path, monkeypatch, capsys):
        class R:
            stdout = "out-line\n"
            stderr = "err-line\n"
            returncode = 0

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
        assert run_validate(tmp_path) is True
        out = capsys.readouterr()
        assert "out-line" in out.out
        assert "err-line" in out.err

    def test_quiet_suppresses_stdout_on_success(self, tmp_path, monkeypatch, capsys):
        class R:
            stdout = "out-line\n"
            stderr = ""
            returncode = 0

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
        assert run_validate(tmp_path, quiet=True) is True
        out = capsys.readouterr()
        assert "out-line" not in out.out

    def test_quiet_shows_output_on_failure(self, tmp_path, monkeypatch, capsys):
        class R:
            stdout = "out-line\n"
            stderr = "err-line\n"
            returncode = 1

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
        assert run_validate(tmp_path, quiet=True) is False
        out = capsys.readouterr()
        assert "out-line" in out.out
        assert "err-line" in out.err


class TestFindModDirs:
    def test_finds_nested_modinfo(self, tmp_path):
        mod = tmp_path / "a" / "b"
        mod.mkdir(parents=True)
        (mod / "modinfo.json").write_text("{}")
        assert validate_mods.find_mod_dirs(tmp_path) == [mod]

    def test_bak_excluded(self, tmp_path):
        mod = tmp_path / "m"
        bak = mod / ".bak"
        bak.mkdir(parents=True)
        (mod / "modinfo.json").write_text("{}")
        (bak / "modinfo.json").write_text("{}")
        assert validate_mods.find_mod_dirs(tmp_path) == [mod]


class TestCollectModIds:
    def _mod(self, tmp_path, name, text):
        d = tmp_path / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "modinfo.json").write_text(text)
        return d

    def test_unparseable_counts_error(self, tmp_path, capsys):
        d = self._mod(tmp_path, "bad", "{bad")
        _, errors = validate_mods.collect_mod_ids([d])
        assert errors == [d]

    def test_non_dict_top_level_counts_error(self, tmp_path):
        d = self._mod(tmp_path, "num", "42")
        _, errors = validate_mods.collect_mod_ids([d])
        assert errors == [d]

    def test_non_dict_entry_counts_error(self, tmp_path):
        d = self._mod(tmp_path, "lst", '["x"]')
        _, errors = validate_mods.collect_mod_ids([d])
        assert errors == [d]

    def test_missing_fields_counts_error(self, tmp_path):
        import json as _json

        d = tmp_path / "miss"
        d.mkdir()
        (d / "modinfo.json").write_text(_json.dumps([{"type": "MOD_INFO", "id": "x"}]))
        _, errors = validate_mods.collect_mod_ids([d])
        assert errors == [d]

    def test_wrong_type_counts_error(self, tmp_path):
        import json as _json

        d = tmp_path / "wt"
        d.mkdir()
        (d / "modinfo.json").write_text(_json.dumps([{"type": "OTHER", "id": "x", "name": "N"}]))
        _, errors = validate_mods.collect_mod_ids([d])
        assert errors == [d]

    def test_invalid_id_counts_error(self, tmp_path):
        import json as _json

        d = tmp_path / "iid"
        d.mkdir()
        (d / "modinfo.json").write_text(_json.dumps([{"type": "MOD_INFO", "id": "", "name": "N"}]))
        _, errors = validate_mods.collect_mod_ids([d])
        assert errors == [d]

    def test_dict_modinfo_ok(self, tmp_path):
        import json as _json

        d = tmp_path / "dictmod"
        d.mkdir()
        (d / "modinfo.json").write_text(_json.dumps({"type": "MOD_INFO", "id": "d1", "name": "D"}))
        id_map, errors = validate_mods.collect_mod_ids([d])
        assert errors == []
        assert id_map == {"d1": [d]}


class TestMainBranches:
    def test_missing_base_returns_1(self, tmp_path, monkeypatch, capsys):
        import sys as _sys

        monkeypatch.setattr(
            _sys, "argv", ["validate_mods.py", "--base-dir", str(tmp_path / "nope")]
        )
        assert validate_mods.main() == 1

    def test_no_mods_returns_1(self, tmp_path, monkeypatch, capsys):
        import sys as _sys

        empty = tmp_path / "empty"
        empty.mkdir()
        monkeypatch.setattr(_sys, "argv", ["validate_mods.py", "--base-dir", str(empty)])
        assert validate_mods.main() == 1

    def test_duplicate_id_returns_1(self, tmp_path, monkeypatch, capsys):
        import json as _json
        import sys as _sys

        for name in ("a", "b"):
            d = tmp_path / name
            d.mkdir()
            (d / "modinfo.json").write_text(
                _json.dumps([{"type": "MOD_INFO", "id": "dup", "name": "N"}])
            )
        monkeypatch.setattr(_sys, "argv", ["validate_mods.py", "--base-dir", str(tmp_path)])
        monkeypatch.setattr(validate_mods, "run_validate", lambda *a, **k: True)
        assert validate_mods.main() == 1
        assert "Duplicate mod ID" in capsys.readouterr().err

    def test_main_success_returns_0(self, tmp_path, monkeypatch):
        import json as _json
        import sys as _sys

        d = tmp_path / "good"
        d.mkdir()
        (d / "modinfo.json").write_text(
            _json.dumps([{"type": "MOD_INFO", "id": "good", "name": "G", "dependencies": ["dda"]}])
        )
        monkeypatch.setattr(_sys, "argv", ["validate_mods.py", "--base-dir", str(tmp_path)])
        monkeypatch.setattr(validate_mods, "run_validate", lambda *a, **k: True)
        assert validate_mods.main() == 0

    def test_main_quiet_suppresses_headers(self, tmp_path, monkeypatch, capsys):
        import json as _json
        import sys as _sys

        d = tmp_path / "good"
        d.mkdir()
        (d / "modinfo.json").write_text(
            _json.dumps([{"type": "MOD_INFO", "id": "good", "name": "G", "dependencies": ["dda"]}])
        )
        seen = {}

        def fake_run(mod_dir, *a, **k):
            seen.update(k)
            return True

        monkeypatch.setattr(
            _sys, "argv", ["validate_mods.py", "--base-dir", str(tmp_path), "--quiet"]
        )
        monkeypatch.setattr(validate_mods, "run_validate", fake_run)
        assert validate_mods.main() == 0
        assert seen.get("quiet") is True
        out = capsys.readouterr()
        assert "Found" not in out.out
        assert "Validating" not in out.out
