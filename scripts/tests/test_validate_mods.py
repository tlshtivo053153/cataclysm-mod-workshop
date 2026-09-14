"""Unit tests for validate_mods.py Level1 content rules (C-1).

Covers CORE.md-derived checks beyond JSON syntax:
- recipe `activity_level` required (ERROR)
- modinfo `dependencies` must include `dda` (ERROR)
- `copy-from` target not defined in-mod (WARNING only)
"""

import json

from validate_mods import (
    check_copy_from_references,
    check_modinfo_dependencies,
    check_recipe_activity_level,
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
