import pytest
from mapgen import DoorOverlapTooSmallError, RoomNotAdjacentError
from mapgen.grid import Grid
from mapgen.room import Room, compute_contained_door_position, compute_door_position


class TestRoomProperties:
    def test_basic_properties(self):
        r = Room("r1", x=3, y=5, w=6, h=4, wall_char="#", floor_char=".")
        assert r.x1 == 3
        assert r.y1 == 5
        assert r.x2 == 9
        assert r.y2 == 9
        assert r.w == 6
        assert r.h == 4
        assert r.room_id == "r1"

    def test_inner_properties(self):
        r = Room("r1", x=3, y=5, w=6, h=4, wall_char="#", floor_char=".")
        assert r.inner_x1 == 4
        assert r.inner_y1 == 6
        assert r.inner_x2 == 8
        assert r.inner_y2 == 8

    def test_has_interior_true(self):
        r = Room("r1", x=0, y=0, w=4, h=4, wall_char="#", floor_char=".")
        assert r.has_interior is True

    def test_has_interior_false_w1(self):
        r = Room("r1", x=0, y=0, w=1, h=10, wall_char="#", floor_char=".")
        assert r.has_interior is False

    def test_has_interior_false_h1(self):
        r = Room("r1", x=0, y=0, w=10, h=1, wall_char="#", floor_char=".")
        assert r.has_interior is False

    def test_has_interior_false_w2(self):
        r = Room("r1", x=0, y=0, w=2, h=5, wall_char="#", floor_char=".")
        assert r.has_interior is False

    def test_has_interior_false_h2(self):
        r = Room("r1", x=0, y=0, w=5, h=2, wall_char="#", floor_char=".")
        assert r.has_interior is False


class TestRoomGeometry:
    def test_intersects_full_overlap(self):
        a = Room("a", x=2, y=2, w=4, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=3, y=3, w=3, h=3, wall_char="#", floor_char=".")
        assert a.intersects(b) is True
        assert b.intersects(a) is True

    def test_intersects_edge_touch(self):
        a = Room("a", x=0, y=0, w=4, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=4, y=0, w=4, h=4, wall_char="#", floor_char=".")
        assert a.intersects(b) is False

    def test_intersects_corner_touch(self):
        a = Room("a", x=0, y=0, w=4, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=4, y=4, w=4, h=4, wall_char="#", floor_char=".")
        assert a.intersects(b) is False

    def test_intersects_separate(self):
        a = Room("a", x=0, y=0, w=3, h=3, wall_char="#", floor_char=".")
        b = Room("b", x=5, y=5, w=3, h=3, wall_char="#", floor_char=".")
        assert a.intersects(b) is False

    def test_contains_strict(self):
        outer = Room("outer", x=0, y=0, w=10, h=10, wall_char="#", floor_char=".")
        inner = Room("inner", x=2, y=2, w=4, h=4, wall_char="#", floor_char=".")
        assert outer.contains(inner) is True
        assert inner.contains(outer) is False

    def test_contains_equal_is_false(self):
        a = Room("a", x=0, y=0, w=5, h=5, wall_char="#", floor_char=".")
        b = Room("b", x=0, y=0, w=5, h=5, wall_char="#", floor_char=".")
        assert a.contains(b) is False
        assert b.contains(a) is False

    def test_contains_larger_is_false(self):
        outer = Room("outer", x=0, y=0, w=10, h=10, wall_char="#", floor_char=".")
        inner = Room("inner", x=2, y=2, w=4, h=4, wall_char="#", floor_char=".")
        assert inner.contains(outer) is False

    def test_is_adjacent_to_east(self):
        a = Room("a", x=0, y=0, w=4, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=4, y=1, w=4, h=2, wall_char="#", floor_char=".")
        assert a.is_adjacent_to(b) is True
        assert b.is_adjacent_to(a) is True

    def test_is_adjacent_to_west(self):
        a = Room("a", x=4, y=0, w=4, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=0, y=1, w=4, h=2, wall_char="#", floor_char=".")
        assert a.is_adjacent_to(b) is True

    def test_is_adjacent_to_south(self):
        a = Room("a", x=0, y=0, w=4, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=1, y=4, w=2, h=4, wall_char="#", floor_char=".")
        assert a.is_adjacent_to(b) is True

    def test_is_adjacent_to_north(self):
        a = Room("a", x=0, y=4, w=4, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=1, y=0, w=2, h=4, wall_char="#", floor_char=".")
        assert a.is_adjacent_to(b) is True

    def test_is_not_adjacent(self):
        a = Room("a", x=0, y=0, w=3, h=3, wall_char="#", floor_char=".")
        b = Room("b", x=5, y=5, w=3, h=3, wall_char="#", floor_char=".")
        assert a.is_adjacent_to(b) is False

    def test_is_not_adjacent_corner_only(self):
        a = Room("a", x=0, y=0, w=3, h=3, wall_char="#", floor_char=".")
        b = Room("b", x=3, y=3, w=3, h=3, wall_char="#", floor_char=".")
        assert a.is_adjacent_to(b) is False

    def test_adjacent_edge_east(self):
        a = Room("a", x=0, y=2, w=4, h=6, wall_char="#", floor_char=".")
        b = Room("b", x=4, y=2, w=4, h=4, wall_char="#", floor_char=".")
        edge = a.adjacent_edge(b)
        assert edge is not None
        assert edge.direction == "east"
        assert edge.overlap_start == 2
        assert edge.overlap_end == 6
        assert edge.overlap_length == 4

    def test_adjacent_edge_west(self):
        a = Room("a", x=4, y=2, w=4, h=6, wall_char="#", floor_char=".")
        b = Room("b", x=0, y=2, w=4, h=4, wall_char="#", floor_char=".")
        edge = a.adjacent_edge(b)
        assert edge is not None
        assert edge.direction == "west"
        assert edge.overlap_start == 2
        assert edge.overlap_end == 6
        assert edge.overlap_length == 4

    def test_adjacent_edge_north(self):
        a = Room("a", x=2, y=4, w=6, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=2, y=0, w=4, h=4, wall_char="#", floor_char=".")
        edge = a.adjacent_edge(b)
        assert edge is not None
        assert edge.direction == "north"
        assert edge.overlap_start == 2
        assert edge.overlap_end == 6

    def test_adjacent_edge_south(self):
        a = Room("a", x=2, y=0, w=6, h=4, wall_char="#", floor_char=".")
        b = Room("b", x=2, y=4, w=4, h=4, wall_char="#", floor_char=".")
        edge = a.adjacent_edge(b)
        assert edge is not None
        assert edge.direction == "south"
        assert edge.overlap_start == 2
        assert edge.overlap_end == 6

    def test_adjacent_edge_none(self):
        a = Room("a", x=0, y=0, w=3, h=3, wall_char="#", floor_char=".")
        b = Room("b", x=5, y=5, w=3, h=3, wall_char="#", floor_char=".")
        assert a.adjacent_edge(b) is None


