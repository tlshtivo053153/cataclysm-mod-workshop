from add_activity_level import (
    DEFAULT_ACTIVITY,
    _activity_map,
    add_activity_level,
    load_activity_config,
)

from .helpers import make_json_file


class TestAddActivityLevel:
    def setup_method(self):
        _activity_map.clear()

    def test_adds_when_missing(self):
        data = [{"type": "recipe", "name": "test recipe"}]
        result = add_activity_level(data)
        assert result[0].get("activity_level") == DEFAULT_ACTIVITY

    def test_skips_when_present(self):
        data = [{"type": "recipe", "activity_level": "MODERATE_EXERCISE", "name": "x"}]
        result = add_activity_level(data)
        assert result[0]["activity_level"] == "MODERATE_EXERCISE"

    def test_skips_non_recipe(self):
        data = [{"type": "ITEM", "name": "sword"}]
        result = add_activity_level(data)
        assert "activity_level" not in result[0]

    def test_insert_position(self):
        data = [{"type": "recipe", "name": "test", "subcategory": "CSC_FOOD_MEAT"}]
        result = add_activity_level(data)
        assert result[0]["activity_level"] == DEFAULT_ACTIVITY
        assert "type" in result[0]

    def test_with_config(self, tmp_path):
        config = make_json_file(tmp_path, {"CSC_FOOD_MEAT": "BRISK_EXERCISE"}, "config.json")
        load_activity_config(config)

        data = [{"type": "recipe", "subcategory": "CSC_FOOD_MEAT", "name": "stew"}]
        result = add_activity_level(data)
        assert result[0]["activity_level"] == "BRISK_EXERCISE"

    def test_non_dict_items_skipped(self):
        data = [{"type": "recipe"}, "not a dict", 42, None]
        result = add_activity_level(data)
        assert len(result) == 4
        assert result[0].get("activity_level") == DEFAULT_ACTIVITY

    def test_non_list_skipped_by_processor(self):
        from add_activity_level import processor

        result = processor({"not": "list"}, None)
        assert result is None
