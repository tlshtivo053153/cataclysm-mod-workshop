#!/usr/bin/env python3
"""Add activity_level to all recipe objects in JSON files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import create_parser, process_directory, resolve_paths, save_json

# Mapping from subcategory to activity_level
ACTIVITY_MAP = {
    "CSC_PSY_MAGI_EQUIPMENT": "BRISK_EXERCISE",
    "CSC_PSY_MAGI_UPGRADE": "BRISK_EXERCISE",
    "CSC_PSY_MAGI_ROBOT": "MODERATE_EXERCISE",
    "CSC_PSY_MAGI_SCROLL": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_ENHANCEMENT": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_HONEY": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_NORMALSPELLS": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_ULTIMATESPELLS": "LIGHT_EXERCISE",
}

DEFAULT_ACTIVITY = "LIGHT_EXERCISE"


def add_activity_level(data: list) -> list:
    for obj in data:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "recipe":
            continue
        if "activity_level" in obj:
            continue

        subcategory = obj.get("subcategory", "")
        activity = ACTIVITY_MAP.get(subcategory, DEFAULT_ACTIVITY)

        # Insert activity_level right after "type" for readability
        new_obj = {}
        for key, value in obj.items():
            new_obj[key] = value
            if key == "type":
                new_obj["activity_level"] = activity
        obj.clear()
        obj.update(new_obj)
    return data


def processor(data, _path):
    if not isinstance(data, list):
        return None
    return add_activity_level(data)


def main():
    parser = create_parser("Add activity_level to recipe objects")
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
        if transformed is not None:
            save_json(output_path, transformed)
            print(f"Updated: {output_path}")


if __name__ == "__main__":
    main()
