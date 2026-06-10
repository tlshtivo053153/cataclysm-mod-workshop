from dataclasses import dataclass, field
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
    RoomOverlapError,
)
from mapgen.room import Room
from mapgen.grid import MAPGEN_SIZE

KNOWN_KEYS = {"om_terrain", "fill_ter", "palette", "rooms", "doors", "features", "global",
               "canvas", "layout", "auto_doors", "default_door_char"}


@dataclass
class PlaceSpec:
    relative_to: str | None = None
    inside: str | None = None
    side: str = "south"
    anchor: str = "south"
    margin: int = 0
    x: int | None = None
    y: int | None = None
    _align_style: str | None = None


@dataclass
class RoomSpec:
    id: str
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    wall: str = ""
    floor: str = ""
    place: PlaceSpec | None = None
    layout_resolved: bool = False


@dataclass
class DoorSpec:
    from_room: str
    to_room: str
    char: str
    offset: int | None = None
    side: str | None = None
    position: str | None = None


@dataclass
class FeatureTile:
    char: str
    x: int
    y: int
    meaning: str | None = None


@dataclass
class FeatureSpec:
    room: str
    tiles: list[FeatureTile] = field(default_factory=list)


@dataclass
class GlobalTile:
    char: str
    x: int | list[int]
    y: int | list[int]


@dataclass
class EntrySpec:
    om_terrain: str
    fill_ter: str
    palette: list[str] = field(default_factory=list)
    rooms: list[RoomSpec] = field(default_factory=list)
    doors: list[DoorSpec] = field(default_factory=list)
    features: list[FeatureSpec] = field(default_factory=list)
    global_tiles: list[GlobalTile] = field(default_factory=list)
    pass_through: dict = field(default_factory=dict)
    auto_doors: bool = False
    default_door_char: str = "+"


@dataclass
class DSLDocument:
    entries: list[EntrySpec] = field(default_factory=list)
    canvas: dict | None = None
    canvas_size: int = MAPGEN_SIZE


def make_room(spec: RoomSpec) -> Room:
    return Room(
        room_id=spec.id, x=spec.x, y=spec.y, w=spec.w, h=spec.h,
        wall_char=spec.wall, floor_char=spec.floor,
    )


_RELATIVE_KEYS = {"right_of", "left_of", "above", "below", "inside", "align", "gap"}


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
        x=None,
        y=None,
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
        x=None,
        y=None,
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


def _parse_rooms(entry_data: dict, canvas_size: int, has_layout: bool = False) -> tuple[list[RoomSpec], dict[str, RoomSpec]]:
    room_specs: list[RoomSpec] = []
    resolved: dict[str, RoomSpec] = {}
    for room_data in entry_data.get("rooms", []):
        room_id = room_data.get("id")
        if not room_id:
            raise CompileError("Room missing required field: id")

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

        if w is None or h is None:
            has_any_coords = has_x or has_y or "place" in room_data or _RELATIVE_KEYS & set(room_data.keys())
            if has_any_coords:
                missing = []
                if w is None:
                    missing.append("w")
                if h is None:
                    missing.append("h")
                raise CompileError(f"Room '{room_id}' missing required field: {', '.join(missing)}")
            w = w or 0
            h = h or 0

        place_data = room_data.get("place")

        new_placement = _detect_new_placement_keys(room_data, room_id, has_x, has_y, place_data is not None)

        if place_data is not None:
            if has_x or has_y:
                raise CompileError(
                    f"Room '{room_id}': cannot specify both 'place' and 'x'/'y' — "
                    f"use 'place' for automatic placement, or 'x'/'y' for absolute coordinates"
                )
            place = PlaceSpec(
                relative_to=place_data.get("relative_to"),
                inside=place_data.get("inside"),
                side=place_data.get("side", "south"),
                anchor=place_data.get("anchor", "south"),
                margin=place_data.get("margin", 0),
                x=place_data.get("x"),
                y=place_data.get("y"),
            )
            x, y = resolve_room_placement(place, w, h, resolved)
        elif new_placement is not None:
            place = new_placement
            x, y = resolve_room_placement(place, w, h, resolved)
        elif has_x and has_y:
            x = room_data["x"]
            y = room_data["y"]
            place = None
        elif has_layout:
            x = 0
            y = 0
            place = None
        else:
            raise CompileError(
                f"Room '{room_id}': must specify either 'place', 'x'/'y' coordinates, "
                f"or a relative placement key (right_of/left_of/above/below/inside)"
            )

        spec = RoomSpec(
            id=room_id,
            x=x,
            y=y,
            w=w,
            h=h,
            wall=wall,
            floor=floor,
            place=place,
        )
        if spec.w < 1 or spec.h < 1:
            if has_layout and spec.w == 0 and spec.h == 0:
                pass
            else:
                raise InvalidRoomSizeError(
                    f"Room '{spec.id}': invalid size w={spec.w}, h={spec.h} — both must be >= 1"
                )
        if has_layout:
            pass
        elif spec.x < 0 or spec.y < 0 or spec.x + spec.w > canvas_size or spec.y + spec.h > canvas_size:
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
        if room_id in resolved:
            raise DuplicateRoomIdError(
                f"Duplicate room id: '{room_id}' — each room must have a unique id"
            )
        room_specs.append(spec)
        resolved[room_id] = spec
    return room_specs, resolved


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


