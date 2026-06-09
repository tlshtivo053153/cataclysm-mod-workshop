import pytest
from pathlib import Path
from mapgen.schema import parse_dsl, RoomSpec, make_room
from mapgen import (
    CompileError,
    OutOfBoundsError,
    DuplicateRoomIdError,
    InvalidRoomSizeError,
    RoomOverlapError,
    RoomNotAdjacentError,
)
from mapgen_compiler import Compiler
from mapgen.grid import MAPGEN_SIZE


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
        ids = {r.id for r in doc.entries[0].rooms}
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
        entries = compiler.compile(type("Doc", (), {"entries": [spec]})())
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
        entries = compiler.compile(type("Doc", (), {"entries": [spec]})())
        data = compiler.emit(entries)
        assert data[0]["object"]["place_loot"] == [1, 2, 3]
        assert data[0]["object"]["fill_ter"] == "t_floor"
