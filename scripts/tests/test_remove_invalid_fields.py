from remove_invalid_fields import make_processor, remove_invalid_fields


class TestRemoveInvalidFields:
    INVALID = {"method", "bashing", "magazine"}

    def test_removes_known_invalid(self):
        obj = {"id": "item1", "method": "some_method", "name": "Test Item"}
        remove_invalid_fields(obj, self.INVALID)
        assert "method" not in obj
        assert "id" in obj
        assert "name" in obj

    def test_recursive_removal(self):
        obj = {
            "id": "outer",
            "bashing": 5,
            "nested": {"name": "inner", "method": "bad"},
        }
        remove_invalid_fields(obj, self.INVALID)
        assert "bashing" not in obj
        assert "method" not in obj["nested"]
        assert "name" in obj["nested"]

    def test_preserves_valid(self):
        obj = {"id": "item1", "name": "Test Item", "weight": 100}
        remove_invalid_fields(obj, self.INVALID)
        assert set(obj.keys()) == {"id", "name", "weight"}

    def test_list_recursion(self):
        obj = {
            "id": "root",
            "items": [
                {"id": "a", "method": "x"},
                {"id": "b", "magazine": "y"},
            ],
        }
        remove_invalid_fields(obj, self.INVALID)
        assert "method" not in obj["items"][0]
        assert "magazine" not in obj["items"][1]
        assert "id" in obj["items"][0]

    def test_non_dict_ignored(self):
        assert remove_invalid_fields("just a string", self.INVALID) == "just a string"
        assert remove_invalid_fields(42, self.INVALID) == 42
        assert remove_invalid_fields([1, 2, 3], self.INVALID) == [1, 2, 3]
        assert remove_invalid_fields(None, self.INVALID) is None


class TestMakeProcessor:
    INVALID = {"bad_field"}

    def test_make_processor_removes_fields_from_list(self):
        proc = make_processor(self.INVALID)
        data = [{"id": "a", "bad_field": "x"}, {"id": "b", "bad_field": "y"}]
        result = proc(data, None)
        assert "bad_field" not in result[0]
        assert "bad_field" not in result[1]
        assert result[0]["id"] == "a"

    def test_make_processor_removes_fields_from_dict(self):
        proc = make_processor(self.INVALID)
        data = {"id": "root", "bad_field": "x"}
        result = proc(data, None)
        assert "bad_field" not in result
        assert result["id"] == "root"
