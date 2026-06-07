from mapgen.known_palettes import KNOWN_PALETTES, is_char_known


class TestKnownPalettes:
    def test_lookup_existing_palette(self):
        palette = KNOWN_PALETTES.get("fortified_shelter")
        assert palette is not None
        assert "terrain" in palette
        assert "furniture" in palette

    def test_lookup_nonexistent_palette(self):
        assert KNOWN_PALETTES.get("nonexistent") is None

    def test_char_in_terrain(self):
        assert is_char_known("fortified_shelter", "{") is True

    def test_char_in_furniture(self):
        assert is_char_known("fortified_shelter", "G") is True

    def test_char_not_in_either(self):
        assert is_char_known("fortified_shelter", "x") is False

    def test_unknown_palette_returns_false(self):
        assert is_char_known("nonexistent", "{") is False
