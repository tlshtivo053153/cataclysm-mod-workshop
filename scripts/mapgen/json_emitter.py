from typing import Any

from mapgen import EntryContext, Warning
from mapgen.schema import COMPILER_KEYS


def emit_entry(entry: EntryContext) -> dict[str, Any]:
    obj: dict[str, Any] = {
        "fill_ter": entry.fill_ter,
        "rows": entry.grid.to_rows(),
        "palettes": entry.palette,
    }
    collisions = set(entry.pass_through.keys()) & COMPILER_KEYS
    if collisions:
        entry.warnings.append(Warning(
            code="passthrough_collision",
            message=f"Pass-through keys {collisions} will override compiler-generated fields",
        ))
    for key, value in entry.pass_through.items():
        if value is not None:
            obj[key] = value
    return {
        "type": "mapgen",
        "om_terrain": entry.om_terrain,
        "object": obj,
    }


def emit_json_array(entries: list[EntryContext]) -> list[dict[str, Any]]:
    return [emit_entry(e) for e in entries]
