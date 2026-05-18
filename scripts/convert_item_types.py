#!/usr/bin/env python3
"""
Convert old item types (TOOL, GUN, ARMOR, TOOL_ARMOR, COMESTIBLE, GENERIC, BOOK)
to new unified ITEM type with subtypes for CDDA 0.I.
"""

import json
import sys
from pathlib import Path

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


def convert_object(obj):
    if not isinstance(obj, dict):
        return obj

    if "type" in obj and obj["type"] in TYPE_MAP:
        old_type = obj["type"]
        obj["type"] = "ITEM"
        obj["subtypes"] = TYPE_MAP[old_type]

    # Recurse into known list fields that may contain objects
    for key, value in obj.items():
        if isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    new_list.append(convert_object(item))
                else:
                    new_list.append(item)
            obj[key] = new_list
        elif isinstance(value, dict):
            obj[key] = convert_object(value)

    return obj


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    data = json.loads(content)

    if isinstance(data, list):
        data = [convert_object(item) for item in data]
    elif isinstance(data, dict):
        data = convert_object(data)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def main():
    target_dir = Path(sys.argv[1])
    for filepath in target_dir.rglob("*.json"):
        try:
            process_file(filepath)
            print(f"Processed: {filepath}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
