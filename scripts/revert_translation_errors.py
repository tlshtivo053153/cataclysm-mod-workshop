#!/usr/bin/env python3
"""Revert name fields from translation objects back to strings for types that don't support it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import create_parser, process_directory, resolve_paths, save_json

# Types that do NOT support translation objects for 'name' field
TYPES_WITH_STRING_NAME = {
    "MONSTER_FACTION",
    "monstergroup",
    # Add more if needed
}


def revert_name_fields(obj):
    """Revert name fields that are objects back to strings for unsupported types."""
    if isinstance(obj, dict):
        obj_type = obj.get("type", "")
        if obj_type in TYPES_WITH_STRING_NAME and "name" in obj and isinstance(obj["name"], dict):
            if "str_sp" in obj["name"]:
                obj["name"] = obj["name"]["str_sp"]
            elif "str" in obj["name"]:
                obj["name"] = obj["name"]["str"]
        for v in obj.values():
            revert_name_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            revert_name_fields(item)
    return obj


def processor(data, _path):
    if isinstance(data, list):
        for item in data:
            revert_name_fields(item)
    elif isinstance(data, dict):
        revert_name_fields(data)
    return data


def main():
    parser = create_parser("Revert translation objects for name fields on unsupported types")
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
