import pytest
from mapgen.room import Room, Edge, compute_door_position, compute_contained_door_position
from mapgen import RoomNotAdjacentError, DoorOverlapTooSmallError


class TestRoomIntersects:
    def test_intersects_true(self):
        a = Room("a", 0, 0, 5, 5, "#", ".")
        b = Room("b", 3, 3, 5, 5, "#", ".")
        assert a.intersects(b)
        assert b.intersects(a)

    def test_intersects_false_apart(self):
        a = Room("a", 0, 0, 3, 3, "#", ".")
        b = Room("b", 5, 5, 3, 3, "#", ".")
        assert not a.intersects(b)

    def test_intersects_false_shared_edge(self):
        a = Room("a", 0, 0, 3, 3, "#", ".")
        b = Room("b", 3, 0, 3, 3, "#", ".")
        assert not a.intersects(b)

    def test_intersects_false_corner_touch(self):
        a = Room("a", 0, 0, 3, 3, "#", ".")
        b = Room("b", 3, 3, 3, 3, "#", ".")
        assert not a.intersects(b)


class TestRoomContains:
    def test_contains_strict_true(self):
        outer = Room("outer", 0, 0, 10, 10, "#", ".")
        inner = Room("inner", 2, 2, 4, 4, "#", ".")
        assert outer.contains(inner)

    def test_contains_shared_wall_false(self):
        a = Room("a", 0, 0, 5, 5, "#", ".")
        b = Room("b", 0, 0, 5, 5, "#", ".")
        assert not a.contains(b)

    def test_contains_partial_false(self):
        outer = Room("outer", 0, 0, 10, 10, "#", ".")
        inner = Room("inner", 8, 8, 5, 5, "#", ".")
        assert not outer.contains(inner)

    def test_contains_touching_left_wall_false(self):
        outer = Room("outer", 0, 0, 10, 10, "#", ".")
        inner = Room("inner", 0, 2, 3, 3, "#", ".")
        assert not outer.contains(inner)


class TestRoomIsAdjacentTo:
    def test_adjacent_east_west(self):
        a = Room("a", 0, 2, 4, 4, "#", ".")
        b = Room("b", 4, 2, 4, 4, "#", ".")
        assert a.is_adjacent_to(b)

    def test_adjacent_north_south(self):
        a = Room("a", 2, 0, 4, 4, "#", ".")
        b = Room("b", 2, 4, 4, 4, "#", ".")
        assert a.is_adjacent_to(b)

    def test_adjacent_partial_overlap(self):
        a = Room("a", 0, 1, 5, 4, "#", ".")
        b = Room("b", 5, 0, 4, 5, "#", ".")
        assert a.is_adjacent_to(b)

    def test_not_adjacent_corner_only(self):
        a = Room("a", 0, 0, 3, 3, "#", ".")
        b = Room("b", 3, 3, 3, 3, "#", ".")
        assert not a.is_adjacent_to(b)

    def test_not_adjacent_separated(self):
        a = Room("a", 0, 0, 3, 3, "#", ".")
        b = Room("b", 5, 0, 3, 3, "#", ".")
        assert not a.is_adjacent_to(b)


class TestAdjacentEdge:
    def test_edge_east(self):
        a = Room("a", 0, 2, 4, 4, "#", ".")
        b = Room("b", 4, 2, 4, 4, "#", ".")
        e = a.adjacent_edge(b)
        assert e is not None
        assert e.direction == "east"
        assert e.overlap_length == 4

    def test_edge_south(self):
        a = Room("a", 2, 0, 4, 4, "#", ".")
        b = Room("b", 2, 4, 4, 4, "#", ".")
        e = a.adjacent_edge(b)
        assert e is not None
        assert e.direction == "south"
        assert e.overlap_length == 4

    def test_edge_none(self):
        a = Room("a", 0, 0, 3, 3, "#", ".")
        b = Room("b", 5, 5, 3, 3, "#", ".")
        assert a.adjacent_edge(b) is None


class TestComputeDoorPosition:
    def test_basic_adjacent(self):
        a = Room("a", 0, 2, 4, 4, "#", ".")
        b = Room("b", 4, 2, 4, 4, "#", ".")
        x, y = compute_door_position(a, b)
        assert 3 <= x <= 4
        assert 2 <= y <= 5

    def test_with_offset(self):
        a = Room("a", 0, 2, 4, 4, "#", ".")
        b = Room("b", 4, 2, 4, 4, "#", ".")
        x, y = compute_door_position(a, b, offset=1)
        assert x == 3
        assert y == 3

    def test_not_adjacent_raises(self):
        a = Room("a", 0, 0, 3, 3, "#", ".")
        b = Room("b", 5, 5, 3, 3, "#", ".")
        with pytest.raises(RoomNotAdjacentError):
            compute_door_position(a, b)

    def test_overlap_too_small_raises(self):
        a = Room("a", 0, 2, 4, 4, "#", ".")
        b = Room("b", 4, 3, 1, 1, "#", ".")
        with pytest.raises(DoorOverlapTooSmallError):
            compute_door_position(a, b)


class TestComputeContainedDoorPosition:
    def test_south_wall(self):
        container = Room("outer", 0, 0, 10, 10, "#", ".")
        inner = Room("inner", 3, 3, 4, 4, "#", ".")
        x, y = compute_contained_door_position(container, inner, side="south")
        assert x == 5
        assert y == 6

    def test_north_wall(self):
        container = Room("outer", 0, 0, 10, 10, "#", ".")
        inner = Room("inner", 3, 3, 4, 4, "#", ".")
        x, y = compute_contained_door_position(container, inner, side="north")
        assert x == 5
        assert y == 3

    def test_with_offset(self):
        container = Room("outer", 0, 0, 10, 10, "#", ".")
        inner = Room("inner", 3, 3, 4, 4, "#", ".")
        x, y = compute_contained_door_position(container, inner, offset=0, side="south")
        assert y == 6

    def test_not_contained_raises(self):
        outer = Room("outer", 0, 0, 5, 5, "#", ".")
        inner = Room("inner", 8, 8, 3, 3, "#", ".")
        with pytest.raises(ValueError):
            compute_contained_door_position(outer, inner)
