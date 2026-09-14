"""Tests for revert_all_translations.py (E-4 gap fill)."""

from pathlib import Path

import revert_all_translations as rat
from common import MAX_RECURSION_DEPTH
from revert_all_translations import processor, revert_all_name_fields


class TestRevertAllNameFields:
    def test_str_object_reverted(self):
        obj = {"type": "ITEM", "id": "x", "name": {"str": "Knife"}}
        assert revert_all_name_fields(obj)["name"] == "Knife"

    def test_str_sp_preferred(self):
        obj = {"name": {"str": "plain", "str_sp": "plural"}}
        assert revert_all_name_fields(obj)["name"] == "plural"

    def test_description_reverted(self):
        obj = {"description": {"str": "A blade"}}
        assert revert_all_name_fields(obj)["description"] == "A blade"

    def test_plain_string_kept(self):
        obj = {"name": "Knife"}
        assert revert_all_name_fields(obj)["name"] == "Knife"

    def test_nested_list_recursion(self):
        data = [{"name": {"str": "A"}}, {"sub": {"name": {"str": "B"}}}]
        revert_all_name_fields(data)
        assert data[0]["name"] == "A"
        assert data[1]["sub"]["name"] == "B"

    def test_scalar_passthrough(self):
        assert revert_all_name_fields("s") == "s"
        assert revert_all_name_fields(42) == 42
        assert revert_all_name_fields(None) is None

    def test_depth_guard_returns_obj(self, capsys):
        obj = {"name": {"str": "x"}}
        assert revert_all_name_fields(obj, _depth=MAX_RECURSION_DEPTH + 1) is obj
        assert "max recursion depth" in capsys.readouterr().err


class TestProcessor:
    def test_converts_list(self):
        data = [{"name": {"str": "A"}}, {"name": "B"}]
        out = processor(data, Path("f.json"))
        assert out is not None
        assert out[0]["name"] == "A"
        assert out[1]["name"] == "B"

    def test_converts_dict(self):
        out = processor({"name": {"str": "A"}}, Path("f.json"))
        assert out == {"name": "A"}

    def test_noop_returns_none(self):
        assert processor([{"name": "plain"}], Path("f.json")) is None
        assert processor({"name": "plain"}, Path("f.json")) is None

    def test_scalar_returns_none(self):
        assert processor("scalar", Path("f.json")) is None
        assert processor(42, Path("f.json")) is None

    def test_main_contract_returns_int(self):
        assert rat.main.__annotations__.get("return") is int
