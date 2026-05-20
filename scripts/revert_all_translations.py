#!/usr/bin/env python3
"""Revert ALL name translation objects back to strings."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import create_parser, process_directory, resolve_paths, save_json


def revert_all_name_fields(obj):
    """Revert all name fields that are translation objects back to strings."""
    if isinstance(obj, dict):
        if "name" in obj and isinstance(obj["name"], dict):
            if "str_sp" in obj["name"]:
                obj["name"] = obj["name"]["str_sp"]
            elif "str" in obj["name"]:
                obj["name"] = obj["name"]["str"]
        if "description" in obj and isinstance(obj["description"], dict):
            if "str_sp" in obj["description"]:
                obj["description"] = obj["description"]["str_sp"]
            elif "str" in obj["description"]:
                obj["description"] = obj["description"]["str"]
        for v in obj.values():
            revert_all_name_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            revert_all_name_fields(item)
    return obj


def processor(data, _path):
    if isinstance(data, list):
        for item in data:
            revert_all_name_fields(item)
    elif isinstance(data, dict):
        revert_all_name_fields(data)
    return data


def main():
    parser = create_parser("Revert all name/description translation objects to strings")
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
