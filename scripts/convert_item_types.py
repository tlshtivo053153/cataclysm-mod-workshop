#!/usr/bin/env python3
"""Convert old item types to new unified ITEM type with subtypes for CDDA 0.I."""

import sys
from pathlib import Path
from typing import Any

from common import depth_exceeded, noop_if_unchanged, run_standard_pipeline, snapshot

TYPE_MAP = {
    "TOOL": ["TOOL"],
    "GUN": ["GUN"],
    "ARMOR": ["ARMOR"],
    "TOOL_ARMOR": ["TOOL", "ARMOR"],
    "COMESTIBLE": ["COMESTIBLE"],
    "GENERIC": ["GENERIC"],
    "BOOK": ["BOOK"],
    "AMMO": ["AMMO"],
    "MAGAZINE": ["MAGAZINE"],
    "GUNMOD": ["GUNMOD"],
    "BIONIC_ITEM": ["BIONIC_ITEM"],
    "SEED": ["SEED"],
    "MILLING": ["MILLING"],
    "PET_ARMOR": ["PET_ARMOR"],
    "WHEEL": ["WHEEL"],
    "ENGINE": ["ENGINE"],
    "BREWABLE": ["BREWABLE"],
    "ARTIFACT": ["ARTIFACT"],
    "TOOLMOD": ["TOOLMOD"],
    "COMPOSTABLE": ["COMPOSTABLE"],
}


def convert_object(obj: Any, _depth: int = 0) -> Any:
    if depth_exceeded(_depth, "convert_item_types"):
        return obj
    if not isinstance(obj, dict):
        return obj

    obj_type = obj.get("type")
    if isinstance(obj_type, str) and obj_type in TYPE_MAP:
        old_type = obj_type
        obj["type"] = "ITEM"
        obj["subtypes"] = TYPE_MAP[old_type]

    for key, value in obj.items():
        if isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    new_list.append(convert_object(item, _depth + 1))
                else:
                    new_list.append(item)
            obj[key] = new_list
        elif isinstance(value, dict):
            obj[key] = convert_object(value, _depth + 1)

    return obj


def processor(data: Any, _path: Path) -> Any | None:
    if not isinstance(data, (list, dict)):
        return None
    original: Any = snapshot(data)
    if isinstance(data, list):
        result: Any = [convert_object(item) for item in data]
    else:
        result = convert_object(data)
    return noop_if_unchanged(original, result)


def main() -> int:
    return run_standard_pipeline("Convert old item types to unified ITEM type", processor)


if __name__ == "__main__":
    sys.exit(main())
