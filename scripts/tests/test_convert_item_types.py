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
