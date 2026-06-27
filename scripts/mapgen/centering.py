"""Global bounding-box computation and centering offset application."""

from __future__ import annotations

from mapgen.schema import EntrySpec
from mapgen.utils import resolve_global_coords

_Bounds = tuple[int | None, int | None, int | None, int | None]


def _update_bbox(
    bounds: _Bounds,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> _Bounds:
    min_x, min_y, max_x, max_y = bounds
    if min_x is None or x1 < min_x:
        min_x = x1
    if min_y is None or y1 < min_y:
        min_y = y1
    if max_x is None or x2 > max_x:
        max_x = x2
    if max_y is None or y2 > max_y:
        max_y = y2
    return min_x, min_y, max_x, max_y


def compute_global_bbox(entries: list[EntrySpec]) -> tuple[int, int, int, int] | None:
    bounds: _Bounds = (None, None, None, None)
    for spec in entries:
        for room in spec.rooms.values():
            bounds = _update_bbox(bounds, room.x, room.y, room.x + room.w, room.y + room.h)
        for feat in spec.features:
            if feat.room is None:
                for tile in feat.tiles:
                    bounds = _update_bbox(bounds, tile.x, tile.y, tile.x + 1, tile.y + 1)
        for gt in spec.global_tiles:
            x_vals = resolve_global_coords(gt.x)
            y_vals = resolve_global_coords(gt.y)
            bounds = _update_bbox(bounds, x_vals[0], y_vals[0], x_vals[-1] + 1, y_vals[-1] + 1)
    min_x, min_y, max_x, max_y = bounds
    if min_x is None or min_y is None or max_x is None or max_y is None:
        return None
    return min_x, min_y, max_x, max_y


def apply_centering(entries: list[EntrySpec], dx: int, dy: int) -> None:
    for spec in entries:
        for room in spec.rooms.values():
            room.shift(dx, dy)
        for feat in spec.features:
            if feat.room is None:
                for tile in feat.tiles:
                    tile.shift(dx, dy)
        for gt in spec.global_tiles:
            gt.shift(dx, dy)
