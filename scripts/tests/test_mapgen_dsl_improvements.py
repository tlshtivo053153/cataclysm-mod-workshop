import tempfile
from pathlib import Path

import pytest
from mapgen import (
    CompileError,
)
from mapgen.schema import parse_dsl
from mapgen_compiler import Compiler


def _parse_yml(yml: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(yml)
        temp_path = Path(f.name)
    try:
        return parse_dsl(temp_path)
    finally:
        temp_path.unlink()


def _compile_yml(yml: str):
    doc = _parse_yml(yml)
    compiler = Compiler()
    return compiler.compile(doc)


class TestInnerDimensions:
    def test_inner_w_converts_to_w_plus_2(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        x: 0
        y: 0
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        room = doc.entries[0].rooms[0]
        assert room.w == 8
        assert room.h == 6

    def test_inner_w_0_produces_w_2(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        x: 0
        y: 0
        inner_w: 0
        inner_h: 0
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        room = doc.entries[0].rooms[0]
        assert room.w == 2
        assert room.h == 2

    def test_error_both_w_and_inner_w(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        x: 0
        y: 0
        w: 8
        inner_w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="both 'w' and 'inner_w'"):
            _parse_yml(yml)

    def test_error_both_h_and_inner_h(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        x: 0
        y: 0
        h: 8
        inner_h: 4
        w: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="both 'h' and 'inner_h'"):
            _parse_yml(yml)

    def test_error_inner_w_negative(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        x: 0
        y: 0
        inner_w: -1
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="inner_w must be >= 0"):
            _parse_yml(yml)

    def test_compiler_uses_inner_dimensions(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "main"
        x: 0
        y: 0
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "."
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(0, 0) == "#"
        assert grid.get(1, 1) == "."
        assert grid.get(4, 4) == "."
        assert grid.get(5, 5) == "#"


class TestRelativePlacement:
    def test_right_of_places_east(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        kitchen = [r for r in doc.entries[0].rooms if r.id == "kitchen"][0]
        assert kitchen.x == 6
        assert kitchen.y == 0

    def test_left_of_places_west(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 6
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        left_of: "hall"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        kitchen = [r for r in doc.entries[0].rooms if r.id == "kitchen"][0]
        assert kitchen.x == 0
        assert kitchen.y == 0

    def test_above_places_north(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 6
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "attic"
        above: "hall"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        attic = [r for r in doc.entries[0].rooms if r.id == "attic"][0]
        assert attic.x == 0
        assert attic.y == 0

    def test_below_places_south(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "basement"
        below: "hall"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        basement = [r for r in doc.entries[0].rooms if r.id == "basement"][0]
        assert basement.x == 0
        assert basement.y == 6

    def test_gap_adds_spacing(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        gap: 2
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        kitchen = [r for r in doc.entries[0].rooms if r.id == "kitchen"][0]
        assert kitchen.x == 8

    def test_right_of_align_bottom(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 10
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        align: "bottom"
        w: 6
        h: 4
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        kitchen = [r for r in doc.entries[0].rooms if r.id == "kitchen"][0]
        assert kitchen.x == 6
        assert kitchen.y == 6

    def test_right_of_align_center(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 10
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        align: "center"
        w: 6
        h: 4
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        kitchen = [r for r in doc.entries[0].rooms if r.id == "kitchen"][0]
        assert kitchen.x == 6
        assert kitchen.y == 3

    def test_below_align_right(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 10
        h: 6
        wall: "#"
        floor: "."
      - id: "storage"
        below: "hall"
        align: "right"
        w: 6
        h: 4
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        storage = [r for r in doc.entries[0].rooms if r.id == "storage"][0]
        assert storage.x == 4
        assert storage.y == 6

    def test_below_align_center(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 10
        h: 6
        wall: "#"
        floor: "."
      - id: "storage"
        below: "hall"
        align: "center"
        w: 6
        h: 4
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        storage = [r for r in doc.entries[0].rooms if r.id == "storage"][0]
        assert storage.x == 2
        assert storage.y == 6

    def test_inside_align_south_east(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "outer"
        x: 0
        y: 0
        w: 10
        h: 10
        wall: "#"
        floor: "."
      - id: "inner"
        inside: "outer"
        align: "south-east"
        gap: 1
        w: 4
        h: 4
        wall: "@"
        floor: "x"
"""
        doc = _parse_yml(yml)
        inner = [r for r in doc.entries[0].rooms if r.id == "inner"][0]
        assert inner.x == 5
        assert inner.y == 5

    def test_inside_align_center(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "outer"
        x: 0
        y: 0
        w: 10
        h: 10
        wall: "#"
        floor: "."
      - id: "inner"
        inside: "outer"
        align: "center"
        w: 4
        h: 4
        wall: "@"
        floor: "x"
"""
        doc = _parse_yml(yml)
        inner = [r for r in doc.entries[0].rooms if r.id == "inner"][0]
        assert inner.x == 3
        assert inner.y == 3

    def test_error_mixing_new_keys_with_xy(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        x: 5
        y: 3
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="cannot mix new placement keys"):
            _parse_yml(yml)

    def test_error_mixing_new_keys_with_place(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        place:
          relative_to: "hall"
          side: "east"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="cannot mix new placement keys"):
            _parse_yml(yml)

    def test_error_multiple_targets(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        left_of: "hall"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="multiple placement targets"):
            _parse_yml(yml)

    def test_error_invalid_align(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        align: "zigzag"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="align.*must be"):
            _parse_yml(yml)

    def test_error_align_right_for_horizontal(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        align: "right"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="align.*right_of.*must be top, bottom, center"):
            _parse_yml(yml)

    def test_error_align_top_for_vertical(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "storage"
        below: "hall"
        align: "top"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="align.*below.*must be left, right, center"):
            _parse_yml(yml)

    def test_error_unknown_reference(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    rooms:
      - id: "hall"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "nonexistent"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="references unknown room"):
            _parse_yml(yml)


class TestLayoutGrid:
    def test_simple_1x2_layout(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [8, 8]
      rows: [8]
    layout:
      - [hall, kitchen]
    rooms:
      - id: hall
        inner_w: 6
        inner_h: 6
        wall: "#"
        floor: "."
      - id: kitchen
        inner_w: 6
        inner_h: 6
        wall: "#"
        floor: "="
"""
        doc = _parse_yml(yml)
        entry = doc.entries[0]
        hall = [r for r in entry.rooms if r.id == "hall"][0]
        kitchen = [r for r in entry.rooms if r.id == "kitchen"][0]
        assert hall.x == 0
        assert hall.y == 0
        assert hall.w == 8
        assert hall.h == 8
        assert kitchen.x == 8
        assert kitchen.y == 0
        assert kitchen.w == 8
        assert kitchen.h == 8

    def test_2x2_layout(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [8, 8]
      rows: [6, 6]
    layout:
      - [hall, kitchen]
      - [closet, bathroom]
    rooms:
      - id: hall
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "."
      - id: kitchen
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "="
      - id: closet
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: ","
      - id: bathroom
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "o"
"""
        doc = _parse_yml(yml)
        entry = doc.entries[0]
        rooms = {r.id: r for r in entry.rooms}
        assert rooms["hall"].x == 0
        assert rooms["hall"].y == 0
        assert rooms["hall"].w == 8
        assert rooms["hall"].h == 6
        assert rooms["kitchen"].x == 8
        assert rooms["kitchen"].y == 0
        assert rooms["kitchen"].w == 8
        assert rooms["kitchen"].h == 6
        assert rooms["closet"].x == 0
        assert rooms["closet"].y == 6
        assert rooms["closet"].w == 8
        assert rooms["closet"].h == 6
        assert rooms["bathroom"].x == 8
        assert rooms["bathroom"].y == 6
        assert rooms["bathroom"].w == 8
        assert rooms["bathroom"].h == 6

    def test_span_merged_cells(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [8, 8, 8]
      rows: [6, 6]
    layout:
      - [hall, hall, storage]
      - [kitchen, living, storage]
    rooms:
      - id: hall
        inner_w: 14
        inner_h: 4
        wall: "#"
        floor: "."
      - id: storage
        inner_w: 6
        inner_h: 10
        wall: "#"
        floor: "="
      - id: kitchen
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: ","
      - id: living
        inner_w: 6
        inner_h: 4
        wall: "#"
        floor: "o"
"""
        doc = _parse_yml(yml)
        entry = doc.entries[0]
        rooms = {r.id: r for r in entry.rooms}
        assert rooms["hall"].x == 0
        assert rooms["hall"].y == 0
        assert rooms["hall"].w == 16
        assert rooms["hall"].h == 6
        assert rooms["storage"].x == 16
        assert rooms["storage"].y == 0
        assert rooms["storage"].w == 8
        assert rooms["storage"].h == 12
        assert rooms["kitchen"].x == 0
        assert rooms["kitchen"].y == 6
        assert rooms["kitchen"].w == 8
        assert rooms["kitchen"].h == 6
        assert rooms["living"].x == 8
        assert rooms["living"].y == 6
        assert rooms["living"].w == 8
        assert rooms["living"].h == 6

    def test_layout_room_can_omit_size(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [6, 6]
      rows: [6]
    layout:
      - [a, b]
    rooms:
      - id: a
        wall: "#"
        floor: "."
      - id: b
        wall: "="
        floor: ","
"""
        doc = _parse_yml(yml)
        entry = doc.entries[0]
        rooms = {r.id: r for r in entry.rooms}
        assert rooms["a"].w == 6
        assert rooms["a"].h == 6
        assert rooms["b"].w == 6
        assert rooms["b"].h == 6

    def test_error_layout_cell_unknown_room(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [8, 8]
      rows: [8]
    layout:
      - [hall, nonexistent]
    rooms:
      - id: hall
        inner_w: 6
        inner_h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="references unknown room.*nonexistent"):
            _parse_yml(yml)

    def test_error_room_not_in_layout(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [8]
      rows: [8]
    layout:
      - [hall]
    rooms:
      - id: hall
        inner_w: 6
        inner_h: 6
        wall: "#"
        floor: "."
      - id: forgotten
        inner_w: 6
        inner_h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="not placed in layout"):
            _parse_yml(yml)

    def test_error_layout_dimensions_mismatch(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [8, 8, 8]
      rows: [8]
    layout:
      - [hall, kitchen]
    rooms:
      - id: hall
        inner_w: 6
        inner_h: 6
        wall: "#"
        floor: "."
      - id: kitchen
        inner_w: 6
        inner_h: 6
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="has 2 cells.*3 columns"):
            _parse_yml(yml)

    def test_error_layout_exceeds_canvas(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [20, 20]
      rows: [20]
    layout:
      - [hall, kitchen]
    rooms:
      - id: hall
        wall: "#"
        floor: "."
      - id: kitchen
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="exceeds mapgen canvas"):
            _parse_yml(yml)

    def test_error_conflicting_w_with_layout_computed(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [8]
      rows: [8]
    layout:
      - [hall]
    rooms:
      - id: hall
        w: 10
        h: 8
        wall: "#"
        floor: "."
"""
        with pytest.raises(CompileError, match="specified w=10 conflicts with layout-computed"):
            _parse_yml(yml)

    def test_layout_compiles_to_valid_grid(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    canvas:
      cols: [6, 6]
      rows: [6]
    layout:
      - [hall, kitchen]
    rooms:
      - id: hall
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "."
      - id: kitchen
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "="
"""
        entries = _compile_yml(yml)
        assert len(entries) == 1
        grid = entries[0].grid
        assert grid.get(0, 0) == "#"
        assert grid.get(1, 1) == "."
        assert grid.get(6, 0) == "#"
        assert grid.get(7, 1) == "="


class TestAutoDoors:
    def test_auto_doors_between_adjacent_rooms(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    default_door_char: "="
    rooms:
      - id: "left"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "right"
        x: 6
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(5, 3) == "="

    def test_auto_doors_with_inner_dimensions(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    rooms:
      - id: "left"
        x: 0
        y: 0
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "."
      - id: "right"
        x: 6
        y: 0
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "."
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(5, 3) == "+"

    def test_auto_doors_with_layout(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    default_door_char: "="
    canvas:
      cols: [6, 6]
      rows: [6]
    layout:
      - [hall, kitchen]
    rooms:
      - id: hall
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "."
      - id: kitchen
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: ","
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(5, 3) == "="

    def test_auto_doors_no_duplicate_existing(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    default_door_char: "+"
    rooms:
      - id: "left"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "right"
        x: 6
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
    doors:
      - from: "left"
        to: "right"
        char: "X"
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(5, 3) == "X"

    def test_auto_doors_no_passthrough_leak(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    rooms:
      - id: "left"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "right"
        x: 6
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        doc = _parse_yml(yml)
        entry = doc.entries[0]
        assert "auto_doors" not in entry.pass_through
        assert "default_door_char" not in entry.pass_through


class TestCombinedFeatures:
    def test_inner_w_plus_right_of_plus_auto_doors(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    default_door_char: "="
    rooms:
      - id: "hall"
        x: 0
        y: 0
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "."
      - id: "kitchen"
        right_of: "hall"
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: ","
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(5, 3) == "="

    def test_layout_with_inner_w_auto_doors_and_features(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    default_door_char: "="
    canvas:
      cols: [6, 6]
      rows: [6]
    layout:
      - [hall, kitchen]
    rooms:
      - id: hall
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: "."
      - id: kitchen
        inner_w: 4
        inner_h: 4
        wall: "#"
        floor: ","
    features:
      - room: kitchen
        tiles:
          - char: "H"
            x: 1
            y: 1
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(5, 3) == "="
        assert grid.get(7, 1) == "H"

    def test_vertical_adjacent_auto_doors(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    default_door_char: "="
    rooms:
      - id: "top"
        x: 0
        y: 0
        w: 6
        h: 6
        wall: "#"
        floor: "."
      - id: "bottom"
        below: "top"
        w: 6
        h: 6
        wall: "#"
        floor: "."
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(3, 5) == "="

    def test_gap_nonzero_prevents_auto_doors(self):
        yml = """\
entries:
  - om_terrain: "test"
    fill_ter: "t_floor"
    auto_doors: true
    default_door_char: "="
    rooms:
      - id: "left"
        x: 0
        y: 0
        w: 4
        h: 6
        wall: "#"
        floor: "."
      - id: "right"
        x: 6
        y: 0
        w: 4
        h: 6
        wall: "#"
        floor: "."
"""
        entries = _compile_yml(yml)
        grid = entries[0].grid
        assert grid.get(2, 3) == "."
        assert grid.get(5, 3) == " "
