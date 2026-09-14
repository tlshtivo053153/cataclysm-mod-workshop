from convert_item_types import convert_object


class TestConvertObject:
    def test_basic_conversion(self):
        obj = {"type": "AMMO"}
        result = convert_object(dict(obj))
        assert result["type"] == "ITEM"
        assert result["subtypes"] == ["AMMO"]

    def test_composite_type(self):
        obj = {"type": "TOOL_ARMOR"}
        result = convert_object(dict(obj))
        assert result["type"] == "ITEM"
        assert result["subtypes"] == ["TOOL", "ARMOR"]

    def test_no_change(self):
        obj = {"type": "MOD_INFO"}
        result = convert_object(dict(obj))
        assert result["type"] == "MOD_INFO"
        assert "subtypes" not in result

    def test_already_converted(self):
        obj = {"type": "ITEM", "subtypes": ["TOOL"]}
        result = convert_object(dict(obj))
        assert result["type"] == "ITEM"
        assert result["subtypes"] == ["TOOL"]

    def test_nested(self):
        obj = {"type": "GUN", "mods": [{"type": "ARMOR"}, {"type": "AMMO"}]}
        result = convert_object(dict(obj))
        assert result["type"] == "ITEM"
        assert result["subtypes"] == ["GUN"]
        assert result["mods"][0]["type"] == "ITEM"
        assert result["mods"][0]["subtypes"] == ["ARMOR"]
        assert result["mods"][1]["type"] == "ITEM"
        assert result["mods"][1]["subtypes"] == ["AMMO"]

    def test_non_dict_passthrough(self):
        assert convert_object("string") == "string"
        assert convert_object(42) == 42
        assert convert_object([1, 2, 3]) == [1, 2, 3]

    def test_non_string_type_does_not_crash(self):
        assert convert_object({"type": ["GUN"]}) == {"type": ["GUN"]}
        assert convert_object({"type": {"a": 1}}) == {"type": {"a": 1}}
        assert convert_object({"type": None}) == {"type": None}

    def test_processor_noop_returns_none(self):
        from convert_item_types import processor

        assert processor([{"type": "MOD_INFO", "id": "x"}], None) is None
        assert processor({"type": "ITEM", "subtypes": ["TOOL"]}, None) is None

    def test_processor_positive_returns_converted(self):
        from convert_item_types import processor

        result = processor([{"type": "GUN", "id": "g"}], None)
        assert result == [{"type": "ITEM", "subtypes": ["GUN"], "id": "g"}]
