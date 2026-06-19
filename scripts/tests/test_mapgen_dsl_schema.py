from pathlib import Path

import pytest
from mapgen import (
    CompileError,
    DuplicateRoomIdError,
    FeatureOutOfGridError,
    FeatureOutOfRoomError,
    OutOfBoundsError,
    RoomNotAdjacentError,
)
from mapgen.parser import parse_dsl

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestMapgenDslSchema:
    def test_parse_single_room(self):
        doc = parse_dsl(FIXTURES / "single_room.yml")
        assert len(doc.entries) == 1
        entry = doc.entries[0]
        assert entry.om_terrain == "test_single"
        assert entry.fill_ter == "t_floor"
        assert entry.palette == ["fortified_shelter"]
        assert len(entry.rooms) == 1
        r = entry.rooms["main"]
        assert r.id == "main"
        assert r.x == 0
        assert r.y == 0
        assert r.w == 8
        assert r.h == 8
        assert r.wall == "#"
        assert r.floor == "."

    def test_parse_two_rooms_with_door(self):
        doc = parse_dsl(FIXTURES / "two_rooms_door.yml")
        entry = doc.entries[0]
        assert len(entry.rooms) == 2
        assert len(entry.doors) == 1
        d = entry.doors[0]
        assert d.from_room == "left"
        assert d.to_room == "right"
        assert d.char == "="
        assert d.offset is None

    def test_parse_nested_rooms(self):
        doc = parse_dsl(FIXTURES / "nested_rooms.yml")
        entry = doc.entries[0]
        assert len(entry.rooms) == 2
        assert len(entry.doors) == 0

    def test_parse_contained_room_door(self):
        doc = parse_dsl(FIXTURES / "contained_room_door.yml")
        entry = doc.entries[0]
        assert len(entry.doors) == 1
        d = entry.doors[0]
        assert d.side == "south"

    def test_parse_door_offset(self):
        doc = parse_dsl(FIXTURES / "door_offset.yml")
        entry = doc.entries[0]
        d = entry.doors[0]
        assert d.offset == 2

    def test_parse_features(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        w: 6
        h: 6
        wall: "#"
        floor: "."
    features:
      - room: "main"
        tiles:
          - char: ">"
            x: 2
            y: 3
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            doc = parse_dsl(temp_path)
            entry = doc.entries[0]
            assert len(entry.features) == 1
            feat = entry.features[0]
            assert feat.room == "main"
            assert len(feat.tiles) == 1
            assert feat.tiles[0].char == ">"
            assert feat.tiles[0].x == 2
            assert feat.tiles[0].y == 3
        finally:
            temp_path.unlink()

    def test_parse_global_tiles_fixture(self):
        doc = parse_dsl(FIXTURES / "global_tiles.yml")
        entry = doc.entries[0]
        assert len(entry.global_tiles) == 2
        assert entry.global_tiles[0].x == [0, 23]
        assert entry.global_tiles[0].y == 0

    def test_parse_pass_through(self):
        doc = parse_dsl(FIXTURES / "pass_through.yml")
        entry = doc.entries[0]
        assert "terrain" in entry.pass_through
        assert "furniture" in entry.pass_through
        assert "place_items" in entry.pass_through
        assert "place_zones" in entry.pass_through
        assert entry.pass_through["terrain"] == {".": "t_floor"}

    def test_parse_multi_entry(self):
        doc = parse_dsl(FIXTURES / "multi_level_stair_ok.yml")
        assert len(doc.entries) == 2
        assert doc.entries[0].om_terrain == "shelter_e"
        assert doc.entries[1].om_terrain == "shelter_e_under"

    def test_error_room_out_of_bounds(self):
        with pytest.raises(OutOfBoundsError):
            parse_dsl(FIXTURES / "room_out_of_bounds.yml")

    def test_error_room_id_duplicate(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "a"
        w: 3
        h: 3
        wall: "#"
        floor: "."
      - id: "a"
        right_of: "a"
        w: 3
        h: 3
        wall: "#"
        floor: "."
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            with pytest.raises(DuplicateRoomIdError):
                parse_dsl(temp_path)
        finally:
            temp_path.unlink()

    def test_error_door_references_unknown_room(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "a"
        w: 3
        h: 3
        wall: "#"
        floor: "."
    doors:
      - from: "a"
        to: "nonexistent"
        char: "="
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            with pytest.raises(RoomNotAdjacentError):
                parse_dsl(temp_path)
        finally:
            temp_path.unlink()

    def test_error_feature_unknown_room(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        w: 5
        h: 5
        wall: "#"
        floor: "."
    features:
      - room: "nonexistent"
        tiles:
          - char: ">"
            x: 1
            y: 1
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            with pytest.raises(FeatureOutOfRoomError):
                parse_dsl(temp_path)
        finally:
            temp_path.unlink()

    def test_error_feature_tile_outside_room(self):
        with pytest.raises(FeatureOutOfRoomError):
            parse_dsl(FIXTURES / "feature_out_of_room.yml")

    def test_error_global_tile_out_of_bounds(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        w: 5
        h: 5
        wall: "#"
        floor: "."
    global:
      - char: "&"
        x: 30
        y: 5
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            with pytest.raises(FeatureOutOfGridError):
                parse_dsl(temp_path)
        finally:
            temp_path.unlink()

    def test_error_door_side_for_adjacent_rooms(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "a"
        w: 4
        h: 6
        wall: "#"
        floor: "."
      - id: "b"
        right_of: "a"
        w: 4
        h: 6
        wall: "#"
        floor: "."
    doors:
      - from: "a"
        to: "b"
        char: "="
        side: "east"
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            with pytest.raises(CompileError):
                parse_dsl(temp_path)
        finally:
            temp_path.unlink()

    def test_error_invalid_room_size(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "a"
        w: 0
        h: 5
        wall: "#"
        floor: "."
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            with pytest.raises(CompileError):
                parse_dsl(temp_path)
        finally:
            temp_path.unlink()

    def test_parse_rooms_as_mapping(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      main:
        w: 6
        h: 6
        wall: "#"
        floor: "."
      kitchen:
        right_of: "main"
        w: 4
        h: 4
        wall: "#"
        floor: "."
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yml)
            temp_path = Path(f.name)
        try:
            doc = parse_dsl(temp_path)
            entry = doc.entries[0]
            assert isinstance(entry.rooms, dict)
            assert "main" in entry.rooms
            assert "kitchen" in entry.rooms
            assert entry.rooms["main"].w == 6
            assert entry.rooms["kitchen"].x == 6
        finally:
            temp_path.unlink()
