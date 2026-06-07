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

KNOWN_KEYS = {"om_terrain", "fill_ter", "palette", "rooms", "doors", "features", "global"}


@dataclass
class RoomSpec:
    id: str
    x: int
    y: int
    w: int
    h: int
    wall: str
    floor: str


@dataclass
class DoorSpec:
    from_room: str
    to_room: str
    char: str
    offset: int | None = None
    side: str | None = None


@dataclass
class FeatureTile:
    char: str
    x: int
    y: int


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


def _validate_entry(entry_data: dict) -> EntrySpec:
    om_terrain = entry_data.get("om_terrain")
    if not om_terrain:
        raise CompileError("Entry missing required field: om_terrain")

    fill_ter = entry_data.get("fill_ter", "t_floor")
    palette = entry_data.get("palette", [])

    room_specs: list[RoomSpec] = []
    for room_data in entry_data.get("rooms", []):
        try:
            spec = RoomSpec(
                id=room_data["id"],
                x=room_data["x"],
                y=room_data["y"],
                w=room_data["w"],
                h=room_data["h"],
                wall=room_data["wall"],
                floor=room_data["floor"],
            )
        except KeyError as e:
            raise CompileError(f"Room missing required field: {e}") from e
        if spec.w < 1 or spec.h < 1:
            raise InvalidRoomSizeError(
                f"Room '{spec.id}': w={spec.w}, h={spec.h} — both must be >= 1"
            )
        if spec.x < 0 or spec.y < 0 or spec.x + spec.w > 24 or spec.y + spec.h > 24:
            raise OutOfBoundsError(
                f"Room '{spec.id}': coordinates out of bounds ({spec.x},{spec.y}) w={spec.w},h={spec.h}"
            )
        room_specs.append(spec)

    room_ids = [r.id for r in room_specs]
    seen: set[str] = set()
    for rid in room_ids:
        if rid in seen:
            raise DuplicateRoomIdError(f"Duplicate room id: '{rid}'")
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
            )
        except KeyError as e:
            raise CompileError(f"Door missing required field: {e}") from e
        if spec.from_room not in seen:
            raise RoomNotAdjacentError(
                f"Door references unknown room: '{spec.from_room}'"
            )
        if spec.to_room not in seen:
            raise RoomNotAdjacentError(
                f"Door references unknown room: '{spec.to_room}'"
            )
        if spec.side is not None:
            room_a = _make_room_from_spec(room_specs, spec.from_room)
            room_b = _make_room_from_spec(room_specs, spec.to_room)
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
                )
            except KeyError as e:
                raise CompileError(f"Feature tile in room '{room_name}' missing required field: {e}") from e
            if tile.x < 0 or tile.x >= room_spec.w or tile.y < 0 or tile.y >= room_spec.h:
                raise FeatureOutOfRoomError(
                    f"Feature tile at ({tile.x},{tile.y}) is outside room '{room_name}' "
                    f"(size={room_spec.w}x{room_spec.h})"
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
            if x_val < 0 or x_val > 23:
                raise FeatureOutOfGridError(
                    f"Global tile x={x_val} out of bounds (0-23)"
                )
        for y_val in _resolve_global_coords(gt.y):
            if y_val < 0 or y_val > 23:
                raise FeatureOutOfGridError(
                    f"Global tile y={y_val} out of bounds (0-23)"
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


def _make_room_from_spec(specs: list[RoomSpec], room_id: str) -> Room:
    s = _find_room_spec(specs, room_id)
    return Room(room_id=s.id, x=s.x, y=s.y, w=s.w, h=s.h, wall_char=s.wall, floor_char=s.floor)


def _find_room_spec(specs: list[RoomSpec], room_id: str) -> RoomSpec:
    for s in specs:
        if s.id == room_id:
            return s
    raise KeyError(f"Room '{room_id}' not found")


def _validate_room_overlaps(entry: EntrySpec) -> None:
    rooms = [_make_room_from_spec(entry.rooms, s.id) for s in entry.rooms]
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
                f"Rooms '{a.room_id}' and '{b.room_id}' partially overlap"
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

    entries: list[EntrySpec] = []
    for entry_data in entries_data:
        entry = _validate_entry(entry_data)
        _validate_room_overlaps(entry)
        entries.append(entry)

    return DSLDocument(entries=entries)
