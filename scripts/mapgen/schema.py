from dataclasses import dataclass, field
from typing import Any

from mapgen import OutOfBoundsError
from mapgen.grid import MAPGEN_SIZE
from mapgen.room import Room


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
    """Intermediate representation of a room during DSL parsing."""

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

    def validate_bounds(self, canvas_size: int, room_id: str, context: str = "") -> None:
        if (
            self.x < 0
            or self.y < 0
            or self.x + self.w > canvas_size
            or self.y + self.h > canvas_size
        ):
            overflows: list[str] = []
            if self.x < 0:
                overflows.append(f"west by {-self.x}")
            if self.y < 0:
                overflows.append(f"north by {-self.y}")
            if self.x + self.w > canvas_size:
                overflows.append(f"east by {self.x + self.w - canvas_size}")
            if self.y + self.h > canvas_size:
                overflows.append(f"south by {self.y + self.h - canvas_size}")
            hints: list[str] = []
            overflows_text = ", ".join(overflows)
            if "east" in overflows_text:
                hints.append("try reducing w, inner_w, or x")
            if "south" in overflows_text:
                hints.append("try reducing h, inner_h, or y")
            if "west" in overflows_text:
                hints.append("increase x to 0 or higher")
            if "north" in overflows_text:
                hints.append("increase y to 0 or higher")
            detail = " — " + "; ".join(hints) if hints else ""
            prefix = f"{context} " if context else ""
            raise OutOfBoundsError(
                f"Room '{room_id}': {prefix}out of bounds at ({self.x},{self.y}) w={self.w},h={self.h} "
                f"(canvas {canvas_size}x{canvas_size}) — overflows: {', '.join(overflows)}{detail}"
            )


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
    """Parsed representation of a single mapgen entry (one z-level)."""

    om_terrain: str
    fill_ter: str
    palette: list[str] = field(default_factory=list)
    rooms: dict[str, RoomSpec] = field(default_factory=dict)
    doors: list[DoorSpec] = field(default_factory=list)
    features: list[FeatureSpec] = field(default_factory=list)
    global_tiles: list[GlobalTile] = field(default_factory=list)
    pass_through: dict[str, Any] = field(default_factory=dict)
    auto_doors: bool = True
    default_door_char: str = "+"
    no_door: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class DSLDocument:
    """Top-level container for a parsed DSL YAML document."""

    entries: list[EntrySpec] = field(default_factory=list)
    canvas: dict[str, Any] | None = None
    canvas_size: int = MAPGEN_SIZE
    center: bool = False


def make_room(spec: RoomSpec) -> Room:
    return Room(
        room_id=spec.id,
        x=spec.x,
        y=spec.y,
        w=spec.w,
        h=spec.h,
        wall_char=spec.wall,
        floor_char=spec.floor,
    )
