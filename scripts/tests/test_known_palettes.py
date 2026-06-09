from mapgen.known_palettes import PaletteRegistry, get_palette, is_char_known


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
