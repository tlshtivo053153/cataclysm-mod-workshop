from dataclasses import dataclass
from typing import Callable, Literal

from mapgen import DoorOverlapTooSmallError, RoomNotAdjacentError
from mapgen.grid import Grid

_SIDE_CONFIG: dict[str, tuple[Callable[["Room"], int], Callable[["Room", int], tuple[int, int]]]] = {
    "south": (lambda r: r.w, lambda r, o: (r.x + min(o, r.w - 1), r.y2 - 1)),
    "north": (lambda r: r.w, lambda r, o: (r.x + min(o, r.w - 1), r.y1)),
    "east":  (lambda r: r.h, lambda r, o: (r.x2 - 1, r.y + min(o, r.h - 1))),
    "west":  (lambda r: r.h, lambda r, o: (r.x1, r.y + min(o, r.h - 1))),
}

_DIRECTION_NAMES: dict[str, str] = {
    "south": "Southern",
    "north": "Northern",
    "east": "Eastern",
    "west": "Western",
}

_EDGE_POS: dict[str, Callable[["Room", int], tuple[int, int]]] = {
    "east":  lambda r, c: (r.x2 - 1, c),
    "west":  lambda r, c: (r.x1, c),
    "south": lambda r, c: (c, r.y2 - 1),
    "north": lambda r, c: (c, r.y1),
}


@dataclass
class Edge:
    direction: Literal["north", "south", "east", "west"]
    overlap_start: int
    overlap_end: int

    @property
    def overlap_length(self) -> int:
        return self.overlap_end - self.overlap_start


class Room:
    def __init__(
        self,
        room_id: str,
        x: int,
        y: int,
        w: int,
        h: int,
        wall_char: str,
        floor_char: str,
    ) -> None:
        self.room_id = room_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.wall_char = wall_char
        self.floor_char = floor_char

    @property
    def x1(self) -> int:
        return self.x

    @property
    def y1(self) -> int:
        return self.y

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def inner_x1(self) -> int:
        return self.x + 1

    @property
    def inner_y1(self) -> int:
        return self.y + 1

    @property
    def inner_x2(self) -> int:
        return self.x + self.w - 1

    @property
    def inner_y2(self) -> int:
        return self.y + self.h - 1

    @property
    def has_interior(self) -> bool:
        return self.w > 2 and self.h > 2

    def intersects(self, other: "Room") -> bool:
        return (
            self.x1 < other.x2
            and self.x2 > other.x1
            and self.y1 < other.y2
            and self.y2 > other.y1
        )

    def contains(self, other: "Room") -> bool:
        return (
            self.x1 < other.x1
            and self.x2 > other.x2
            and self.y1 < other.y1
            and self.y2 > other.y2
            and not (
                self.x1 == other.x1
                and self.x2 == other.x2
                and self.y1 == other.y1
                and self.y2 == other.y2
            )
        )

    def is_adjacent_to(self, other: "Room") -> bool:
        horiz = (self.x2 == other.x1) or (self.x1 == other.x2)
        vert_overlap = self.y1 < other.y2 and self.y2 > other.y1
        if horiz and vert_overlap:
            return True

        vert = (self.y2 == other.y1) or (self.y1 == other.y2)
        horiz_overlap = self.x1 < other.x2 and self.x2 > other.x1
        return vert and horiz_overlap

    def _try_edge(
        self, other: "Room",
        axis_self: int, axis_other: int,
        overlap_a1: int, overlap_a2: int,
        overlap_b1: int, overlap_b2: int,
        direction: str,
    ) -> Edge | None:
        if axis_self != axis_other:
            return None
        start = max(overlap_a1, overlap_b1)
        end = min(overlap_a2, overlap_b2)
        if end > start:
            return Edge(direction=direction, overlap_start=start, overlap_end=end)
        return None

    def adjacent_edge(self, other: "Room") -> Edge | None:
        return (
            self._try_edge(other, self.x2, other.x1, self.y1, self.y2, other.y1, other.y2, "east")
            or self._try_edge(other, self.x1, other.x2, self.y1, self.y2, other.y1, other.y2, "west")
            or self._try_edge(other, self.y2, other.y1, self.x1, self.x2, other.x1, other.x2, "south")
            or self._try_edge(other, self.y1, other.y2, self.x1, self.x2, other.x1, other.x2, "north")
        )

    def draw(self, grid: Grid) -> None:
        grid.draw_rect_border(self.x, self.y, self.w, self.h, self.wall_char)
        if self.has_interior:
            grid.fill_rect(
                self.inner_x1, self.inner_y1,
                self.w - 2, self.h - 2,
                self.floor_char,
            )


def compute_door_position(
    room_a: Room,
    room_b: Room,
    offset: int | None = None,
) -> tuple[int, int]:
    edge = room_a.adjacent_edge(room_b)
    if edge is None:
        raise RoomNotAdjacentError(
            f"Rooms '{room_a.room_id}' and '{room_b.room_id}' are not adjacent"
        )
    if edge.overlap_length < 2:
        raise DoorOverlapTooSmallError(
            f"Overlap between '{room_a.room_id}' and '{room_b.room_id}' is {edge.overlap_length}, need at least 2"
        )

    pos = offset if offset is not None else edge.overlap_length // 2
    coord = edge.overlap_start + pos

    pos_fn = _EDGE_POS.get(edge.direction)
    if pos_fn is None:
        raise RoomNotAdjacentError(
            f"Unknown edge direction: {edge.direction}"
        )
    return pos_fn(room_a, coord)


def compute_contained_door_position(
    container: Room,
    inner: Room,
    offset: int | None = None,
    side: str = "south",
) -> tuple[int, int]:
    if not container.contains(inner):
        raise ValueError(
            f"Room '{container.room_id}' does not strictly contain '{inner.room_id}'"
        )

    config = _SIDE_CONFIG.get(side)
    if config is None:
        raise ValueError(f"Unknown side: '{side}'")

    get_overlap, get_pos = config
    overlap_length = get_overlap(inner)
    if overlap_length < 2:
        raise DoorOverlapTooSmallError(
            f"{_DIRECTION_NAMES.get(side, side.capitalize())} wall of '{inner.room_id}' "
            f"has overlap {overlap_length}, need at least 2"
        )
    offset_used = offset if offset is not None else overlap_length // 2
    return get_pos(inner, offset_used)
