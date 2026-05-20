#!/usr/bin/env python3
"""Convert old item types to new unified ITEM type with subtypes for CDDA 0.I."""

import sys
from pathlib import Path

# Add scripts directory to path for common imports
sys.path.insert(0, str(Path(__file__).parent))

from common import create_parser, process_directory, resolve_paths, save_json

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


def processor(data, _path):
    if isinstance(data, list):
        return [convert_object(item) for item in data]
    elif isinstance(data, dict):
        return convert_object(data)
    return data


def main():
    parser = create_parser("Convert old item types to unified ITEM type")
    args = parser.parse_args()
    input_path, output_path = resolve_paths(args)

    if input_path.is_dir():
        process_directory(input_path, output_path, processor, backup=args.backup)
    else:
        from common import backup_file, load_json

        if args.backup:
            backup_file(input_path)
        data = load_json(input_path)
        transformed = processor(data, input_path)
        save_json(output_path, transformed)
        print(f"Updated: {output_path}")


if __name__ == "__main__":
    main()
