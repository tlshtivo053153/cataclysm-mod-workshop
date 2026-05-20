#!/usr/bin/env python3
"""Remove ARMOR_BULLET and ARMOR_BALLISTIC values from enchantment definitions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import create_parser, process_directory, resolve_paths, save_json

TARGET_VALUES = {"ARMOR_BULLET", "ARMOR_BALLISTIC"}


def clean_object(obj):
    if not isinstance(obj, dict):
        return obj

    # Check if this is a values array item we want to remove
    if "value" in obj and obj["value"] in TARGET_VALUES:
        return None

    for key, value in list(obj.items()):
        if isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    cleaned = clean_object(item)
                    if cleaned is not None:
                        new_list.append(cleaned)
                else:
                    new_list.append(item)
            obj[key] = new_list
        elif isinstance(value, dict):
            cleaned = clean_object(value)
            if cleaned is None:
                del obj[key]
            else:
                obj[key] = cleaned
    return obj


def processor(data, _path):
    if isinstance(data, list):
        data = [clean_object(item) for item in data]
        data = [item for item in data if item is not None]
        return data
    elif isinstance(data, dict):
        return clean_object(data)
    return data


def main():
    parser = create_parser("Remove ARMOR_BULLET/BALLISTIC enchantment values")
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
