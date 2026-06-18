from dataclasses import dataclass, field

from mapgen.grid import MAPGEN_SIZE
from mapgen.room import Room

KNOWN_KEYS = {"om_terrain", "fill_ter", "palette", "rooms", "doors", "features", "global",
               "canvas", "layout", "auto_doors", "default_door_char", "no_door"}


@dataclass
class PlaceSpec:
    relative_to: str | None = None
    inside: str | None = None
    side: str = "south"
    anchor: str = "south"
    margin: int = 0
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

    def shift(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy


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

    def shift(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy


@dataclass
class FeatureSpec:
    room: str | None = None
    tiles: list[FeatureTile] = field(default_factory=list)


@dataclass
class GlobalTile:
    char: str
    x: int | list[int]
    y: int | list[int]

    def shift(self, dx: int, dy: int) -> None:
        self.x = self.x + dx if isinstance(self.x, int) else [v + dx for v in self.x]
        self.y = self.y + dy if isinstance(self.y, int) else [v + dy for v in self.y]


@dataclass
class EntrySpec:
    om_terrain: str
    fill_ter: str
    palette: list[str] = field(default_factory=list)
    rooms: dict[str, RoomSpec] = field(default_factory=dict)
    doors: list[DoorSpec] = field(default_factory=list)
    features: list[FeatureSpec] = field(default_factory=list)
    global_tiles: list[GlobalTile] = field(default_factory=list)
    pass_through: dict = field(default_factory=dict)
    auto_doors: bool = True
    default_door_char: str = "+"
    no_door: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class DSLDocument:
    entries: list[EntrySpec] = field(default_factory=list)
    canvas: dict | None = None
    canvas_size: int = MAPGEN_SIZE
    center: bool = False


def make_room(spec: RoomSpec) -> Room:
    return Room(
        room_id=spec.id, x=spec.x, y=spec.y, w=spec.w, h=spec.h,
        wall_char=spec.wall, floor_char=spec.floor,
    )


_RELATIVE_KEYS = {"right_of", "left_of", "above", "below", "inside", "align", "gap"}


def make_room_from_spec(specs: dict[str, RoomSpec], room_id: str) -> Room:
    s = specs[room_id]
    return make_room(s)


