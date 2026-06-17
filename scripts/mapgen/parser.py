from __future__ import annotations

from pathlib import Path

import yaml

from mapgen import (
    CompileError,
    DuplicateRoomIdError,
    FeatureOutOfGridError,
    FeatureOutOfRoomError,
    InvalidRoomSizeError,
    OutOfBoundsError,
    RoomNotAdjacentError,
)
from mapgen.grid import MAPGEN_SIZE
from mapgen.placement import _resolve_entry_layout, resolve_room_placement
from mapgen.schema import (
    _RELATIVE_KEYS,
    KNOWN_KEYS,
    DoorSpec,
    DSLDocument,
    EntrySpec,
    FeatureSpec,
    FeatureTile,
    GlobalTile,
    PlaceSpec,
    RoomSpec,
    make_room,
)
from mapgen.validation import _validate_room_overlaps


def _detect_new_placement_keys(
    room_data: dict, room_id: str, has_x: bool, has_y: bool, has_place: bool,
) -> PlaceSpec | None:
    new_keys = _RELATIVE_KEYS & set(room_data.keys())
    if not new_keys:
        return None

    if has_place:
        raise CompileError(
            f"Room '{room_id}': cannot mix new placement keys ({', '.join(sorted(new_keys))}) "
            f"with 'place' — use one or the other"
        )
    if has_x or has_y:
        raise CompileError(
            f"Room '{room_id}': cannot mix new placement keys ({', '.join(sorted(new_keys))}) "
            f"with 'x'/'y' absolute coordinates — use one or the other"
        )

    right_of = room_data.get("right_of")
    left_of = room_data.get("left_of")
    above = room_data.get("above")
    below = room_data.get("below")
    inside = room_data.get("inside")
    align = room_data.get("align")
    gap = room_data.get("gap", 0)

    place_count = sum(1 for v in [right_of, left_of, above, below, inside] if v is not None)
    if place_count == 0:
        raise CompileError(
            f"Room '{room_id}': must specify one of 'right_of', 'left_of', "
            f"'above', 'below', or 'inside' for relative placement"
        )
    if place_count > 1:
        raise CompileError(
            f"Room '{room_id}': cannot specify multiple placement targets "
            f"(right_of/left_of/above/below/inside) — use exactly one"
        )

    if gap < 0:
        raise CompileError(
            f"Room '{room_id}': 'gap' must be >= 0, got {gap}"
        )

    if inside is not None:
        if align is None:
            align = "north"
        return _build_inside_placement(inside, align, gap, room_id)
    else:
        ref = right_of or left_of or above or below
        if right_of is not None or left_of is not None:
            if align is None:
                align = "top"
            return _build_adjacent_placement(ref, "east" if right_of is not None else "west", align, gap, room_id)
        elif above is not None or below is not None:
            if align is None:
                align = "left"
            return _build_adjacent_placement(ref, "north" if above is not None else "south", align, gap, room_id)


def _build_adjacent_placement(
    ref: str, side: str, align: str, gap: int, room_id: str,
) -> PlaceSpec:
    if side in ("east", "west"):
        if align not in ("top", "bottom", "center", "middle"):
            raise CompileError(
                f"Room '{room_id}': 'align' for right_of/left_of must be "
                f"top, bottom, center, or middle, got '{align}'"
            )
    else:
        if align not in ("left", "right", "center", "middle"):
            raise CompileError(
                f"Room '{room_id}': 'align' for above/below must be "
                f"left, right, center, or middle, got '{align}'"
            )

    return PlaceSpec(
        relative_to=ref,
        side=side,
        anchor="south",
        margin=gap,
        _align_style=align,
    )


def _build_inside_placement(
    inside: str, align: str, gap: int, room_id: str,
) -> PlaceSpec:
    valid_aligns = {
        "top", "north", "bottom", "south", "left", "west", "right", "east",
        "center", "middle",
        "top-left", "north-west", "top-right", "north-east",
        "bottom-left", "south-west", "bottom-right", "south-east",
    }
    if align not in valid_aligns:
        raise CompileError(
            f"Room '{room_id}': invalid 'align' for inside placement: '{align}' — "
            f"must be one of: top, bottom, left, right, center, "
            f"or compound like south-east, top-left, etc."
        )

    anchor_map = {
        "top": "north", "north": "north",
        "bottom": "south", "south": "south",
        "left": "west", "west": "west",
        "right": "east", "east": "east",
        "center": "north", "middle": "north",
        "top-left": "north", "north-west": "north",
        "top-right": "north", "north-east": "north",
        "bottom-left": "south", "south-west": "south",
        "bottom-right": "south", "south-east": "south",
    }
    anchor = anchor_map.get(align, "south")

    return PlaceSpec(
        inside=inside,
        side="south",
        anchor=anchor,
        margin=gap,
        _align_style=align,
    )


