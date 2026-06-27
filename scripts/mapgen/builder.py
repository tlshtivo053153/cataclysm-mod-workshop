"""Grid construction: draws rooms, places doors/features, merges walls."""

from __future__ import annotations

from mapgen import Warning
from mapgen.constants import STAIR_CHARS
from mapgen.doors import DoorPlacer
from mapgen.grid import EMPTY_CELL_CHAR, MAPGEN_SIZE, Grid
from mapgen.room import Room
from mapgen.schema import EntrySpec, make_room
from mapgen.utils import resolve_global_coords
from mapgen.walls import merge_adjacent_walls


def _build_containment_map(rooms: dict[str, Room]) -> dict[str, list[Room]]:
    containment: dict[str, list[Room]] = {}
    room_list = list(rooms.values())
    for i in range(len(room_list)):
        for j in range(len(room_list)):
            if i == j:
                continue
            if room_list[i].contains(room_list[j]):
                containment.setdefault(room_list[i].room_id, []).append(room_list[j])
    return containment


def _is_inside_contained_room(
    ax: int,
    ay: int,
    parent: Room,
    rooms: dict[str, Room],
    containment: dict[str, list[Room]],
) -> bool:
    children = containment.get(parent.room_id)
    if children is None:
        return False
    return any(other.x1 <= ax < other.x2 and other.y1 <= ay < other.y2 for other in children)


class GridBuilder:
    """Builds the character grid for a single entry spec."""

    def __init__(self) -> None:
        self._doors = DoorPlacer()

    def build(
        self,
        spec: EntrySpec,
        canvas_size: int = MAPGEN_SIZE,
    ) -> tuple[Grid, dict[str, Room], list[Warning]]:
        warnings: list[Warning] = []
        grid = Grid(width=canvas_size, height=canvas_size, fill_char=EMPTY_CELL_CHAR)
        rooms = self._draw_rooms(spec, grid)
        containment = _build_containment_map(rooms)
        self._doors.place_doors(spec, rooms, grid, warnings)
        if spec.auto_doors:
            self._doors.generate_auto_doors(rooms, grid, spec, warnings)
        merge_adjacent_walls(rooms, grid)
        self._place_features(spec, rooms, grid, containment)
        self._place_global_tiles(spec, grid)
        return grid, rooms, warnings

    @staticmethod
    def _draw_rooms(spec: EntrySpec, grid: Grid) -> dict[str, Room]:
        rooms: dict[str, Room] = {}
        for spec_room in spec.rooms.values():
            room = make_room(spec_room)
            rooms[spec_room.id] = room
            room.draw(grid)
        return rooms

    @staticmethod
    def _place_features(
        spec: EntrySpec,
        rooms: dict[str, Room],
        grid: Grid,
        containment: dict[str, list[Room]],
    ) -> None:
        for feat in spec.features:
            for tile in feat.tiles:
                if feat.room is not None:
                    room = rooms[feat.room]
                    ax = room.x + tile.x
                    ay = room.y + tile.y
                    if _is_inside_contained_room(ax, ay, room, rooms, containment):
                        continue
                else:
                    ax = tile.x
                    ay = tile.y
                grid.place(ax, ay, tile.char)

    @staticmethod
    def _place_global_tiles(spec: EntrySpec, grid: Grid) -> None:
        for gt in spec.global_tiles:
            x_vals = resolve_global_coords(gt.x)
            y_vals = resolve_global_coords(gt.y)
            for x in x_vals:
                for y in y_vals:
                    grid.place(x, y, gt.char)


def collect_passable_chars(
    rooms: dict[str, Room],
    spec: EntrySpec,
) -> set[str]:
    """Compute the set of passable characters for reachability checks."""
    passable_chars: set[str] = {EMPTY_CELL_CHAR}
    wall_chars_all: set[str] = {r.wall_char for r in rooms.values()}
    for room in rooms.values():
        passable_chars.add(room.floor_char)
    for door in spec.doors:
        if door.char not in wall_chars_all:
            passable_chars.add(door.char)
    if spec.auto_doors:
        door_char = spec.default_door_char
        if door_char not in wall_chars_all:
            passable_chars.add(door_char)
    for feat in spec.features:
        for tile in feat.tiles:
            if tile.char in STAIR_CHARS:
                passable_chars.add(tile.char)
    for gt in spec.global_tiles:
        if gt.char in STAIR_CHARS:
            passable_chars.add(gt.char)
    return passable_chars
