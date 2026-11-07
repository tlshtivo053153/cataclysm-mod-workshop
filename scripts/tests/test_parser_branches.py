"""Branch tests for mapgen/parser.py uncovered lines (E-4 gap fill)."""

import pytest
from mapgen import CompileError
from mapgen.parser import parse_dsl


def _write(tmp_path, text, name="t.yml"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


BASE = """entries:
  - om_terrain: "t_x"
    fill_ter: "t_floor"
    palette: ["fortified_shelter"]
    rooms:
"""


def _room(rid="a", extra=""):
    return f"""      - id: "{rid}"
        w: 4
        h: 4
        wall: "#"
        floor: "."
{extra}"""


def _two_valid(extra=""):
    # second room anchored via right_of so entry parses; extra appended at entry level
    return BASE + _room("a") + _room("b", '        right_of: "a"\n') + extra


class TestDetectPlacementKeys:
    def test_no_target(self, tmp_path):
        yml = BASE + _room("a", '        align: "top"\n')
        with pytest.raises(CompileError, match="must specify one of"):
            parse_dsl(_write(tmp_path, yml))

    def test_multiple_targets(self, tmp_path):
        yml = BASE + _room("a", '        right_of: "b"\n        left_of: "c"\n') + _room("b") + _room(
            "c"
        )
        with pytest.raises(CompileError, match="exactly one"):
            parse_dsl(_write(tmp_path, yml))

    def test_negative_gap(self, tmp_path):
        yml = BASE + _room("a") + _room("b", '        right_of: "a"\n        gap: -1\n')
        with pytest.raises(CompileError, match="'gap' must be >= 0"):
            parse_dsl(_write(tmp_path, yml))

    def test_none_without_keys(self, tmp_path):
        yml = BASE + _room("a")
        assert parse_dsl(_write(tmp_path, yml)) is not None


class TestPlacementViaParse:
    def test_xy_rejected(self, tmp_path):
        yml = BASE + _room("a", "        x: 0\n")
        with pytest.raises(CompileError, match="no longer supported"):
            parse_dsl(_write(tmp_path, yml))

    def test_place_rejected(self, tmp_path):
        yml = BASE + _room("a", '        place: {"x": 0}\n')
        with pytest.raises(CompileError, match="no longer supported"):
            parse_dsl(_write(tmp_path, yml))

    def test_circular_dependency(self, tmp_path):
        yml = BASE + _room("a", '        right_of: "b"\n') + _room("b", '        right_of: "a"\n')
        with pytest.raises(CompileError, match="[Cc]ircular"):
            parse_dsl(_write(tmp_path, yml))


class TestRoomValidation:
    def test_dict_value_must_be_mapping(self, tmp_path):
        yml = """entries:
  - om_terrain: "t_x"
    fill_ter: "t_floor"
    palette: ["fortified_shelter"]
    rooms:
      a: "not-a-mapping"
"""
        with pytest.raises(CompileError, match="value must be a mapping"):
            parse_dsl(_write(tmp_path, yml))

    def test_room_missing_id(self, tmp_path):
        yml = BASE + '      - w: 4\n        h: 4\n        wall: "#"\n        floor: "."\n'
        with pytest.raises(CompileError, match="missing required field: id"):
            parse_dsl(_write(tmp_path, yml))

    def test_rooms_must_be_list_or_mapping(self, tmp_path):
        yml = BASE.replace("    rooms:\n", '    rooms: "nope"\n')
        with pytest.raises(CompileError, match="'rooms' must be a list or mapping"):
            parse_dsl(_write(tmp_path, yml))

    def test_inner_h_negative(self, tmp_path):
        yml = BASE + '      - id: "a"\n        inner_h: -2\n        wall: "#"\n        floor: "."\n'
        with pytest.raises(CompileError, match="inner_h must be >= 0"):
            parse_dsl(_write(tmp_path, yml))

    def test_wall_floor_required(self, tmp_path):
        yml = BASE + '      - id: "a"\n        w: 4\n        h: 4\n'
        with pytest.raises(CompileError, match="wall or floor"):
            parse_dsl(_write(tmp_path, yml))

    def test_relative_missing_wh(self, tmp_path):
        yml = (
            BASE
            + '      - id: "a"\n        wall: "#"\n        floor: "."\n        right_of: "b"\n'
            + _room("b")
        )
        with pytest.raises(CompileError, match="missing required field"):
            parse_dsl(_write(tmp_path, yml))

    def test_door_missing_field(self, tmp_path):
        yml = _two_valid('    doors:\n      - from: "a"\n')
        with pytest.raises(CompileError, match="Door missing required field"):
            parse_dsl(_write(tmp_path, yml))


class TestNoDoorAndCanvas:
    def test_no_door_must_be_pair(self, tmp_path):
        with pytest.raises(CompileError, match="must be lists of 2"):
            parse_dsl(_write(tmp_path, _two_valid('    no_door: ["only-one"]\n')))

    def test_no_door_unknown_room(self, tmp_path):
        with pytest.raises(CompileError, match="unknown room"):
            parse_dsl(_write(tmp_path, _two_valid('    no_door: [["a", "ghost"]]\n')))

    def test_layout_requires_canvas(self, tmp_path):
        # layout path needs rooms valid under layout (w/h optional); use layout rooms
        yml = """entries:
  - om_terrain: "t_x"
    fill_ter: "t_floor"
    palette: ["fortified_shelter"]
    rooms:
      - id: "a"
        wall: "#"
        floor: "."
    layout:
      - room: a
"""
        with pytest.raises(CompileError, match="requires 'canvas'"):
            parse_dsl(_write(tmp_path, yml))

    def test_top_level_must_be_mapping(self, tmp_path):
        with pytest.raises(CompileError, match="must be a mapping"):
            parse_dsl(_write(tmp_path, "- just\n- list\n"))

    def test_entries_must_be_list(self, tmp_path):
        with pytest.raises(CompileError, match="'entries' must be a list"):
            parse_dsl(_write(tmp_path, "entries: {}\n"))

    def test_canvas_must_be_mapping(self, tmp_path):
        with pytest.raises(CompileError, match="'canvas' must be a mapping"):
            parse_dsl(_write(tmp_path, "entries: []\ncanvas: 5\n"))

    def test_canvas_missing_keys(self, tmp_path):
        with pytest.raises(CompileError, match="both 'w' and 'h'"):
            parse_dsl(_write(tmp_path, "entries: []\ncanvas: {w: 2}\n"))

    def test_canvas_non_integer(self, tmp_path):
        with pytest.raises(CompileError, match="must be integers"):
            parse_dsl(_write(tmp_path, "entries: []\ncanvas: {w: big, h: 2}\n"))

    def test_canvas_must_be_square(self, tmp_path):
        with pytest.raises(CompileError, match="must be square"):
            parse_dsl(_write(tmp_path, "entries: []\ncanvas: {w: 2, h: 3}\n"))

    def test_global_tile_missing_field(self, tmp_path):
        with pytest.raises(CompileError, match="missing required field"):
            parse_dsl(_write(tmp_path, _two_valid("    global:\n      - {x: 0}\n")))

    def test_center_must_be_boolean(self, tmp_path):
        with pytest.raises(CompileError, match="'center' must be a boolean"):
            parse_dsl(_write(tmp_path, 'entries: []\ncenter: "yes"\n'))


class TestInputValidation:
    def test_wall_two_chars(self, tmp_path):
        yml = BASE + '      - id: "a"\n        w: 4\n        h: 4\n        wall: "##"\n        floor: "."\n'
        with pytest.raises(CompileError, match="must be a single character"):
            parse_dsl(_write(tmp_path, yml))

    def test_floor_two_chars(self, tmp_path):
        yml = BASE + '      - id: "a"\n        w: 4\n        h: 4\n        wall: "#"\n        floor: ".."\n'
        with pytest.raises(CompileError, match="must be a single character"):
            parse_dsl(_write(tmp_path, yml))

    def test_rooms_list_string_entry(self, tmp_path):
        yml = BASE + '      - "a"\n'
        with pytest.raises(CompileError):
            parse_dsl(_write(tmp_path, yml))

    def test_gap_string(self, tmp_path):
        yml = BASE + '      - id: "a"\n        w: 4\n        h: 4\n        wall: "#"\n        floor: "."\n' + '      - id: "b"\n        w: 2\n        h: 2\n        wall: "#"\n        floor: "."\n        right_of: "a"\n        gap: "x"\n'
        with pytest.raises(CompileError, match="must be an integer"):
            parse_dsl(_write(tmp_path, yml))

    def test_contained_door_bad_side(self, tmp_path):
        yml = _two_valid(
            '    doors:\n      - {from: "a", to: "b", char: "+", side: "up"}\n'
        )
        with pytest.raises(CompileError, match="invalid side"):
            parse_dsl(_write(tmp_path, yml))

    def test_feature_char_two_chars(self, tmp_path):
        yml = _two_valid('    features:\n      - room: "a"\n        tiles:\n          - {char: "ab", x: 0, y: 0}\n')
        with pytest.raises(CompileError, match="must be a single character"):
            parse_dsl(_write(tmp_path, yml))

    def test_global_char_two_chars(self, tmp_path):
        yml = _two_valid("    global:\n      - {char: ab, x: 0, y: 0}\n")
        with pytest.raises(CompileError, match="must be a single character"):
            parse_dsl(_write(tmp_path, yml))


class TestExtraBranches:
    def test_first_room_missing_wh(self, tmp_path):
        yml = BASE + '      - id: "a"\n        wall: "#"\n        floor: "."\n'
        with pytest.raises(CompileError, match="missing required field"):
            parse_dsl(_write(tmp_path, yml))

    def test_second_room_without_placement(self, tmp_path):
        yml = BASE + _room("a") + _room("b")
        with pytest.raises(CompileError, match="must specify a relative placement"):
            parse_dsl(_write(tmp_path, yml))

    def test_door_invalid_position(self, tmp_path):
        yml = _two_valid('    doors:\n      - {from: "a", to: "b", char: "+", position: "top"}\n')
        with pytest.raises(CompileError, match="invalid position"):
            parse_dsl(_write(tmp_path, yml))

    def test_door_unknown_from_room(self, tmp_path):
        from mapgen import RoomNotAdjacentError

        yml = _two_valid('    doors:\n      - {from: "ghost", to: "a", char: "+"}\n')
        with pytest.raises(RoomNotAdjacentError, match="unknown room"):
            parse_dsl(_write(tmp_path, yml))

    def test_feature_tile_missing_field(self, tmp_path):
        yml = _two_valid("    features:\n      - room: a\n        tiles:\n          - {char: c}\n")
        with pytest.raises(CompileError, match="missing required field"):
            parse_dsl(_write(tmp_path, yml))

    def test_feature_global_out_of_grid(self, tmp_path):
        from mapgen import FeatureOutOfGridError

        yml = _two_valid("    features:\n      - tiles:\n          - {char: c, x: 999, y: 999}\n")
        with pytest.raises(FeatureOutOfGridError):
            parse_dsl(_write(tmp_path, yml))

    def test_global_tile_out_of_bounds(self, tmp_path):
        from mapgen import FeatureOutOfGridError

        yml = _two_valid("    global:\n      - {char: c, x: 999, y: 0}\n")
        with pytest.raises(FeatureOutOfGridError):
            parse_dsl(_write(tmp_path, yml))

    def test_no_door_first_unknown(self, tmp_path):
        with pytest.raises(CompileError, match="unknown room.*ghost"):
            parse_dsl(_write(tmp_path, _two_valid('    no_door: [["ghost", "a"]]\n')))

    def test_no_door_happy_path(self, tmp_path):
        doc = parse_dsl(_write(tmp_path, _two_valid('    no_door: [["a", "b"]]\n')))
        assert doc.entries[0].no_door == [("a", "b")]

    def test_canvas_cols_requires_layout(self, tmp_path):
        yml = _two_valid("").replace(
            "    rooms:",
            "    canvas:\n      cols: 2\n      rows: 2\n    rooms:",
        )
        with pytest.raises(CompileError, match="requires 'layout'"):
            parse_dsl(_write(tmp_path, yml))

    def test_inside_invalid_align(self, tmp_path):
        yml = (
            BASE
            + _room("a")
            + '      - id: "b"\n        w: 2\n        h: 2\n        wall: "#"\n'
            + '        floor: "."\n        inside: "a"\n        align: "diagonal"\n'
        )
        with pytest.raises(CompileError, match="invalid 'align'"):
            parse_dsl(_write(tmp_path, yml))

    def test_partial_overlap_error(self, tmp_path):
        from mapgen import RoomOverlapError
        from mapgen.parser import _validate_room_overlaps

        doc = parse_dsl(_write(tmp_path, _two_valid("")))
        entry = doc.entries[0]
        # Adjacent rooms (gap 0) pass without error.
        _validate_room_overlaps(entry)
        # Shift into partial overlap: intersects, not adjacent/contained.
        entry.rooms["b"].x = 2
        with pytest.raises(RoomOverlapError, match="partially overlap"):
            _validate_room_overlaps(entry)
