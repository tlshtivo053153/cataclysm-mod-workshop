"""Tests for revert_translation_errors.py (E-4 gap fill)."""

from pathlib import Path

import revert_translation_errors as rte
from revert_translation_errors import processor, revert_name_fields


class TestRevertNameFields:
    def test_supported_type_reverted(self):
        obj = {"type": "MONSTER_FACTION", "name": {"str": "Faction"}}
        assert revert_name_fields(obj)["name"] == "Faction"

    def test_monstergroup_reverted(self):
        obj = {"type": "monstergroup", "name": {"str": "Group"}}
        assert revert_name_fields(obj)["name"] == "Group"

    def test_other_type_kept(self):
        obj = {"type": "ITEM", "id": "x", "name": {"str": "Knife"}}
        assert revert_name_fields(obj)["name"] == {"str": "Knife"}

    def test_missing_type_kept(self):
        obj = {"name": {"str": "x"}}
        assert revert_name_fields(obj)["name"] == {"str": "x"}

    def test_plain_name_kept(self):
        obj = {"type": "MONSTER_FACTION", "name": "plain"}
        assert revert_name_fields(obj)["name"] == "plain"

    def test_nested_recursion(self):
        data = [
            {"type": "MONSTER_FACTION", "name": {"str": "A"}},
            {"type": "ITEM", "name": {"str": "B"}},
        ]
        revert_name_fields(data)
        assert data[0]["name"] == "A"
        assert data[1]["name"] == {"str": "B"}

    def test_scalar_passthrough(self):
        assert revert_name_fields("s") == "s"
        assert revert_name_fields(5) == 5

    def test_depth_guard_returns_obj(self, capsys):
        obj = {"type": "MONSTER_FACTION", "name": {"str": "x"}}
        assert revert_name_fields(obj, _depth=51) is obj
        assert "max recursion depth" in capsys.readouterr().err


class TestProcessor:
    def test_converts_supported_in_list(self):
        data = [{"type": "MONSTER_FACTION", "name": {"str": "A"}}]
        out = processor(data, Path("f.json"))
        assert out == [{"type": "MONSTER_FACTION", "name": "A"}]

    def test_converts_dict(self):
        out = processor({"type": "monstergroup", "name": {"str": "G"}}, Path("f.json"))
        assert out == {"type": "monstergroup", "name": "G"}

    def test_noop_returns_none(self):
        assert processor([{"type": "ITEM", "name": {"str": "x"}}], Path("f.json")) is None
        assert processor({"type": "ITEM", "name": "x"}, Path("f.json")) is None

    def test_scalar_returns_none(self):
        assert processor("scalar", Path("f.json")) is None

    def test_main_callable(self):
        assert callable(rte.main)
