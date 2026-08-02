import json
from pathlib import Path

import pytest
from mapgen.known_palettes import (
    PaletteRegistry,
    _cdda_dict_to_palettes,
    _cdda_list_to_palettes,
    _extract_cdda_palette_fields,
    _load_json_palettes,
    get_palette,
    is_char_known,
)


class TestKnownPalettes:
    def setup_method(self):
        self.registry = PaletteRegistry()

    def test_lookup_existing_palette(self):
        palette = self.registry.get_palette("fortified_shelter")
        assert palette is not None
        assert "terrain" in palette
        assert "furniture" in palette

    def test_lookup_nonexistent_palette(self):
        assert self.registry.get_palette("nonexistent") is None

    def test_lookup_nonexistent_reported_once(self):
        assert self.registry.get_palette("nonexistent2") is None
        assert "nonexistent2" in self.registry._unknown_reported

    def test_char_in_terrain(self):
        assert self.registry.is_char_known("fortified_shelter", "{") is True

    def test_char_in_furniture(self):
        assert self.registry.is_char_known("fortified_shelter", "G") is True

    def test_char_not_in_either(self):
        assert self.registry.is_char_known("fortified_shelter", "x") is False

    def test_unknown_palette_returns_false(self):
        assert self.registry.is_char_known("nonexistent", "{") is False

    def test_module_level_get_palette(self):
        palette = get_palette("fortified_shelter")
        assert palette is not None

    def test_module_level_is_char_known(self):
        assert is_char_known("fortified_shelter", "{") is True


