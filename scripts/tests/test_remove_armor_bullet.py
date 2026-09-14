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

    def test_non_string_value_does_not_crash(self):
        # {"value": [...]} must not raise TypeError: unhashable.
        obj = {"id": "x", "value": ["ARMOR_BULLET"], "other": {"value": {"a": 1}}}
        result = clean_object(obj)
        assert result["value"] == ["ARMOR_BULLET"]
        assert result["other"] == {"value": {"a": 1}}

    def test_processor_noop_returns_none(self):
        from remove_armor_bullet import processor

        assert processor([{"id": "a", "value": "ARMOR_CUT"}], None) is None
        assert processor({"id": "a"}, None) is None

    def test_processor_top_level_target_skipped_not_nulled(self):
        from remove_armor_bullet import processor

        # Whole-file dict matching TARGET would previously risk writing null.
        assert processor({"value": "ARMOR_BULLET"}, None) is None

    def test_processor_positive_returns_data(self):
        from remove_armor_bullet import processor

        data = [{"value": "ARMOR_BULLET"}, {"id": "keep"}]
        result = processor(data, None)
        assert result == [{"id": "keep"}]
