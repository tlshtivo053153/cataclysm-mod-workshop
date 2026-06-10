import pytest
from pathlib import Path
from mapgen.schema import parse_dsl, RoomSpec, PlaceSpec, resolve_room_placement
from mapgen import CompileError, OutOfBoundsError
from mapgen.grid import MAPGEN_SIZE


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestCanvas:
    def test_canvas_valid(self):
        doc = parse_dsl(FIXTURES / "canvas_32.yml")
        assert doc.canvas == {"w": 32, "h": 32}
        assert len(doc.entries) == 1

    def test_canvas_invalid_size(self):
        with pytest.raises(CompileError, match="canvas"):
            parse_dsl(FIXTURES / "canvas_invalid_size.yml")

    def test_canvas_default(self):
        doc = parse_dsl(FIXTURES / "single_room.yml")
        assert doc.canvas is None
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        assert len(entries) == 1
        grid = entries[0].grid
        assert grid.width == MAPGEN_SIZE
        assert grid.height == MAPGEN_SIZE

    def test_canvas_room_oob(self):
        with pytest.raises(CompileError, match="out of bounds"):
            parse_dsl(FIXTURES / "canvas_oob.yml")


class TestAnchorPlacement:
    def test_anchor_adjacent_east(self):
        doc = parse_dsl(FIXTURES / "anchor_adjacent_east.yml")
        entry = doc.entries[0]
        living = entry.rooms["living"]
        kitchen = entry.rooms["kitchen"]
        assert kitchen.x == 8
        assert kitchen.y == 0
        assert kitchen.place is not None
        assert kitchen.place.relative_to == "living"

    def test_anchor_adjacent_with_margin(self):
        doc = parse_dsl(FIXTURES / "anchor_with_margin.yml")
        entry = doc.entries[0]
        living = entry.rooms["living"]
        kitchen = entry.rooms["kitchen"]
        assert kitchen.x == 10
        assert kitchen.y == 0

    def test_anchor_inside(self):
        doc = parse_dsl(FIXTURES / "anchor_inside.yml")
        entry = doc.entries[0]
        outer = entry.rooms["outer"]
        inner = entry.rooms["inner"]
        assert inner.x == outer.x + 1
        assert inner.y == outer.y + outer.h - inner.h - 1
        assert inner.place is not None
        assert inner.place.inside == "outer"

    def test_anchor_place_xy_conflict(self):
        with pytest.raises(CompileError, match="x/y"):
            parse_dsl(FIXTURES / "anchor_place_xy_conflict.yml")

    def test_anchor_unknown_ref(self):
        with pytest.raises(CompileError, match="unknown room"):
            parse_dsl(FIXTURES / "anchor_unknown_ref.yml")

    def test_anchor_out_of_bounds(self):
        with pytest.raises(CompileError, match="out of bounds"):
            parse_dsl(FIXTURES / "anchor_oob.yml")

    def test_anchor_south(self):
        doc = parse_dsl(FIXTURES / "anchor_adjacent_east.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        grid = entries[0].grid
        assert grid.get(7, 5) == "="


class TestDoorPosition:
    def test_door_position_left(self):
        doc = parse_dsl(FIXTURES / "door_position_left.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        grid = entries[0].grid
        assert grid.get(3, 0) == "="

    def test_door_position_right(self):
        doc = parse_dsl(FIXTURES / "door_position_right.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        grid = entries[0].grid
        assert grid.get(3, 5) == "="

    def test_door_position_offset_conflict(self):
        with pytest.raises(CompileError, match="position.*offset"):
            parse_dsl(FIXTURES / "door_position_offset_conflict.yml")

    def test_door_position_center_default(self):
        doc = parse_dsl(FIXTURES / "two_rooms_door.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        grid = entries[0].grid
        assert grid.get(5, 4) == "="


class TestMeaningAnnotation:
    def test_meaning_match_no_warning(self):
        doc = parse_dsl(FIXTURES / "meaning_annotation.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        meaning_warnings = [w for w in entries[0].warnings if w.code in ("meaning_conflict", "meaning_not_in_palette")]
        assert len(meaning_warnings) == 1

    def test_meaning_conflict_warning(self):
        doc = parse_dsl(FIXTURES / "meaning_annotation.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        conflict_warnings = [w for w in entries[0].warnings if w.code == "meaning_conflict"]
        assert len(conflict_warnings) == 1
        assert "f_custom_chair" in conflict_warnings[0].message
        assert "f_sofa" in conflict_warnings[0].message

    def test_meaning_not_in_palette_warning(self):
        doc = parse_dsl(FIXTURES / "meaning_unknown.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        entries = compiler.compile(doc)
        meaning_warnings = [w for w in entries[0].warnings if w.code == "meaning_not_in_palette"]
        assert len(meaning_warnings) == 1
        assert "f_mystery_item" in meaning_warnings[0].message