class TestRoomDraw:
    def test_draw_room_with_interior(self):
        grid = Grid()
        r = Room("r1", x=2, y=3, w=5, h=4, wall_char="#", floor_char=".")
        r.draw(grid)
        assert grid.get(2, 3) == "#"
        assert grid.get(6, 3) == "#"
        assert grid.get(2, 6) == "#"
        assert grid.get(6, 6) == "#"
        assert grid.get(4, 4) == "."
        assert grid.get(0, 0) == " "

    def test_draw_room_without_interior_w1(self):
        grid = Grid()
        r = Room("r1", x=5, y=5, w=1, h=5, wall_char="|", floor_char=".")
        r.draw(grid)
        for dy in range(5):
            assert grid.get(5, 5 + dy) == "|"

    def test_draw_room_without_interior_h1(self):
        grid = Grid()
        r = Room("r1", x=5, y=5, w=5, h=1, wall_char="-", floor_char=".")
        r.draw(grid)
        for dx in range(5):
            assert grid.get(5 + dx, 5) == "-"


class TestComputeDoorPosition:
    def test_center_default(self):
        a = Room("a", x=0, y=0, w=4, h=6, wall_char="#", floor_char=".")
        b = Room("b", x=4, y=1, w=4, h=4, wall_char="#", floor_char=".")
        dx, dy = compute_door_position(a, b)
        assert dx == 3
        assert dy == 3

    def test_explicit_offset(self):
        a = Room("a", x=0, y=0, w=4, h=10, wall_char="#", floor_char=".")
        b = Room("b", x=4, y=0, w=4, h=5, wall_char="#", floor_char=".")
        dx, dy = compute_door_position(a, b, offset=1)
        assert dx == 3
        assert dy == 1

    def test_overlap_too_small(self):
        a = Room("a", x=0, y=0, w=2, h=1, wall_char="#", floor_char=".")
        b = Room("b", x=2, y=0, w=2, h=1, wall_char="#", floor_char=".")
        with pytest.raises(DoorOverlapTooSmallError):
            compute_door_position(a, b)

    def test_not_adjacent(self):
        a = Room("a", x=0, y=0, w=3, h=3, wall_char="#", floor_char=".")
        b = Room("b", x=5, y=5, w=3, h=3, wall_char="#", floor_char=".")
        with pytest.raises(RoomNotAdjacentError):
            compute_door_position(a, b)


class TestComputeContainedDoorPosition:
    def test_south_wall_default(self):
        container = Room("outer", x=0, y=0, w=10, h=10, wall_char="#", floor_char=".")
        inner = Room("inner", x=2, y=2, w=6, h=4, wall_char="#", floor_char=".")
        dx, dy = compute_contained_door_position(container, inner)
        assert dx == 5
        assert dy == 5

    def test_explicit_side_north(self):
        container = Room("outer", x=0, y=0, w=10, h=10, wall_char="#", floor_char=".")
        inner = Room("inner", x=2, y=2, w=6, h=4, wall_char="#", floor_char=".")
        dx, dy = compute_contained_door_position(container, inner, side="north")
        assert dx == 5
        assert dy == 2

    def test_not_contained(self):
        outer = Room("outer", x=0, y=0, w=3, h=3, wall_char="#", floor_char=".")
        inner = Room("inner", x=5, y=5, w=3, h=3, wall_char="#", floor_char=".")
        with pytest.raises(ValueError):
            compute_contained_door_position(outer, inner)

    def test_overlap_too_small(self):
        container = Room("outer", x=0, y=0, w=10, h=10, wall_char="#", floor_char=".")
        inner = Room("inner", x=2, y=2, w=1, h=3, wall_char="#", floor_char=".")
        with pytest.raises(DoorOverlapTooSmallError):
            compute_contained_door_position(container, inner, side="south")
