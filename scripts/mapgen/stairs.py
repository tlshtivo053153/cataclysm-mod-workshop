"""Stair/ladder position collection and cross-level validation."""

from __future__ import annotations

from mapgen import CompileError, EntryContext, StairMismatchError
from mapgen.constants import STAIR_CHARS
from mapgen.schema import FeatureSpec, GlobalTile, RoomSpec
from mapgen.utils import resolve_global_coords


def collect_stair_positions(
    features: list[FeatureSpec],
    global_tiles: list[GlobalTile],
    rooms: dict[str, RoomSpec],
) -> set[tuple[int, int]]:
    """Return the set of intended stair/ladder positions declared in the spec.

    Positions are derived from feature tiles and global tiles whose character is
    in ``STAIR_CHARS``. For room-relative features, the room's origin is added.
    """
    positions: set[tuple[int, int]] = set()
    for feat in features:
        for tile in feat.tiles:
            if tile.char not in STAIR_CHARS:
                continue
            if feat.room is not None:
                room_spec = rooms.get(feat.room)
                if room_spec is None:
                    continue
                positions.add((room_spec.x + tile.x, room_spec.y + tile.y))
            else:
                positions.add((tile.x, tile.y))
    for gt in global_tiles:
        if gt.char not in STAIR_CHARS:
            continue
        x_vals = resolve_global_coords(gt.x)
        y_vals = resolve_global_coords(gt.y)
        for x in x_vals:
            for y in y_vals:
                positions.add((x, y))
    return positions


def validate_stairs(entries: list[EntryContext], canvas_size: int) -> list[CompileError]:
    """Validate stair/ladder position matching between adjacent z-levels.

    Entries are expected to be in z-order (top to bottom: roof → ground →
    underground). Adjacent entries in the list are treated as vertically
    adjacent z-levels.

    Placed stair positions are derived from each entry's intended
    ``stair_positions`` filtered to those cells whose grid character is still a
    stair char — equivalent to a full grid scan but without the O(canvas²) walk.
    """
    errors: list[CompileError] = []
    for i in range(len(entries) - 1):
        current = entries[i]
        next_entry = entries[i + 1]

        current_up: set[tuple[int, int]] = set()
        current_down: set[tuple[int, int]] = set()
        current_ladders: set[tuple[int, int]] = set()
        next_up: set[tuple[int, int]] = set()
        next_down: set[tuple[int, int]] = set()
        next_ladders: set[tuple[int, int]] = set()

        for x, y in current.stair_positions:
            if not current.grid.is_in_bounds(x, y):
                continue
            ch = current.grid.get(x, y)
            if ch not in STAIR_CHARS:
                continue
            if ch == "<":
                current_up.add((x, y))
            elif ch == ">":
                current_down.add((x, y))
            else:
                current_ladders.add((x, y))

        for x, y in next_entry.stair_positions:
            if not next_entry.grid.is_in_bounds(x, y):
                continue
            ch = next_entry.grid.get(x, y)
            if ch not in STAIR_CHARS:
                continue
            if ch == "<":
                next_up.add((x, y))
            elif ch == ">":
                next_down.add((x, y))
            else:
                next_ladders.add((x, y))

        if current_down and next_up and current_down != next_up:
            errors.append(
                StairMismatchError(
                    f"Stair mismatch between {current.om_terrain} (>) and "
                    f"{next_entry.om_terrain} (<): positions differ"
                )
            )

        if current_up and next_down and current_up != next_down:
            errors.append(
                StairMismatchError(
                    f"Stair mismatch between {current.om_terrain} (<) and "
                    f"{next_entry.om_terrain} (>): positions differ"
                )
            )

        if current_ladders and next_ladders and current_ladders != next_ladders:
            errors.append(
                StairMismatchError(
                    f"Ladder mismatch between {current.om_terrain} and "
                    f"{next_entry.om_terrain}: positions differ"
                )
            )

    return errors
