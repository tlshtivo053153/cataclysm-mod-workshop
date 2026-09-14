#!/usr/bin/env python3
"""Convert old item types to new unified ITEM type with subtypes for CDDA 0.I."""

import copy
import sys

from common import MAX_RECURSION_DEPTH, run_standard_pipeline

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


MAX_DEPTH = MAX_RECURSION_DEPTH


def convert_object(obj, _depth=0):
    if _depth > MAX_DEPTH:
        if _depth == MAX_DEPTH + 1:
            print(
                f"Warning: max recursion depth ({MAX_DEPTH}) exceeded in convert_item_types",
                file=sys.stderr,
            )
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


def processor(data, _path):
    if isinstance(data, list):
        original = copy.deepcopy(data)
        result = [convert_object(item) for item in data]
        if result == original:
            return None
        return result
    elif isinstance(data, dict):
        original = copy.deepcopy(data)
        result = convert_object(data)
        if result == original:
            return None
        return result
    return None


def main():
    run_standard_pipeline("Convert old item types to unified ITEM type", processor)


if __name__ == "__main__":
    main()