def _resolve_global_coords(value: int | list[int]) -> list[int]:
    if isinstance(value, int):
        return [value]
    if isinstance(value, list) and len(value) == 2:
        if value[0] > value[1]:
            raise CompileError(
                f"Invalid global coordinate range: [{value[0]}, {value[1]}] "
                f"(start must be <= end)"
            )
        return list(range(value[0], value[1] + 1))
    raise CompileError(f"Invalid global coordinate: {value}")


def _check_deps_cycle(
    room_id: str, start: str, deps: dict[str, set[str]], visited: set[str],
) -> None:
    if room_id in visited:
        if room_id == start:
            cycle_path = " → ".join(list(visited) + [room_id])
            raise CompileError(
                f"Circular room placement dependency detected: {cycle_path} — "
                f"relative placement must form a directed acyclic graph"
            )
        return
    visited.add(room_id)
    for dep in deps.get(room_id, set()):
        _check_deps_cycle(dep, start, deps, visited)
    visited.discard(room_id)


def _parse_rooms(entry_data: dict, canvas_size: int, has_layout: bool = False) -> dict[str, RoomSpec]:
    rooms_data = entry_data.get("rooms", [])

    room_items: list[tuple[str, dict]] = []
    if isinstance(rooms_data, dict):
        for room_id, room_data in rooms_data.items():
            if not isinstance(room_data, dict):
                raise CompileError(f"Room '{room_id}': value must be a mapping")
            room_items.append((room_id, room_data))
    elif isinstance(rooms_data, list):
        for room_data in rooms_data:
            room_id = room_data.get("id")
            if not room_id:
                raise CompileError("Room missing required field: id")
            room_items.append((room_id, room_data))
    else:
        raise CompileError("'rooms' must be a list or mapping")

    specs: dict[str, RoomSpec] = {}
    deps: dict[str, set[str]] = {}
    is_first = True

    for room_id, room_data in room_items:
        if room_id in specs:
            raise DuplicateRoomIdError(
                f"Duplicate room id: '{room_id}' — each room must have a unique id"
            )

        inner_w = room_data.get("inner_w")
        inner_h = room_data.get("inner_h")
        w = room_data.get("w")
        h = room_data.get("h")

        if inner_w is not None and w is not None:
            raise CompileError(
                f"Room '{room_id}': cannot specify both 'w' and 'inner_w' — "
                f"use 'inner_w' for interior width (walls added automatically: w = inner_w + 2) "
                f"or 'w' for total width including walls"
            )
        if inner_h is not None and h is not None:
            raise CompileError(
                f"Room '{room_id}': cannot specify both 'h' and 'inner_h' — "
                f"use 'inner_h' for interior height (walls added automatically: h = inner_h + 2) "
                f"or 'h' for total height including walls"
            )
        if inner_w is not None:
            if inner_w < 0:
                raise CompileError(
                    f"Room '{room_id}': inner_w must be >= 0, got {inner_w}"
                )
            w = inner_w + 2
        if inner_h is not None:
            if inner_h < 0:
                raise CompileError(
                    f"Room '{room_id}': inner_h must be >= 0, got {inner_h}"
                )
            h = inner_h + 2

        wall = room_data.get("wall")
        floor = room_data.get("floor")
        if wall is None or floor is None:
            raise CompileError(f"Room '{room_id}' missing required field: wall or floor")

        has_x = "x" in room_data
        has_y = "y" in room_data
        has_place = "place" in room_data
        has_new_placement = bool(_RELATIVE_KEYS & set(room_data.keys()))

        if has_x or has_y:
            raise CompileError(
                f"Room '{room_id}': x/y absolute coordinates are no longer supported. "
                f"Use right_of/left_of/above/below/inside for relative placement, "
                f"or 'layout' with 'canvas.cols'/'canvas.rows' for grid-based placement."
            )

        if has_place:
            raise CompileError(
                f"Room '{room_id}': 'place' dict is no longer supported. "
                f"Use right_of/left_of/above/below/inside for relative placement instead."
            )

        if w is None and h is None:
            if has_layout:
                w = 0
                h = 0
            elif has_new_placement:
                missing = []
                if w is None:
                    missing.append("w")
                if h is None:
                    missing.append("h")
                raise CompileError(f"Room '{room_id}' missing required field: {', '.join(missing)}")
            else:
                missing = []
                if w is None:
                    missing.append("w")
                if h is None:
                    missing.append("h")
                raise CompileError(f"Room '{room_id}' missing required field: {', '.join(missing)}")
        else:
            w = w or 0
            h = h or 0

        place = None
        dep_rooms: set[str] = set()

        if has_new_placement:
            place = _detect_new_placement_keys(room_data, room_id, has_x, has_y, has_place)
            if place:
                if place.relative_to:
                    dep_rooms.add(place.relative_to)
                if place.inside:
                    dep_rooms.add(place.inside)
        elif not has_layout and not is_first:
            raise CompileError(
                f"Room '{room_id}': must specify a relative placement key "
                f"(right_of/left_of/above/below/inside) or use 'layout' for grid placement. "
                f"The first room in the list can be the anchor (placed at 0,0)."
            )

        specs[room_id] = RoomSpec(
            id=room_id,
            x=0,
            y=0,
            w=w,
            h=h,
            wall=wall,
            floor=floor,
            place=place,
        )
        deps[room_id] = dep_rooms
        is_first = False

    for room_id, dep_set in deps.items():
        for dep in dep_set:
            if dep not in specs:
                raise CompileError(
                    f"Room '{room_id}': references unknown room '{dep}'. "
                    f"Known rooms: {', '.join(sorted(specs.keys()))}"
                )

    for room_id in deps:
        if deps[room_id]:
            _check_deps_cycle(room_id, room_id, deps, set())

    unresolved = set(specs.keys())
    resolved: dict[str, RoomSpec] = {}

    while unresolved:
        progress = False
        for room_id in specs:
            if room_id not in unresolved:
                continue
            spec = specs[room_id]
            if has_layout:
                resolved[room_id] = spec
                unresolved.discard(room_id)
                progress = True
            elif spec.place is not None:
                req_rooms = deps[room_id]
                if all(r in resolved for r in req_rooms):
                    x, y = resolve_room_placement(spec.place, spec.w, spec.h, resolved)
                    spec.x = x
                    spec.y = y
                    resolved[room_id] = spec
                    unresolved.discard(room_id)
                    progress = True
            else:
                spec.x = 0
                spec.y = 0
                resolved[room_id] = spec
                unresolved.discard(room_id)
                progress = True

        if not progress and unresolved:
            unresolved_ids = ", ".join(sorted(unresolved))
            raise CompileError(
                f"Circular room placement dependency detected involving: {unresolved_ids}. "
                f"Check that all right_of/left_of/above/below/inside references form a directed acyclic graph."
            )

    if not has_layout:
        for spec in resolved.values():
            if spec.w < 1 or spec.h < 1:
                raise InvalidRoomSizeError(
                    f"Room '{spec.id}': invalid size w={spec.w}, h={spec.h} — both must be >= 1"
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
                detail = ""
                if overflows:
                    if "east" in " ".join(overflows):
                        detail = " — try reducing w, inner_w, or x"
                    if "south" in " ".join(overflows):
                        detail = " — try reducing h, inner_h, or y"
                    if "west" in " ".join(overflows):
                        detail = " — increase x to 0 or higher"
                    if "north" in " ".join(overflows):
                        detail = " — increase y to 0 or higher"
                raise OutOfBoundsError(
                    f"Room '{spec.id}': out of bounds at ({spec.x},{spec.y}) w={spec.w},h={spec.h} "
                    f"(canvas {canvas_size}x{canvas_size}) — overflows: {', '.join(overflows)}{detail}"
                )

    return resolved


def _parse_doors(entry_data: dict, resolved: dict[str, RoomSpec]) -> list[DoorSpec]:
    door_specs: list[DoorSpec] = []
    for door_data in entry_data.get("doors", []):
        try:
            spec = DoorSpec(
                from_room=door_data["from"],
                to_room=door_data["to"],
                char=door_data["char"],
                offset=door_data.get("offset"),
                side=door_data.get("side"),
                position=door_data.get("position"),
            )
        except KeyError as e:
            raise CompileError(f"Door missing required field: {e}") from e
        if spec.position is not None and spec.offset is not None:
            raise CompileError(
                f"Door between '{spec.from_room}' and '{spec.to_room}': "
                f"cannot specify both 'position' and 'offset' — use one or the other"
            )
        if spec.position is not None and spec.position not in ("left", "center", "right"):
            raise CompileError(
                f"Door between '{spec.from_room}' and '{spec.to_room}': "
                f"invalid position '{spec.position}' — must be left, center, or right"
            )
        if spec.from_room not in resolved:
            known = list(resolved.keys())
            raise RoomNotAdjacentError(
                f"Door references unknown room: '{spec.from_room}'. "
                f"Known rooms: {', '.join(known)}"
            )
        if spec.to_room not in resolved:
            known = list(resolved.keys())
            raise RoomNotAdjacentError(
                f"Door references unknown room: '{spec.to_room}'. "
                f"Known rooms: {', '.join(known)}"
            )
        if spec.side is not None:
            room_a = make_room(resolved[spec.from_room])
            room_b = make_room(resolved[spec.to_room])
            if room_a.is_adjacent_to(room_b):
                raise CompileError(
                    f"Door between '{spec.from_room}' and '{spec.to_room}': "
                    f"'side' is only valid for contained rooms, but rooms are adjacent"
                )
        door_specs.append(spec)
    return door_specs


def _parse_features(entry_data: dict, resolved: dict[str, RoomSpec], canvas_size: int) -> list[FeatureSpec]:
    feature_specs: list[FeatureSpec] = []
    for feat_data in entry_data.get("features", []):
        room_name = feat_data.get("room")
        if room_name is not None and room_name not in resolved:
            raise FeatureOutOfRoomError(
                f"Feature references unknown room: '{room_name}'"
            )
        room_spec = resolved.get(room_name) if room_name is not None else None
        tiles: list[FeatureTile] = []
        for tile_data in feat_data.get("tiles", []):
            try:
                tile = FeatureTile(
                    char=tile_data["char"],
                    x=tile_data["x"],
                    y=tile_data["y"],
                    meaning=tile_data.get("meaning"),
                )
            except KeyError as e:
                room_label = f"room '{room_name}'" if room_name else "global space"
                raise CompileError(f"Feature tile in {room_label} missing required field: {e}") from e

            if room_spec is not None:
                if tile.x < 0 or tile.x >= room_spec.w or tile.y < 0 or tile.y >= room_spec.h:
                    raise FeatureOutOfRoomError(
                        f"Feature tile at ({tile.x},{tile.y}) is outside room '{room_name}' "
                        f"(valid range: x=0-{room_spec.w - 1}, y=0-{room_spec.h - 1})"
                    )
            else:
                if tile.x < 0 or tile.x >= canvas_size or tile.y < 0 or tile.y >= canvas_size:
                    raise FeatureOutOfGridError(
                        f"Feature tile at ({tile.x},{tile.y}) is outside canvas "
                        f"(valid range: x=0-{canvas_size - 1}, y=0-{canvas_size - 1})"
                    )
            tiles.append(tile)
        feature_specs.append(FeatureSpec(room=room_name, tiles=tiles))
    return feature_specs


def _parse_global_tiles(entry_data: dict, canvas_size: int) -> list[GlobalTile]:
    global_tiles: list[GlobalTile] = []
    for gt_data in entry_data.get("global", []):
        try:
            gt = GlobalTile(
                char=gt_data["char"],
                x=gt_data["x"],
                y=gt_data["y"],
            )
        except KeyError as e:
            raise CompileError(f"Global tile missing required field: {e}") from e
        for x_val in _resolve_global_coords(gt.x):
            if x_val < 0 or x_val > canvas_size - 1:
                raise FeatureOutOfGridError(
                    f"Global tile x={x_val} out of bounds (0-{canvas_size - 1})"
                )
        for y_val in _resolve_global_coords(gt.y):
            if y_val < 0 or y_val > canvas_size - 1:
                raise FeatureOutOfGridError(
                    f"Global tile y={y_val} out of bounds (0-{canvas_size - 1})"
                )
        global_tiles.append(gt)
    return global_tiles


def _extract_pass_through(entry_data: dict) -> dict:
    pass_through: dict = {}
    for key, value in entry_data.items():
        if key not in KNOWN_KEYS:
            pass_through[key] = value
    return pass_through


def _parse_no_door(entry_data: dict, resolved: dict[str, RoomSpec]) -> list[tuple[str, str]]:
    no_door_pairs: list[tuple[str, str]] = []
    for pair_data in entry_data.get("no_door", []):
        if not isinstance(pair_data, list) or len(pair_data) != 2:
            raise CompileError(
                f"'no_door' entries must be lists of 2 room IDs, got: {pair_data}"
            )
        room_a, room_b = pair_data[0], pair_data[1]
        if room_a not in resolved:
            raise CompileError(
                f"'no_door' references unknown room: '{room_a}'"
            )
        if room_b not in resolved:
            raise CompileError(
                f"'no_door' references unknown room: '{room_b}'"
            )
        no_door_pairs.append((room_a, room_b))
    return no_door_pairs


def _validate_entry(entry_data: dict, canvas_size: int = MAPGEN_SIZE) -> EntrySpec:
    om_terrain = entry_data.get("om_terrain")
    if not om_terrain:
        raise CompileError("Entry missing required field: om_terrain")

    fill_ter = entry_data.get("fill_ter", "t_floor")
    palette = entry_data.get("palette", [])
    auto_doors = entry_data.get("auto_doors", True)
    default_door_char = entry_data.get("default_door_char", "+")

    layout_matrix = entry_data.get("layout")
    has_layout = layout_matrix is not None
    rooms = _parse_rooms(entry_data, canvas_size, has_layout=has_layout)

    layout_canvas = entry_data.get("canvas")
    if layout_canvas is not None and layout_matrix is not None:
        _resolve_entry_layout(layout_canvas, layout_matrix, rooms, canvas_size)
    elif layout_matrix is not None:
        raise CompileError(
            "'layout' requires 'canvas' with 'cols' and 'rows' to define cell sizes"
        )
    elif layout_canvas is not None and "cols" in layout_canvas:
        raise CompileError(
            "'canvas' with 'cols'/'rows' requires 'layout' matrix to define room placement"
        )

    door_specs = _parse_doors(entry_data, rooms)
    feature_specs = _parse_features(entry_data, rooms, canvas_size)
    global_tiles = _parse_global_tiles(entry_data, canvas_size)
    pass_through = _extract_pass_through(entry_data)
    no_door_pairs = _parse_no_door(entry_data, rooms)

    return EntrySpec(
        om_terrain=om_terrain,
        fill_ter=fill_ter,
        palette=palette,
        rooms=rooms,
        doors=door_specs,
        features=feature_specs,
        global_tiles=global_tiles,
        pass_through=pass_through,
        auto_doors=auto_doors,
        default_door_char=default_door_char,
        no_door=no_door_pairs,
    )


def parse_dsl(yaml_path: Path) -> DSLDocument:
    with open(yaml_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise CompileError("DSL YAML must be a mapping at top level")

    entries_data = raw.get("entries")
    if entries_data is None:
        raise CompileError("DSL YAML must contain 'entries' key")
    if not isinstance(entries_data, list):
        raise CompileError("'entries' must be a list")

    canvas_data = raw.get("canvas")
    canvas_size: int = MAPGEN_SIZE
    if canvas_data is not None:
        if not isinstance(canvas_data, dict):
            raise CompileError("'canvas' must be a mapping with 'w' and 'h' keys")
        cw = canvas_data.get("w")
        ch = canvas_data.get("h")
        if cw is None or ch is None:
            raise CompileError("'canvas' must contain both 'w' and 'h' keys")
        if not isinstance(cw, int) or not isinstance(ch, int):
            raise CompileError("'canvas.w' and 'canvas.h' must be integers")
        if cw < 2 or ch < 2:
            raise CompileError(
                f"'canvas' dimensions must be >= 2, got w={cw} h={ch}"
            )
        if cw != ch:
            raise CompileError(
                f"'canvas' must be square (w={cw}, h={ch})"
            )
        canvas_size = cw

    center = raw.get("center", False)
    if not isinstance(center, bool):
        raise CompileError("'center' must be a boolean")

    entries: list[EntrySpec] = []
    for entry_data in entries_data:
        entry = _validate_entry(entry_data, canvas_size=canvas_size)
        _validate_room_overlaps(entry)
        entries.append(entry)

    return DSLDocument(entries=entries, canvas=canvas_data, canvas_size=canvas_size, center=center)
