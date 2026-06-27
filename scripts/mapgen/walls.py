"""Adjacent double-wall merging between neighboring rooms."""

from __future__ import annotations

from mapgen.grid import Grid
from mapgen.room import Edge, Room


def _resolve_wall_merge(a: Room, b: Room, edge: Edge) -> tuple[Room, Room]:
    """Determine which room keeps its wall and which gets the wall floored over.

    For east-west adjacency, the eastern room's wall is replaced. For
    north-south adjacency, the southern room's wall is replaced. Returns
    ``(room_to_keep_wall, room_to_replace_wall)``.
    """
    direction_replace: dict[str, tuple[Room, Room]] = {
        "east": (a, b),
        "west": (b, a),
        "south": (a, b),
        "north": (b, a),
    }
    return direction_replace[edge.direction]


def merge_adjacent_walls(rooms: dict[str, Room], grid: Grid) -> None:
    """Replace one side of double walls between adjacent rooms with floor.

    Only the interior portion of the wall (excluding corners) is merged. Tiles
    already replaced by doors are left intact.
    """
    room_list = list(rooms.values())
    for i in range(len(room_list)):
        for j in range(i + 1, len(room_list)):
            a = room_list[i]
            b = room_list[j]
            if not a.is_adjacent_to(b):
                continue

            edge = a.adjacent_edge(b)
            if edge is None:
                continue

            _keeper, replacer = _resolve_wall_merge(a, b, edge)

            if edge.direction in ("east", "west"):
                lo = max(edge.overlap_start, replacer.y + 1)
                hi = min(edge.overlap_end, replacer.y + replacer.h - 1)
                x = replacer.x1
                for y in range(lo, hi):
                    if grid.get(x, y) == replacer.wall_char:
                        grid.place(x, y, replacer.floor_char)
            else:
                lo = max(edge.overlap_start, replacer.x + 1)
                hi = min(edge.overlap_end, replacer.x + replacer.w - 1)
                y = replacer.y1
                for x in range(lo, hi):
                    if grid.get(x, y) == replacer.wall_char:
                        grid.place(x, y, replacer.floor_char)
