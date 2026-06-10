from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mapgen.grid import Grid
    from mapgen.schema import FeatureSpec

__all__ = [
    "CompileError",
    "CompileErrorGroup",
    "RoomOverlapError",
    "RoomNotAdjacentError",
    "DoorOverlapTooSmallError",
    "DoorNotOnWallError",
    "OutOfBoundsError",
    "FeatureOutOfRoomError",
    "FeatureOutOfGridError",
    "DuplicateRoomIdError",
    "InvalidRoomSizeError",
    "StairMismatchError",
    "NoEntryPointError",
    "Warning",
    "EntryContext",
]


class CompileError(Exception):
    def __init__(self, message: str, detail: str = "") -> None:
        self.detail = detail
        super().__init__(message)


class CompileErrorGroup(CompileError):
    def __init__(self, errors: list[CompileError]) -> None:
        self.errors = errors
        summary = f"{len(errors)} compilation error(s): " + "; ".join(str(e) for e in errors)
        super().__init__(summary)


class RoomOverlapError(CompileError):
    pass


class RoomNotAdjacentError(CompileError):
    pass


class DoorOverlapTooSmallError(CompileError):
    pass


class DoorNotOnWallError(CompileError):
    pass


class OutOfBoundsError(CompileError):
    pass


class FeatureOutOfRoomError(CompileError):
    pass


class FeatureOutOfGridError(CompileError):
    pass


class DuplicateRoomIdError(CompileError):
    pass


class InvalidRoomSizeError(CompileError):
    pass


class StairMismatchError(CompileError):
    pass


class NoEntryPointError(CompileError):
    pass


@dataclass
class Warning:
    code: str
    message: str
    detail: str = ""


@dataclass
class EntryContext:
    om_terrain: str
    fill_ter: str
    palette: list[str]
    grid: "Grid"
    pass_through: dict[str, Any]
    warnings: list[Warning]
    features: list[FeatureSpec] = field(default_factory=list)
