"""Coordinate resolution helpers shared by parser, stairs, and centering."""

from __future__ import annotations

from mapgen import CompileError


def resolve_global_coords(value: int | list[int]) -> list[int]:
    """Expand a coordinate spec into the list of integer coordinates it covers.

    An ``int`` yields a single-element list. A two-element ``[start, end]`` list
    yields the inclusive range ``range(start, end + 1)``.
    """
    if isinstance(value, int):
        return [value]
    if isinstance(value, list) and len(value) == 2:
        if value[0] > value[1]:
            raise CompileError(
                f"Invalid global coordinate range: [{value[0]}, {value[1]}] (start must be <= end)"
            )
        return list(range(value[0], value[1] + 1))
    raise CompileError(f"Invalid global coordinate: {value}")
