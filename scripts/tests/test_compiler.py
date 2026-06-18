from pathlib import Path

from mapgen.grid import MAPGEN_SIZE
from mapgen.parser import parse_dsl
from mapgen.schema import RoomSpec
from mapgen_compiler import Compiler

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestParseDSL:
    def test_minimal(self):
        doc = parse_dsl(FIXTURES / "demo_mapgen.yml")
        assert len(doc.entries) == 1
        entry = doc.entries[0]
        assert entry.om_terrain == "demo_house"
        assert entry.fill_ter == "t_dirt"
        assert "fortified_shelter" in entry.palette
        assert len(entry.rooms) == 3
        assert len(entry.doors) == 2
        assert len(entry.features) == 3

    def test_room_ids(self):
        doc = parse_dsl(FIXTURES / "demo_mapgen.yml")
        ids = set(doc.entries[0].rooms.keys())
        assert ids == {"living", "kitchen", "closet"}


class TestCompilerIntegration:
    def test_compile_demo(self):
        doc = parse_dsl(FIXTURES / "demo_mapgen.yml")
        compiler = Compiler()
        entries = compiler.compile(doc)
        assert len(entries) == 1
        ctx = entries[0]
        assert ctx.om_terrain == "demo_house"
        assert ctx.fill_ter == "t_dirt"
        rows = ctx.grid.to_rows()
        assert len(rows) == MAPGEN_SIZE
        assert all(len(r) == MAPGEN_SIZE for r in rows)

    def test_emit_json(self):
        doc = parse_dsl(FIXTURES / "demo_mapgen.yml")
        compiler = Compiler()
        entries = compiler.compile(doc)
        data = compiler.emit(entries)
        assert len(data) == 1
        obj = data[0]
        assert obj["type"] == "mapgen"
        assert obj["om_terrain"] == "demo_house"
        assert "fill_ter" in obj["object"]
        assert "rows" in obj["object"]
        assert "palettes" in obj["object"]

    def test_passthrough_collision_warning(self):
        from mapgen.schema import EntrySpec
        spec = EntrySpec(
            om_terrain="test",
            fill_ter="t_floor",
            pass_through={"fill_ter": "t_dirt"},
        )
        compiler = Compiler()
        entries = compiler.compile(type("Doc", (), {"entries": [spec], "center": False})())
        assert len(entries) == 1
        entry = entries[0]
        collision_warnings = [w for w in entry.warnings if w.code == "passthrough_collision"]
        assert len(collision_warnings) == 0  # collision is added in emit_entry, not compile
        data = compiler.emit(entries)
        assert data[0]["object"]["fill_ter"] == "t_dirt"
        # Verify warning was added by emit
        collision_warnings = [w for w in entry.warnings if w.code == "passthrough_collision"]
        assert len(collision_warnings) == 1

    def test_passthrough_no_collision(self):
        from mapgen.schema import EntrySpec
        spec = EntrySpec(
            om_terrain="test",
            fill_ter="t_floor",
            pass_through={"place_loot": [1, 2, 3]},
        )
        compiler = Compiler()
        entries = compiler.compile(type("Doc", (), {"entries": [spec], "center": False})())
        data = compiler.emit(entries)
        assert data[0]["object"]["place_loot"] == [1, 2, 3]
        assert data[0]["object"]["fill_ter"] == "t_floor"

    def test_center_single_entry(self):
        from mapgen.schema import EntrySpec
        room = RoomSpec(id="r1", x=0, y=0, w=4, h=4)
        spec = EntrySpec(
            om_terrain="test",
            fill_ter="t_floor",
            rooms={"r1": room},
        )
        doc = type("Doc", (), {"entries": [spec], "center": True, "canvas_size": 24})()
        compiler = Compiler()
        compiler.compile(doc)
        assert room.x == 10  # (24 - 4) // 2 - 0
        assert room.y == 10

    def test_center_multiple_entries_same_offset(self):
        from mapgen.schema import EntrySpec
        room1 = RoomSpec(id="r1", x=0, y=0, w=4, h=4)
        room2 = RoomSpec(id="r2", x=2, y=2, w=4, h=4)
        spec1 = EntrySpec(om_terrain="test1", fill_ter="t_floor", rooms={"r1": room1})
        spec2 = EntrySpec(om_terrain="test2", fill_ter="t_floor", rooms={"r2": room2})
        doc = type("Doc", (), {"entries": [spec1, spec2], "center": True, "canvas_size": 24})()
        compiler = Compiler()
        compiler.compile(doc)
        # Global bbox: min=0, max=6, w=6, dx=(24-6)//2=9
        assert room1.x == 9
        assert room1.y == 9
        assert room2.x == 11
        assert room2.y == 11

    def test_center_no_shift_when_bbox_equals_canvas(self):
        from mapgen.schema import EntrySpec
        room = RoomSpec(id="r1", x=0, y=0, w=24, h=24)
        spec = EntrySpec(om_terrain="test", fill_ter="t_floor", rooms={"r1": room})
        doc = type("Doc", (), {"entries": [spec], "center": True, "canvas_size": 24})()
        compiler = Compiler()
        compiler.compile(doc)
        assert room.x == 0
        assert room.y == 0

    def test_center_with_global_tiles_and_features(self):
        from mapgen.schema import EntrySpec, FeatureSpec, FeatureTile, GlobalTile
        room = RoomSpec(id="r1", x=0, y=0, w=4, h=4)
        feature = FeatureSpec(room=None, tiles=[FeatureTile(char="f", x=3, y=3)])
        global_tile = GlobalTile(char="g", x=5, y=5)
        spec = EntrySpec(
            om_terrain="test",
            fill_ter="t_floor",
            rooms={"r1": room},
            features=[feature],
            global_tiles=[global_tile],
        )
        doc = type("Doc", (), {"entries": [spec], "center": True, "canvas_size": 24})()
        compiler = Compiler()
        compiler.compile(doc)
        # Global bbox: min=0, max=6 (room edge=4, global tile edge=6), w=6, dx=9
        assert room.x == 9
        assert room.y == 9
        assert feature.tiles[0].x == 12
        assert feature.tiles[0].y == 12
        assert global_tile.x == 14
        assert global_tile.y == 14