class TestCddaFormat:
    def test_cdda_array_format(self, tmp_path: Path):
        p = tmp_path / "pal.json"
        p.write_text(
            json.dumps(
                [
                    {
                        "type": "palette",
                        "id": "test_pal",
                        "terrain": {"{": "t_wall"},
                        "furniture": {"G": "f_chair"},
                    }
                ]
            ),
            encoding="utf-8",
        )
        reg = PaletteRegistry(palette_paths=[p])
        pal = reg.get_palette("test_pal")
        assert pal is not None
        assert pal["terrain"]["{"] == "t_wall"
        assert pal["furniture"]["G"] == "f_chair"

    def test_cdda_single_format(self, tmp_path: Path):
        p = tmp_path / "pal.json"
        p.write_text(
            json.dumps(
                {
                    "type": "palette",
                    "id": "solo",
                    "terrain": {"a": "t_floor"},
                }
            ),
            encoding="utf-8",
        )
        reg = PaletteRegistry(palette_paths=[p])
        assert reg.get_palette("solo") == {"terrain": {"a": "t_floor"}}

    def test_cdda_mixed_array(self, tmp_path: Path):
        p = tmp_path / "pal.json"
        p.write_text(
            json.dumps(
                [
                    {"type": "palette", "id": "keep", "terrain": {"a": "t_x"}},
                    {"type": "mapgen", "id": "ignore_me"},
                    {"type": "palette", "id": "", "terrain": {"b": "t_y"}},
                    {"type": "palette", "id": "keep2"},
                ]
            ),
            encoding="utf-8",
        )
        reg = PaletteRegistry(palette_paths=[p])
        assert reg.get_palette("keep") is not None
        assert reg.get_palette("keep2") is not None
        assert reg.get_palette("ignore_me") is None

    def test_cdda_no_id_skipped(self):
        assert _cdda_dict_to_palettes({"type": "palette", "terrain": {}}) == {}

    def test_cdda_missing_terrain(self, tmp_path: Path):
        p = tmp_path / "pal.json"
        p.write_text(
            json.dumps(
                [
                    {"type": "palette", "id": "no_ter", "furniture": {"a": "f_x"}},
                ]
            ),
            encoding="utf-8",
        )
        reg = PaletteRegistry(palette_paths=[p])
        pal = reg.get_palette("no_ter")
        assert pal is not None
        assert "terrain" not in pal
        assert pal["furniture"]["a"] == "f_x"

    def test_backward_compat(self, tmp_path: Path):
        p = tmp_path / "pal.json"
        p.write_text(json.dumps({"legacy": {"terrain": {"a": "t_legacy"}}}), encoding="utf-8")
        reg = PaletteRegistry(palette_paths=[p])
        assert reg.get_palette("legacy") == {"terrain": {"a": "t_legacy"}}

    def test_parametric_explain(self):
        obj = {
            "type": "palette",
            "id": "para",
            "terrain": {"a": {"ter": "t_wall", "furn": "f_sofa"}},
        }
        result = _cdda_dict_to_palettes(obj)
        reg = PaletteRegistry()
        reg._palettes.update(result)
        assert reg.explain_char("para", "a") == "t_wall"

    def test_parametric_explain_terrain_key(self):
        obj = {
            "type": "palette",
            "id": "para2",
            "furniture": {"b": {"terrain": "f_chair"}},
        }
        reg = PaletteRegistry()
        reg._palettes.update(_cdda_dict_to_palettes(obj))
        assert reg.explain_char("para2", "b") == "f_chair"

    def test_cdda_fortified_shelter(self):
        path = Path("mods/small/fortified_shelters/data/palette/fortified_shelter.json")
        if not path.is_file():
            pytest.skip(f"fixture not found: {path}")
        reg = PaletteRegistry(palette_paths=[path])
        pal = reg.get_palette("fortified_shelter")
        assert pal is not None
        assert pal["terrain"]["{"] == "t_window_boarded"
        assert pal["furniture"]["G"] == "f_gun_safe_el"
        assert pal["items"]["G"] == {"item": "army_personal_locker", "chance": 80}
        assert reg.is_char_known("fortified_shelter", "{") is True
        assert reg.is_char_known("fortified_shelter", "G") is True

    def test_load_json_palettes_list(self, tmp_path: Path):
        p = tmp_path / "p.json"
        p.write_text(
            json.dumps([{"type": "palette", "id": "x", "terrain": {"a": "t_a"}}]), encoding="utf-8"
        )
        assert _load_json_palettes(p) == {"x": {"terrain": {"a": "t_a"}}}

    def test_load_json_palettes_dict_compiler(self, tmp_path: Path):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({"x": {"terrain": {"a": "t_a"}}}), encoding="utf-8")
        assert _load_json_palettes(p) == {"x": {"terrain": {"a": "t_a"}}}

    def test_load_json_palettes_invalid_json(self, tmp_path: Path, caplog):
        p = tmp_path / "p.json"
        p.write_text("{not json", encoding="utf-8")
        assert _load_json_palettes(p) == {}
        assert any(
            "Failed to load palettes" in record.message and "p.json" in record.message
            for record in caplog.records
        )

    def test_extract_cdda_palette_fields_ignores_non_dict(self):
        result = _extract_cdda_palette_fields(
            {
                "terrain": {"a": "t_x"},
                "furniture": "not_a_dict",
                "items": ["list", "not", "dict"],
            }
        )
        assert result == {"terrain": {"a": "t_x"}}

    def test_explain_char_legacy_string(self):
        reg = PaletteRegistry()
        reg._palettes["legacy"] = {"terrain": {"a": "t_legacy"}}
        assert reg.explain_char("legacy", "a") == "t_legacy"

    def test_explain_char_unknown_returns_none(self):
        reg = PaletteRegistry()
        reg._palettes["empty"] = {}
        assert reg.explain_char("empty", "a") is None

    def test_cdda_list_helper_filters_non_palette(self):
        result = _cdda_list_to_palettes(
            [
                {"type": "mapgen", "id": "x"},
                "not_a_dict",
                {"type": "palette", "id": "p1", "terrain": {"a": "t_b"}},
            ]
        )
        assert result == {"p1": {"terrain": {"a": "t_b"}}}

    def test_cdda_list_helper_no_id(self):
        assert _cdda_list_to_palettes([{"type": "palette", "terrain": {}}]) == {}

    def test_parametric_empty_dict_falls_through(self):
        reg = PaletteRegistry()
        reg._palettes["p"] = {
            "terrain": {"a": {}},
            "furniture": {"a": "f_chair"},
        }
        assert reg.explain_char("p", "a") == "f_chair"

    def test_parametric_empty_dict_no_match_returns_none(self):
        reg = PaletteRegistry()
        reg._palettes["p2"] = {"terrain": {"a": {}}}
        assert reg.explain_char("p2", "a") is None
