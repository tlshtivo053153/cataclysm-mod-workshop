from remove_armor_bullet import clean_object


class TestCleanObject:
    def test_removes_target_value(self):
        obj = {"type": "enchantment", "values": [{"value": "ARMOR_BULLET"}]}
        result = clean_object(obj)
        assert len(result["values"]) == 0

    def test_removes_armor_ballistic(self):
        obj = {"type": "enchantment", "values": [{"value": "ARMOR_BALLISTIC"}]}
        result = clean_object(obj)
        assert len(result["values"]) == 0

    def test_preserves_other_values(self):
        obj = {
            "type": "enchantment",
            "values": [{"value": "ARMOR_CUT"}, {"value": "REGEN_HP"}],
        }
        result = clean_object(obj)
        assert len(result["values"]) == 2
        assert result["values"][0]["value"] == "ARMOR_CUT"
        assert result["values"][1]["value"] == "REGEN_HP"

    def test_nested_cleanup(self):
        obj = {
            "type": "armor_data",
            "armor": [{"protection": [{"value": "ARMOR_BULLET"}]}],
        }
        result = clean_object(obj)
        assert len(result["armor"][0]["protection"]) == 0

    def test_nested_dict_removed(self):
        obj = {"outer": {"value": "ARMOR_BULLET"}}
        result = clean_object(obj)
        assert "outer" not in result

    def test_non_dict_passthrough(self):
        assert clean_object("string") == "string"
        assert clean_object(42) == 42
        assert clean_object([1, 2, 3]) == [1, 2, 3]

    def test_mixed_list(self):
        obj = {
            "values": [
                {"value": "ARMOR_BULLET"},
                {"value": "ARMOR_CUT"},
                "non_dict",
            ]
        }
        result = clean_object(obj)
        assert len(result["values"]) == 2
        assert result["values"][0]["value"] == "ARMOR_CUT"
        assert result["values"][1] == "non_dict"

    def test_entire_top_level_removed(self):
        from remove_armor_bullet import processor

        data = [{"value": "ARMOR_BULLET"}, {"value": "ARMOR_CUT"}]
        result = processor(data, None)
        assert result == [{"value": "ARMOR_CUT"}]
