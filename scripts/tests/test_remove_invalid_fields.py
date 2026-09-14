import copy
import json
import sys
from pathlib import Path

import pytest
import remove_invalid_fields as rif
from remove_invalid_fields import (
    InvalidFieldsConfig,
    load_invalid_fields,
    make_processor,
    parse_invalid_fields,
    remove_invalid_fields,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def make_config(
    always=None,
    by_type=None,
) -> InvalidFieldsConfig:
    return InvalidFieldsConfig(
        remove_always=set(always) if always else set(),
        remove_by_type={k: set(v) for k, v in (by_type or {}).items()},
    )


REAL_CONFIG = load_invalid_fields()


class TestRemoveAlways:
    def test_removes_known_invalid(self):
        config = make_config(always={"method", "bashing"})
        obj = {"id": "item1", "method": "some_method", "name": "Test Item"}
        remove_invalid_fields(obj, config)
        assert "method" not in obj
        assert "id" in obj
        assert "name" in obj

    def test_recursive_removal(self):
        config = make_config(always={"method", "bashing"})
        obj = {
            "id": "outer",
            "bashing": 5,
            "nested": {"name": "inner", "method": "bad"},
        }
        remove_invalid_fields(obj, config)
        assert "bashing" not in obj
        assert "method" not in obj["nested"]
        assert "name" in obj["nested"]

    def test_preserves_valid(self):
        config = make_config(always={"method", "bashing"})
        obj = {"id": "item1", "name": "Test Item", "weight": 100}
        remove_invalid_fields(obj, config)
        assert set(obj.keys()) == {"id", "name", "weight"}

    def test_list_recursion(self):
        config = make_config(always={"method", "armor_bullet"})
        obj = {
            "id": "root",
            "items": [
                {"id": "a", "method": "x"},
                {"id": "b", "armor_bullet": "y"},
            ],
        }
        remove_invalid_fields(obj, config)
        assert "method" not in obj["items"][0]
        assert "armor_bullet" not in obj["items"][1]
        assert "id" in obj["items"][0]

    def test_non_dict_ignored(self):
        config = make_config(always={"method"})
        assert remove_invalid_fields("just a string", config) == "just a string"
        assert remove_invalid_fields(42, config) == 42
        assert remove_invalid_fields([1, 2, 3], config) == [1, 2, 3]
        assert remove_invalid_fields(None, config) is None


class TestFalsePositiveRegression:
    """The 5 fields valid in current CDDA must survive the real config."""

    CONTEXTS = [
        {"type": "GUN", "id": "pipe_pistol", "ammo": ["9mm"]},
        {"type": "item_group", "id": "guns_common", "ammo": 75, "magazine": 100},
        {"type": "vehicle_part", "id": "turret_m249", "ammo": 80},
        {"x": -1, "y": 2, "chance": 35, "magazine": 100, "ammo": 50},
        {"vehicle_data": {"sound_volume": 18, "sound": "Pop!"}},
        {"type": "sound", "sound_volume": 20},
        {"reproduction": {"baby_type": {"baby_egg": "egg_fish"}}},
        {"type": "TOOL", "id": "radio", "charges_per_use": 1},
        {"type": "MONSTER", "id": "mon_fish", "baby_egg": "egg_fish"},
    ]

    @pytest.mark.parametrize("obj", CONTEXTS)
    def test_valid_fields_kept(self, obj):
        data = copy.deepcopy(obj)
        remove_invalid_fields(data, REAL_CONFIG)
        assert data == obj

    def test_pipe_pistol_real_file(self):
        path = REPO_ROOT / "mods" / "small" / "pipe_pistol" / "data" / "items.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        original = copy.deepcopy(data)
        remove_invalid_fields(data, REAL_CONFIG)
        assert data == original
        assert data[0]["ammo"] == ["9mm"]

    def test_true_invalid_still_removed_with_real_config(self):
        obj = {
            "type": "ARMOR",
            "id": "old_armor",
            "armor_bullet": 5,
            "method": "x",
            "name": "Old",
        }
        remove_invalid_fields(obj, REAL_CONFIG)
        assert "armor_bullet" not in obj
        assert "method" not in obj
        assert obj["name"] == "Old"


class TestRemoveByType:
    def test_matching_type_removes(self, capsys):
        config = make_config(by_type={"GUN": ["ammo"]})
        obj = {"type": "GUN", "id": "g", "ammo": ["9mm"]}
        remove_invalid_fields(obj, config)
        assert "ammo" not in obj
        assert "id" in obj

    def test_mismatched_type_keeps_with_warning(self, capsys):
        config = make_config(by_type={"GUN": ["ammo"]})
        obj = {"type": "ARMOR", "id": "a", "ammo": ["9mm"]}
        remove_invalid_fields(obj, config)
        assert obj["ammo"] == ["9mm"]
        assert "keeping field 'ammo'" in capsys.readouterr().err

    def test_missing_type_keeps_with_warning(self, capsys):
        config = make_config(by_type={"GUN": ["ammo"]})
        obj = {"x": 1, "ammo": 50, "magazine": 100}
        remove_invalid_fields(obj, config)
        assert obj["ammo"] == 50
        assert "keeping field 'ammo'" in capsys.readouterr().err

    def test_non_string_type_keeps_with_warning(self, capsys):
        config = make_config(by_type={"GUN": ["ammo"]})
        obj = {"type": ["GUN"], "ammo": ["9mm"]}
        remove_invalid_fields(obj, config)
        assert obj["ammo"] == ["9mm"]
        assert "keeping field 'ammo'" in capsys.readouterr().err

    def test_unlisted_field_untouched_no_warning(self, capsys):
        config = make_config(by_type={"GUN": ["ammo"]})
        obj = {"type": "ARMOR", "id": "a", "name": "x"}
        remove_invalid_fields(obj, config)
        assert obj == {"type": "ARMOR", "id": "a", "name": "x"}
        assert capsys.readouterr().err == ""

    def test_always_wins_over_by_type(self):
        with pytest.raises(ValueError):
            parse_invalid_fields({"remove_always": ["ammo"], "remove_by_type": {"GUN": ["ammo"]}})


class TestConfigSchema:
    def test_valid_minimal(self):
        config = parse_invalid_fields({"remove_always": [], "remove_by_type": {}})
        assert config == InvalidFieldsConfig()

    def test_legacy_list_rejected(self):
        with pytest.raises(ValueError, match="legacy"):
            parse_invalid_fields(["ammo", "method"])

    def test_non_object_rejected(self):
        with pytest.raises(ValueError, match="top level"):
            parse_invalid_fields("ammo")

    def test_unknown_keys_rejected(self):
        with pytest.raises(ValueError, match="unknown keys"):
            parse_invalid_fields({"remove_always": [], "remove_by_type": {}, "extra": []})

    def test_missing_keys_rejected(self):
        with pytest.raises(ValueError, match="missing keys"):
            parse_invalid_fields({"remove_always": []})

    def test_non_list_always_rejected(self):
        with pytest.raises(ValueError, match="remove_always"):
            parse_invalid_fields({"remove_always": "ammo", "remove_by_type": {}})

    def test_non_object_by_type_rejected(self):
        with pytest.raises(ValueError, match="remove_by_type must be an object"):
            parse_invalid_fields({"remove_always": [], "remove_by_type": ["GUN"]})

    def test_empty_and_non_string_entries_rejected(self):
        with pytest.raises(ValueError, match="non-empty strings"):
            parse_invalid_fields({"remove_always": [""], "remove_by_type": {}})
        with pytest.raises(ValueError, match="non-empty strings"):
            parse_invalid_fields({"remove_always": [], "remove_by_type": {"GUN": [42]}})

    def test_duplicates_rejected(self):
        with pytest.raises(ValueError, match="duplicates"):
            parse_invalid_fields({"remove_always": ["method", "method"], "remove_by_type": {}})

    def test_real_config_loads(self):
        assert "armor_bullet" in REAL_CONFIG.remove_always
        assert "ammo" not in REAL_CONFIG.remove_always
        assert "magazine" not in REAL_CONFIG.remove_always
        assert "sound_volume" not in REAL_CONFIG.remove_always
        assert "baby_egg" not in REAL_CONFIG.remove_always
        assert "charges_per_use" not in REAL_CONFIG.remove_always
        # relic_data is valid (MAGIC.md artifacts) and must not be removed.
        assert "relic_data" not in REAL_CONFIG.remove_always

    def test_relic_data_kept_with_real_config(self):
        obj = {
            "type": "ITEM",
            "id": "ring",
            "relic_data": {"passive_effects": []},
        }
        original = copy.deepcopy(obj)
        remove_invalid_fields(obj, REAL_CONFIG)
        assert obj == original

    def test_noop_returns_none(self):
        proc = make_processor(make_config(always={"bad_field"}))
        assert proc({"id": "a"}, None) is None
        assert proc([{"id": "a"}], None) is None
        assert proc("just a scalar", None) is None

    def test_positive_returns_data(self):
        proc = make_processor(make_config(always={"bad_field"}))
        data = [{"id": "a", "bad_field": "x"}]
        result = proc(data, None)
        assert result == [{"id": "a"}]


class TestMakeProcessor:
    def test_make_processor_removes_fields_from_list(self):
        proc = make_processor(make_config(always={"bad_field"}))
        data = [{"id": "a", "bad_field": "x"}, {"id": "b", "bad_field": "y"}]
        result = proc(data, None)
        assert "bad_field" not in result[0]
        assert "bad_field" not in result[1]
        assert result[0]["id"] == "a"

    def test_make_processor_removes_fields_from_dict(self):
        proc = make_processor(make_config(always={"bad_field"}))
        data = {"id": "root", "bad_field": "x"}
        result = proc(data, None)
        assert "bad_field" not in result
        assert result["id"] == "root"

    def test_make_processor_applies_type_rule(self):
        proc = make_processor(make_config(by_type={"GUN": ["ammo"]}))
        data = [
            {"type": "GUN", "id": "g", "ammo": ["9mm"]},
            {"type": "ARMOR", "id": "a", "ammo": ["9mm"]},
        ]
        result = proc(data, None)
        assert "ammo" not in result[0]
        assert result[1]["ammo"] == ["9mm"]


class TestMain:
    def test_missing_config_exits_1(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(rif, "INVALID_FIELDS_PATH", tmp_path / "does_not_exist.json")
        monkeypatch.setattr(sys, "argv", ["remove_invalid_fields.py", "--input", str(tmp_path)])
        with pytest.raises(SystemExit) as exc:
            rif.main()
        assert exc.value.code == 1
        assert "not found" in capsys.readouterr().err

    def test_malformed_config_exits_1(self, tmp_path, monkeypatch, capsys):
        bad = tmp_path / "invalid_fields.json"
        bad.write_text('["ammo"]', encoding="utf-8")
        monkeypatch.setattr(rif, "INVALID_FIELDS_PATH", bad)
        monkeypatch.setattr(sys, "argv", ["remove_invalid_fields.py", "--input", str(tmp_path)])
        with pytest.raises(SystemExit) as exc:
            rif.main()
        assert exc.value.code == 1
        assert "Invalid fields list error" in capsys.readouterr().err
