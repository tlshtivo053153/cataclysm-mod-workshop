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

KNOWN_KEYS = {"om_terrain", "fill_ter", "palette", "rooms", "doors", "features", "global"}


@dataclass
class PlaceSpec:
    relative_to: str | None = None
    inside: str | None = None
    side: str = "south"
    anchor: str = "south"
    margin: int = 0
    x: int | None = None
    y: int | None = None


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


def _validate_entry(entry_data: dict, canvas_size: int = MAPGEN_SIZE) -> EntrySpec:
    om_terrain = entry_data.get("om_terrain")
    if not om_terrain:
        raise CompileError("Entry missing required field: om_terrain")

    fill_ter = entry_data.get("fill_ter", "t_floor")
    palette = entry_data.get("palette", [])

    room_specs: list[RoomSpec] = []
    resolved: dict[str, RoomSpec] = {}
    for room_data in entry_data.get("rooms", []):
        room_id = room_data.get("id")
        if not room_id:
            raise CompileError("Room missing required field: id")
        w = room_data.get("w")
        h = room_data.get("h")
        if w is None or h is None:
            raise CompileError(f"Room '{room_id}' missing required field: w or h")

        wall = room_data.get("wall")
        floor = room_data.get("floor")
        if wall is None or floor is None:
            raise CompileError(f"Room '{room_id}' missing required field: wall or floor")

        place_data = room_data.get("place")
        has_x = "x" in room_data
        has_y = "y" in room_data

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
        elif has_x and has_y:
            x = room_data["x"]
            y = room_data["y"]
            place = None
        else:
            raise CompileError(
                f"Room '{room_id}': must specify either 'place' or both 'x' and 'y' coordinates"
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
            raise OutOfBoundsError(
                f"Room '{spec.id}': out of bounds at ({spec.x},{spec.y}) w={spec.w},h={spec.h} "
                f"(canvas {canvas_size}x{canvas_size}) — overflows: {', '.join(overflows)}"
            )
        room_specs.append(spec)
        resolved[room_id] = spec

    room_ids = [r.id for r in room_specs]
    seen: set[str] = set()
    for rid in room_ids:
        if rid in seen:
            raise DuplicateRoomIdError(
                f"Duplicate room id: '{rid}' — each room must have a unique id"
            )
        seen.add(rid)

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
        if spec.from_room not in seen:
            raise RoomNotAdjacentError(
                f"Door references unknown room: '{spec.from_room}'"
            )
        if spec.to_room not in seen:
            raise RoomNotAdjacentError(
                f"Door references unknown room: '{spec.to_room}'"
            )
        if spec.side is not None:
            room_a = make_room_from_spec(room_specs, spec.from_room)
            room_b = make_room_from_spec(room_specs, spec.to_room)
            if room_a.is_adjacent_to(room_b):
                raise CompileError(
                    f"Door between '{spec.from_room}' and '{spec.to_room}': "
                    f"'side' is only valid for contained rooms, but rooms are adjacent"
                )
        door_specs.append(spec)

    feature_specs: list[FeatureSpec] = []
    for feat_data in entry_data.get("features", []):
        try:
            room_name = feat_data["room"]
        except KeyError as e:
            raise CompileError(f"Feature missing required field: {e}") from e
        if room_name not in seen:
            raise FeatureOutOfRoomError(
                f"Feature references unknown room: '{room_name}'"
            )
        room_spec = _find_room_spec(room_specs, room_name)
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

    pass_through: dict = {}
    for key, value in entry_data.items():
        if key not in KNOWN_KEYS:
            pass_through[key] = value

    return EntrySpec(
        om_terrain=om_terrain,
        fill_ter=fill_ter,
        palette=palette,
        rooms=room_specs,
        doors=door_specs,
        features=feature_specs,
        global_tiles=global_tiles,
        pass_through=pass_through,
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
            y = place.y if place.y is not None else ref.y
        elif side == "west":
            x = ref.x - w - place.margin
            y = place.y if place.y is not None else ref.y
        elif side == "south":
            y = ref.y + ref.h + place.margin
            x = place.x if place.x is not None else ref.x
        elif side == "north":
            y = ref.y - h - place.margin
            x = place.x if place.x is not None else ref.x
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
                f"adjust one room's position or size to eliminate overlap"
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
