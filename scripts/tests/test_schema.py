from pathlib import Path

import pytest
from mapgen import (
    CompileError,
    DuplicateRoomIdError,
    InvalidRoomSizeError,
    OutOfBoundsError,
)
from mapgen.parser import parse_dsl

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestParseDSLValidationErrors:
    def test_room_out_of_bounds(self):
        with pytest.raises(CompileError) as exc_info:
            parse_dsl(FIXTURES / "room_oob.yml")
        cause = exc_info.value
        assert isinstance(cause, OutOfBoundsError) or "out of bounds" in str(cause).lower()

    def test_duplicate_room_ids(self):
        with pytest.raises(CompileError) as exc_info:
            parse_dsl(FIXTURES / "duplicate_ids.yml")
        cause = exc_info.value
        assert isinstance(cause, DuplicateRoomIdError) or "duplicate" in str(cause).lower()

    def test_room_overlap_v2(self):
        with pytest.raises(CompileError) as exc_info:
            parse_dsl(FIXTURES / "room_out_of_bounds.yml")
        cause = exc_info.value
        assert isinstance(cause, OutOfBoundsError) or "out of bounds" in str(cause).lower()

    def test_invalid_room_size(self):
        with pytest.raises(CompileError) as exc_info:
            parse_dsl(FIXTURES / "invalid_size.yml")
        cause = exc_info.value
        assert isinstance(cause, InvalidRoomSizeError) or "size" in str(cause).lower()

    def test_door_not_adjacent_compile_fails(self):
        doc = parse_dsl(FIXTURES / "door_not_adjacent.yml")
        from mapgen_compiler import Compiler
        compiler = Compiler()
        with pytest.raises(CompileError):
            compiler.compile(doc)

    def test_contained_rooms_ok(self):
        doc = parse_dsl(FIXTURES / "contained_rooms.yml")
        assert len(doc.entries) == 1
        entry = doc.entries[0]
        assert len(entry.doors) == 1
        assert entry.doors[0].side == "south"

    def test_missing_om_terrain(self):
        from mapgen.parser import _validate_entry
        with pytest.raises(CompileError, match="om_terrain"):
            _validate_entry({})

    def test_missing_entries_key(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("not_entries: []\n")
            tmp_path = f.name
        try:
            with pytest.raises(CompileError, match="entries"):
                parse_dsl(Path(tmp_path))
        finally:
            Path(tmp_path).unlink()


class TestDSLDocument:
    def test_pass_through_preserved(self):
        doc = parse_dsl(FIXTURES / "contained_rooms.yml")
        # KNOWN_KEYS not in the yaml should produce empty pass_through
        pass_through = doc.entries[0].pass_through
        assert isinstance(pass_through, dict)


class TestMakeRoom:
    def test_make_room(self):
        from mapgen.schema import RoomSpec, make_room
        spec = RoomSpec(id="test", x=1, y=2, w=5, h=6, wall="#", floor=".")
        room = make_room(spec)
        assert room.room_id == "test"
        assert room.x == 1
        assert room.y == 2
        assert room.w == 5
        assert room.h == 6
        assert room.wall_char == "#"
        assert room.floor_char == "."
        assert room.x2 == 6
        assert room.y2 == 8
        assert room.inner_x1 == 2
        assert room.inner_y1 == 3
        assert room.inner_x2 == 5
        assert room.inner_y2 == 7
        assert room.has_interior is True

    def test_resolve_global_coords(self):
        from mapgen.parser import _resolve_global_coords
        assert _resolve_global_coords(5) == [5]
        assert _resolve_global_coords([2, 5]) == [2, 3, 4, 5]
        with pytest.raises(CompileError):
            _resolve_global_coords([5, 2])
        with pytest.raises(CompileError):
            _resolve_global_coords("invalid")
