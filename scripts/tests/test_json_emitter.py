from mapgen import EntryContext
from mapgen.grid import Grid
from mapgen.json_emitter import emit_entry, emit_json_array


class TestJsonEmitter:
    def test_single_entry_structure(self):
        grid = Grid(fill_char=" ")
        grid.draw_rect_border(0, 0, 4, 4, "#")
        ctx = EntryContext(
            om_terrain="test_location",
            fill_ter="t_floor",
            palette=["my_palette"],
            grid=grid,
            pass_through={},
            warnings=[],
        )
        result = emit_entry(ctx)
        assert result["type"] == "mapgen"
        assert result["om_terrain"] == "test_location"
        obj = result["object"]
        assert obj["fill_ter"] == "t_floor"
        assert len(obj["rows"]) == 24
        assert obj["palettes"] == ["my_palette"]

    def test_pass_through_terrain(self):
        grid = Grid()
        ctx = EntryContext(
            om_terrain="test",
            fill_ter="t_floor",
            palette=[],
            grid=grid,
            pass_through={"terrain": {"@": "t_railing"}},
            warnings=[],
        )
        result = emit_entry(ctx)
        assert result["object"]["terrain"] == {"@": "t_railing"}

    def test_pass_through_furniture(self):
        grid = Grid()
        ctx = EntryContext(
            om_terrain="test",
            fill_ter="t_floor",
            palette=[],
            grid=grid,
            pass_through={"furniture": {"~": "f_sandbag_half"}},
            warnings=[],
        )
        result = emit_entry(ctx)
        assert result["object"]["furniture"] == {"~": "f_sandbag_half"}

    def test_pass_through_place_items(self):
        grid = Grid()
        ctx = EntryContext(
            om_terrain="test",
            fill_ter="t_floor",
            palette=[],
            grid=grid,
            pass_through={
                "place_items": [
                    {"item": "SUS_trash_roof", "chance": 50}
                ]
            },
            warnings=[],
        )
        result = emit_entry(ctx)
        assert result["object"]["place_items"] == [
            {"item": "SUS_trash_roof", "chance": 50}
        ]

    def test_pass_through_place_zones(self):
        grid = Grid()
        ctx = EntryContext(
            om_terrain="test",
            fill_ter="t_floor",
            palette=[],
            grid=grid,
            pass_through={
                "place_zones": [
                    {"type": "ZONE_START_POINT"}
                ]
            },
            warnings=[],
        )
        result = emit_entry(ctx)
        assert len(result["object"]["place_zones"]) == 1

    def test_empty_pass_through_omitted(self):
        grid = Grid()
        ctx = EntryContext(
            om_terrain="test",
            fill_ter="t_floor",
            palette=[],
            grid=grid,
            pass_through={"terrain": {}, "furniture": {}},
            warnings=[],
        )
        result = emit_entry(ctx)
        assert "terrain" in result["object"]
        assert "furniture" in result["object"]
        assert result["object"]["terrain"] == {}
        assert result["object"]["furniture"] == {}

    def test_multi_entry_array(self):
        grid1 = Grid()
        grid2 = Grid()
        ctx1 = EntryContext(
            om_terrain="a",
            fill_ter="t_floor",
            palette=["p1"],
            grid=grid1,
            pass_through={},
            warnings=[],
        )
        ctx2 = EntryContext(
            om_terrain="b",
            fill_ter="t_dirt",
            palette=["p2"],
            grid=grid2,
            pass_through={},
            warnings=[],
        )
        result = emit_json_array([ctx1, ctx2])
        assert len(result) == 2
        assert result[0]["om_terrain"] == "a"
        assert result[1]["om_terrain"] == "b"