def _parse_features(entry_data: dict, resolved: dict[str, RoomSpec]) -> list[FeatureSpec]:
    feature_specs: list[FeatureSpec] = []
    for feat_data in entry_data.get("features", []):
        try:
            room_name = feat_data["room"]
        except KeyError as e:
            raise CompileError(f"Feature missing required field: {e}") from e
        if room_name not in resolved:
            raise FeatureOutOfRoomError(
                f"Feature references unknown room: '{room_name}'"
            )
        room_spec = resolved[room_name]
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
                raise CompileError(f"Feature tile in room '{room_name}' missing required field: {e}") from e
            if tile.x < 0 or tile.x >= room_spec.w or tile.y < 0 or tile.y >= room_spec.h:
                raise FeatureOutOfRoomError(
                    f"Feature tile at ({tile.x},{tile.y}) is outside room '{room_name}' "
                    f"(valid range: x=0-{room_spec.w - 1}, y=0-{room_spec.h - 1})"
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


def _validate_entry(entry_data: dict, canvas_size: int = MAPGEN_SIZE) -> EntrySpec:
    om_terrain = entry_data.get("om_terrain")
    if not om_terrain:
        raise CompileError("Entry missing required field: om_terrain")

    fill_ter = entry_data.get("fill_ter", "t_floor")
    palette = entry_data.get("palette", [])
    auto_doors = entry_data.get("auto_doors", False)
    default_door_char = entry_data.get("default_door_char", "+")

    layout_matrix = entry_data.get("layout")
    has_layout = layout_matrix is not None
    room_specs, resolved = _parse_rooms(entry_data, canvas_size, has_layout=has_layout)

    layout_canvas = entry_data.get("canvas")
    if layout_canvas is not None and layout_matrix is not None:
        _resolve_entry_layout(layout_canvas, layout_matrix, room_specs, resolved, canvas_size)
    elif layout_matrix is not None:
        raise CompileError(
            "'layout' requires 'canvas' with 'cols' and 'rows' to define cell sizes"
        )
    elif layout_canvas is not None and "cols" in layout_canvas:
        raise CompileError(
            "'canvas' with 'cols'/'rows' requires 'layout' matrix to define room placement"
        )

    door_specs = _parse_doors(entry_data, resolved)
    feature_specs = _parse_features(entry_data, resolved)
    global_tiles = _parse_global_tiles(entry_data, canvas_size)
    pass_through = _extract_pass_through(entry_data)

    return EntrySpec(
        om_terrain=om_terrain,
        fill_ter=fill_ter,
        palette=palette,
        rooms=room_specs,
        doors=door_specs,
        features=feature_specs,
        global_tiles=global_tiles,
        pass_through=pass_through,
        auto_doors=auto_doors,
        default_door_char=default_door_char,
    )


def make_room_from_spec(specs: list[RoomSpec], room_id: str) -> Room:
    s = _find_room_spec(specs, room_id)
    return make_room(s)


def _find_room_spec(specs: list[RoomSpec], room_id: str) -> RoomSpec:
    for s in specs:
        if s.id == room_id:
            return s
    raise KeyError(f"Room '{room_id}' not found")


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
            y = place.y if place.y is not None else _resolve_align_y(place, ref, h)
        elif side == "west":
            x = ref.x - w - place.margin
            y = place.y if place.y is not None else _resolve_align_y(place, ref, h)
        elif side == "south":
            y = ref.y + ref.h + place.margin
            x = place.x if place.x is not None else _resolve_align_x(place, ref, w)
        elif side == "north":
            y = ref.y - h - place.margin
            x = place.x if place.x is not None else _resolve_align_x(place, ref, w)
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
    room_specs: list[RoomSpec],
    resolved: dict[str, RoomSpec],
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

    room_by_id: dict[str, RoomSpec] = {r.id: r for r in room_specs}

    room_cells: dict[str, tuple[int, int, int, int]] = {}
    for ri, row in enumerate(layout_matrix):
        for ci, cell_id in enumerate(row):
            if cell_id not in room_by_id:
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

    all_room_ids = {r.id for r in room_specs}
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

        spec = room_by_id[cell_id]
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



def _validate_room_overlaps(entry: EntrySpec) -> None:
    rooms = [make_room(s) for s in entry.rooms]
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

    entries: list[EntrySpec] = []
    for entry_data in entries_data:
        entry = _validate_entry(entry_data, canvas_size=canvas_size)
        _validate_room_overlaps(entry)
        entries.append(entry)

    return DSLDocument(entries=entries, canvas=canvas_data, canvas_size=canvas_size)
