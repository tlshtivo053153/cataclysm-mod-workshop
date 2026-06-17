from __future__ import annotations

from mapgen import CompileError, InvalidRoomSizeError, OutOfBoundsError
from mapgen.schema import PlaceSpec, RoomSpec


def resolve_room_placement(
    place: PlaceSpec,
    w: int,
    h: int,
    resolved: dict[str, RoomSpec],
) -> tuple[int, int]:
    if place.relative_to is not None and place.inside is not None:
        raise CompileError(
            "Room 'place' must specify exactly one of 'relative_to' or 'inside', not both"
        )
    if place.relative_to is None and place.inside is None:
        raise CompileError(
            "Room 'place' must specify either 'relative_to' or 'inside'"
        )
    if place.margin < 0:
        raise CompileError(
            f"Room 'place.margin' must be >= 0, got {place.margin}"
        )

    if place.relative_to is not None:
        ref = resolved.get(place.relative_to)
        if ref is None:
            raise CompileError(
                f"Room 'place.relative_to' references unknown room: '{place.relative_to}'"
            )
        side = place.side
        if side == "east":
            x = ref.x + ref.w + place.margin
            y = _resolve_align_y(place, ref, h)
        elif side == "west":
            x = ref.x - w - place.margin
            y = _resolve_align_y(place, ref, h)
        elif side == "south":
            y = ref.y + ref.h + place.margin
            x = _resolve_align_x(place, ref, w)
        elif side == "north":
            y = ref.y - h - place.margin
            x = _resolve_align_x(place, ref, w)
        else:
            raise CompileError(
                f"Invalid side: '{side}' — must be north, south, east, or west"
            )
    elif place.inside is not None:
        ref = resolved.get(place.inside)
        if ref is None:
            raise CompileError(
                f"Room 'place.inside' references unknown room: '{place.inside}'"
            )
        if w + 2 * place.margin > ref.w or h + 2 * place.margin > ref.h:
            raise CompileError(
                f"Room with w={w},h={h} and margin={place.margin} does not fit inside "
                f"'{place.inside}' (w={ref.w},h={ref.h})"
            )
        if place._align_style is not None:
            x, y = _resolve_inside_compound_align(place, ref, w, h)
        else:
            anchor = place.anchor
            if anchor == "south":
                x = ref.x + place.margin
                y = ref.y + ref.h - h - place.margin
            elif anchor == "east":
                x = ref.x + ref.w - w - place.margin
                y = ref.y + place.margin
            elif anchor in ("north", "west"):
                x = ref.x + place.margin
                y = ref.y + place.margin
            else:
                raise CompileError(
                    f"Invalid anchor: '{anchor}' — must be north, south, east, or west"
                )
    else:
        raise CompileError("Unreachable: place must have relative_to or inside")  # pragma: no cover

    return x, y


def _resolve_align_y(place: PlaceSpec, ref: RoomSpec, h: int) -> int:
    style = place._align_style
    if style is None:
        return ref.y
    if style == "top":
        return ref.y
    elif style == "bottom":
        return ref.y + ref.h - h
    elif style in ("center", "middle"):
        return ref.y + (ref.h - h) // 2
    return ref.y


def _resolve_align_x(place: PlaceSpec, ref: RoomSpec, w: int) -> int:
    style = place._align_style
    if style is None:
        return ref.x
    if style == "left":
        return ref.x
    elif style == "right":
        return ref.x + ref.w - w
    elif style in ("center", "middle"):
        return ref.x + (ref.w - w) // 2
    return ref.x


