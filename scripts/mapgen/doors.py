"""Explicit and automatic door placement."""

from __future__ import annotations

from mapgen import (
    CompileError,
    DoorNotOnWallError,
    DoorOverlapTooSmallError,
    RoomNotAdjacentError,
    Warning,
)
from mapgen.constants import FALLBACK_DOOR_CHAR
from mapgen.grid import Grid
from mapgen.room import (
    DEFAULT_DOOR_SIDE,
    SIDES,
    Room,
    compute_contained_door_position,
    compute_door_position,
)
from mapgen.schema import DoorSpec, EntrySpec


def resolve_door_offset(door: DoorSpec, room_a: Room, room_b: Room) -> int | None:
    if door.position is None:
        return door.offset
    if room_a.contains(room_b) or room_b.contains(room_a):
        inner = room_b if room_a.contains(room_b) else room_a
        side = door.side if door.side else DEFAULT_DOOR_SIDE
        config = SIDES.get(side)
        if config is None:
            return door.offset
        overlap_length = config.overlap_length(inner)
    else:
        edge = room_a.adjacent_edge(room_b)
        if edge is None:
            edge = room_b.adjacent_edge(room_a)
        if edge is None:
            return door.offset
        overlap_length = edge.overlap_length

    if overlap_length <= 0:
        raise CompileError(
            f"Door between '{door.from_room}' and '{door.to_room}': "
            f"no overlapping edge to place door (position='{door.position}')"
        )
    if door.position == "left":
        return 0
    elif door.position == "center":
        return overlap_length // 2
    elif door.position == "right":
        return overlap_length - 1
    return door.offset


class DoorPlacer:
    """Places explicit doors declared in the spec and auto-generated doors."""

    def place_doors(
        self,
        spec: EntrySpec,
        rooms: dict[str, Room],
        grid: Grid,
        warnings: list[Warning],
    ) -> None:
        for door in spec.doors:
            room_a = rooms[door.from_room]
            room_b = rooms[door.to_room]
            offset = resolve_door_offset(door, room_a, room_b)
            if room_a.contains(room_b) or room_b.contains(room_a):
                container = room_a if room_a.contains(room_b) else room_b
                inner = room_b if room_a.contains(room_b) else room_a
                side = door.side if door.side else DEFAULT_DOOR_SIDE
                door_x, door_y = compute_contained_door_position(
                    container,
                    inner,
                    offset=offset,
                    side=side,
                )
            elif room_a.is_adjacent_to(room_b):
                try:
                    door_x, door_y = compute_door_position(
                        room_a,
                        room_b,
                        offset=offset,
                    )
                except RoomNotAdjacentError:
                    door_x, door_y = compute_door_position(
                        room_b,
                        room_a,
                        offset=offset,
                    )
            else:
                raise RoomNotAdjacentError(
                    f"Rooms '{door.from_room}' and '{door.to_room}' are neither adjacent nor contained"
                )
            cell_char = grid.get(door_x, door_y)
            wall_chars = {room_a.wall_char, room_b.wall_char}
            if cell_char not in wall_chars:
                raise DoorNotOnWallError(
                    f"Door at ({door_x},{door_y}) between '{door.from_room}' and "
                    f"'{door.to_room}' is not on a wall (found '{cell_char}')"
                )
            if door.char in wall_chars:
                warnings.append(
                    Warning(
                        code="invisible_door",
                        message=f"Door char '{door.char}' matches wall char "
                        f"of room '{door.from_room}' or '{door.to_room}'",
                    )
                )
            grid.place(door_x, door_y, door.char)

    def generate_auto_doors(
        self,
        rooms: dict[str, Room],
        grid: Grid,
        spec: EntrySpec,
        warnings: list[Warning],
    ) -> None:
        room_list = list(rooms.values())
        explicit_pairs: set[tuple[str, str]] = set()
        for door in spec.doors:
            explicit_pairs.add((door.from_room, door.to_room))
            explicit_pairs.add((door.to_room, door.from_room))

        suppressed_pairs: set[tuple[str, str]] = set()
        for pair in spec.no_door:
            suppressed_pairs.add(pair)
            suppressed_pairs.add((pair[1], pair[0]))

        for i in range(len(room_list)):
            for j in range(i + 1, len(room_list)):
                a = room_list[i]
                b = room_list[j]
                pair = (a.room_id, b.room_id)
                if pair in explicit_pairs or pair in suppressed_pairs:
                    continue

                if a.is_adjacent_to(b):
                    try:
                        door_x, door_y = compute_door_position(a, b)
                    except (RoomNotAdjacentError, DoorOverlapTooSmallError):
                        try:
                            door_x, door_y = compute_door_position(b, a)
                        except (RoomNotAdjacentError, DoorOverlapTooSmallError):
                            continue

                    self._place_auto_door(
                        grid,
                        a,
                        b,
                        door_x,
                        door_y,
                        spec.default_door_char,
                        warnings,
                    )

        for i in range(len(room_list)):
            for j in range(len(room_list)):
                if i == j:
                    continue
                container = room_list[i]
                inner = room_list[j]
                if not container.contains(inner):
                    continue
                pair = (container.room_id, inner.room_id)
                if pair in explicit_pairs or pair in suppressed_pairs:
                    continue

                for side in ("south", "north", "east", "west"):
                    try:
                        door_x, door_y = compute_contained_door_position(
                            container,
                            inner,
                            side=side,
                        )
                    except (ValueError, DoorOverlapTooSmallError):
                        continue

                    if grid.get(door_x, door_y) not in {container.wall_char, inner.wall_char}:
                        continue

                    self._place_auto_door(
                        grid,
                        container,
                        inner,
                        door_x,
                        door_y,
                        spec.default_door_char,
                        warnings,
                    )
                    break

    @staticmethod
    def _place_auto_door(
        grid: Grid,
        room_a: Room,
        room_b: Room,
        door_x: int,
        door_y: int,
        default_door_char: str,
        warnings: list[Warning],
    ) -> None:
        wall_chars = {room_a.wall_char, room_b.wall_char}
        cell_char = grid.get(door_x, door_y)
        if cell_char not in wall_chars:
            return

        door_char = default_door_char
        if door_char in wall_chars:
            door_char = FALLBACK_DOOR_CHAR
        if door_char in wall_chars:
            warnings.append(
                Warning(
                    code="invisible_door",
                    message=f"Auto-door char '{door_char}' matches wall char "
                    f"of room '{room_a.room_id}' or '{room_b.room_id}'",
                )
            )

        grid.place(door_x, door_y, door_char)
