from mapgen.known_palettes import _load_palettes, is_char_known


class TestKnownPalettes:
    def test_lookup_existing_palette(self):
        palettes = _load_palettes()
        palette = palettes.get("fortified_shelter")
        assert palette is not None
        assert "terrain" in palette
        assert "furniture" in palette

    def test_lookup_nonexistent_palette(self):
        palettes = _load_palettes()
        assert palettes.get("nonexistent") is None

    def test_char_in_terrain(self):
        assert is_char_known("fortified_shelter", "{") is True

    def test_char_in_furniture(self):
        assert is_char_known("fortified_shelter", "G") is True

    def test_char_not_in_either(self):
        assert is_char_known("fortified_shelter", "x") is False

    def test_unknown_palette_returns_false(self):
        assert is_char_known("nonexistent", "{") is False
