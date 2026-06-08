from typing import Any

from mapgen import EntryContext


def emit_entry(entry: EntryContext) -> dict[str, Any]:
    obj: dict[str, Any] = {
        "fill_ter": entry.fill_ter,
        "rows": entry.grid.to_rows(),
        "palettes": entry.palette,
    }
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