def _resolve_inside_compound_align(
    place: PlaceSpec, ref: RoomSpec, w: int, h: int,
) -> tuple[int, int]:
    style = place._align_style or "top-left"
    margin = place.margin

    compound_map: dict[str, tuple[int, int]] = {
        "top":          (ref.x + margin, ref.y + margin),
        "north":        (ref.x + margin, ref.y + margin),
        "bottom":       (ref.x + margin, ref.y + ref.h - h - margin),
        "south":        (ref.x + margin, ref.y + ref.h - h - margin),
        "left":         (ref.x + margin, ref.y + margin),
        "west":         (ref.x + margin, ref.y + margin),
        "right":        (ref.x + ref.w - w - margin, ref.y + margin),
        "east":         (ref.x + ref.w - w - margin, ref.y + margin),
        "top-left":     (ref.x + margin, ref.y + margin),
        "north-west":   (ref.x + margin, ref.y + margin),
        "top-right":    (ref.x + ref.w - w - margin, ref.y + margin),
        "north-east":   (ref.x + ref.w - w - margin, ref.y + margin),
        "bottom-left":  (ref.x + margin, ref.y + ref.h - h - margin),
        "south-west":   (ref.x + margin, ref.y + ref.h - h - margin),
        "bottom-right": (ref.x + ref.w - w - margin, ref.y + ref.h - h - margin),
        "south-east":   (ref.x + ref.w - w - margin, ref.y + ref.h - h - margin),
        "center":       (ref.x + (ref.w - w) // 2, ref.y + (ref.h - h) // 2),
        "middle":       (ref.x + (ref.w - w) // 2, ref.y + (ref.h - h) // 2),
    }

    if style in compound_map:
        return compound_map[style]

    raise CompileError(
        f"Invalid align style for inside placement: '{style}'"
    )


def _resolve_entry_layout(
    layout_canvas: dict,
    layout_matrix: list[list[str]],
    rooms: dict[str, RoomSpec],
    canvas_size: int,
) -> None:
    if not isinstance(layout_canvas, dict):
        raise CompileError("'canvas' for layout must be a mapping with 'cols' and 'rows' keys")
    cols: list[int] = layout_canvas.get("cols", [])
    rows: list[int] = layout_canvas.get("rows", [])
    if not cols or not rows:
        raise CompileError("'canvas' for layout must contain non-empty 'cols' and 'rows' lists")
    if not isinstance(cols, list) or not all(isinstance(c, int) and c > 0 for c in cols):
        raise CompileError("'canvas.cols' must be a list of positive integers")
    if not isinstance(rows, list) or not all(isinstance(r, int) and r > 0 for r in rows):
        raise CompileError("'canvas.rows' must be a list of positive integers")

    total_w = sum(cols)
    total_h = sum(rows)
    if total_w > canvas_size or total_h > canvas_size:
        raise CompileError(
            f"Layout canvas ({total_w}x{total_h}) exceeds mapgen canvas ({canvas_size}x{canvas_size}) — "
            f"reduce column widths or row heights"
        )

    if not isinstance(layout_matrix, list) or not layout_matrix:
        raise CompileError("'layout' must be a non-empty list of rows")
    for i, row in enumerate(layout_matrix):
        if not isinstance(row, list) or len(row) != len(cols):
            raise CompileError(
                f"Layout row {i} has {len(row) if isinstance(row, list) else 'non-list'} cells, "
                f"but {len(cols)} columns are defined in canvas.cols"
            )

    if len(layout_matrix) != len(rows):
        raise CompileError(
            f"Layout has {len(layout_matrix)} rows, but {len(rows)} rows are defined in canvas.rows"
        )

    room_cells: dict[str, tuple[int, int, int, int]] = {}
    for ri, row in enumerate(layout_matrix):
        for ci, cell_id in enumerate(row):
            if cell_id not in rooms:
                raise CompileError(
                    f"Layout cell [{ri}][{ci}] references unknown room: '{cell_id}'"
                )
            if cell_id not in room_cells:
                room_cells[cell_id] = (ci, ri, ci + 1, ri + 1)
            else:
                c_min, r_min, c_max, r_max = room_cells[cell_id]
                room_cells[cell_id] = (
                    min(c_min, ci), min(r_min, ri),
                    max(c_max, ci + 1), max(r_max, ri + 1),
                )

    all_room_ids = set(rooms.keys())
    for cell_id in all_room_ids:
        if cell_id not in room_cells:
            raise CompileError(
                f"Room '{cell_id}' is defined in rooms but not placed in layout matrix — "
                f"all rooms must be assigned to at least one cell in layout"
            )

    for cell_id, (c_min, r_min, c_max, r_max) in room_cells.items():
        computed_w = sum(cols[c_min:c_max])
        computed_h = sum(rows[r_min:r_max])
        computed_x = sum(cols[:c_min])
        computed_y = sum(rows[:r_min])

        spec = rooms[cell_id]
        if spec.w > 0 and spec.h > 0:
            if spec.w != computed_w:
                raise CompileError(
                    f"Room '{cell_id}': specified w={spec.w} conflicts with layout-computed "
                    f"width {computed_w} (spans columns {c_min}-{c_max - 1}). "
                    f"Omit 'w'/'h' or 'inner_w'/'inner_h' to use layout-derived sizes."
                )
            if spec.h != computed_h:
                raise CompileError(
                    f"Room '{cell_id}': specified h={spec.h} conflicts with layout-computed "
                    f"height {computed_h} (spans rows {r_min}-{r_max - 1}). "
                    f"Omit 'w'/'h' or 'inner_w'/'inner_h' to use layout-derived sizes."
                )

        spec.w = computed_w
        spec.h = computed_h
        spec.x = computed_x
        spec.y = computed_y
        spec.layout_resolved = True

        if spec.w < 1 or spec.h < 1:
            raise InvalidRoomSizeError(
                f"Room '{cell_id}': layout-computed size w={spec.w}, h={spec.h} — both must be >= 1"
            )
        if spec.x < 0 or spec.y < 0 or spec.x + spec.w > canvas_size or spec.y + spec.h > canvas_size:
            overflows: list[str] = []
            if spec.x < 0:
                overflows.append(f"west by {-spec.x}")
            if spec.y < 0:
                overflows.append(f"north by {-spec.y}")
            if spec.x + spec.w > canvas_size:
                overflows.append(f"east by {spec.x + spec.w - canvas_size}")
            if spec.y + spec.h > canvas_size:
                overflows.append(f"south by {spec.y + spec.h - canvas_size}")
            raise OutOfBoundsError(
                f"Room '{cell_id}': layout-resolved position ({spec.x},{spec.y}) w={spec.w},h={spec.h} "
                f"out of bounds (canvas {canvas_size}x{canvas_size}) — overflows: {', '.join(overflows)}"
            )
