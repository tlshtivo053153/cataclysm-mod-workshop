from dataclasses import dataclass

from mapgen import DoorOverlapTooSmallError, RoomNotAdjacentError
from mapgen.grid import Grid


@dataclass
class Edge:
    direction: str
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
            self.x1 <= other.x1
            and self.x2 >= other.x2
            and self.y1 <= other.y1
            and self.y2 >= other.y2
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

    def adjacent_edge(self, other: "Room") -> Edge | None:
        if self.x2 == other.x1:
            overlap_start = max(self.y1, other.y1)
            overlap_end = min(self.y2, other.y2)
            if overlap_end > overlap_start:
                return Edge(
                    direction="east",
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                )
        if self.x1 == other.x2:
            overlap_start = max(self.y1, other.y1)
            overlap_end = min(self.y2, other.y2)
            if overlap_end > overlap_start:
                return Edge(
                    direction="west",
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                )
        if self.y2 == other.y1:
            overlap_start = max(self.x1, other.x1)
            overlap_end = min(self.x2, other.x2)
            if overlap_end > overlap_start:
                return Edge(
                    direction="south",
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                )
        if self.y1 == other.y2:
            overlap_start = max(self.x1, other.x1)
            overlap_end = min(self.x2, other.x2)
            if overlap_end > overlap_start:
                return Edge(
                    direction="north",
                    overlap_start=overlap_start,
                    overlap_end=overlap_end,
                )
        return None

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

    if edge.direction == "east":
        return (room_a.x2 - 1, coord)
    elif edge.direction == "west":
        return (room_a.x1, coord)
    elif edge.direction == "south":
        return (coord, room_a.y2 - 1)
    elif edge.direction == "north":
        return (coord, room_a.y1)
    else:
        raise RoomNotAdjacentError(
            f"Unknown edge direction: {edge.direction}"
        )


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

    if side == "south":
        overlap_length = inner.w
        if overlap_length < 2:
            raise DoorOverlapTooSmallError(
                f"Southern wall of '{inner.room_id}' has overlap {overlap_length}, need at least 2"
            )
        rel_offset = offset if offset is not None else inner.w // 2
        door_x = inner.x + min(rel_offset, inner.w - 1)
        door_y = inner.y2 - 1
        return (door_x, door_y)
    elif side == "north":
        overlap_length = inner.w
        if overlap_length < 2:
            raise DoorOverlapTooSmallError(
                f"Northern wall of '{inner.room_id}' has overlap {overlap_length}, need at least 2"
            )
        rel_offset = offset if offset is not None else inner.w // 2
        door_x = inner.x + min(rel_offset, inner.w - 1)
        door_y = inner.y1
        return (door_x, door_y)
    elif side == "east":
        overlap_length = inner.h
        if overlap_length < 2:
            raise DoorOverlapTooSmallError(
                f"Eastern wall of '{inner.room_id}' has overlap {overlap_length}, need at least 2"
            )
        rel_offset = offset if offset is not None else inner.h // 2
        door_x = inner.x2 - 1
        door_y = inner.y + min(rel_offset, inner.h - 1)
        return (door_x, door_y)
    elif side == "west":
        overlap_length = inner.h
        if overlap_length < 2:
            raise DoorOverlapTooSmallError(
                f"Western wall of '{inner.room_id}' has overlap {overlap_length}, need at least 2"
            )
        rel_offset = offset if offset is not None else inner.h // 2
        door_x = inner.x1
        door_y = inner.y + min(rel_offset, inner.h - 1)
        return (door_x, door_y)
    else:
        raise ValueError(f"Unknown side: '{side}'")
