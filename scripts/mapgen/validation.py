from __future__ import annotations

from mapgen import RoomOverlapError
from mapgen.schema import EntrySpec, make_room


def _validate_room_overlaps(entry: EntrySpec) -> None:
    room_values = list(entry.rooms.values())
    rooms = [make_room(s) for s in room_values]
    for i in range(len(rooms)):
        for j in range(i + 1, len(rooms)):
            a = rooms[i]
            b = rooms[j]
            if not a.intersects(b):
                continue
            if a.contains(b) or b.contains(a):
                continue
            if a.is_adjacent_to(b):
                continue
            raise RoomOverlapError(
                f"Rooms '{a.room_id}' (x={a.x},y={a.y},w={a.w},h={a.h}) and "
                f"'{b.room_id}' (x={b.x},y={b.y},w={b.w},h={b.h}) partially overlap — "
                f"adjust one room's position or size to eliminate overlap. "
                f"Try: move '{a.room_id}' x to {b.x + b.w} or '{b.room_id}' x to {a.x + a.w}, "
                f"or reduce width of one room."
            )
