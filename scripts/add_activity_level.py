#!/usr/bin/env python3
"""Add activity_level to all recipe objects in JSON files."""

import json
from pathlib import Path

from common import create_parser, process_directory, process_file, resolve_paths

DEFAULT_ACTIVITY = "LIGHT_EXERCISE"

_activity_map: dict[str, str] = {}


def load_activity_config(config_path: Path) -> None:
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    _activity_map.clear()
    _activity_map.update(data)


def add_activity_level(data: list) -> list:
    for obj in data:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "recipe":
            continue
        if "activity_level" in obj:
            continue

        subcategory = obj.get("subcategory", "")
        activity = _activity_map.get(subcategory, DEFAULT_ACTIVITY)

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
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="JSON file mapping subcategory to activity_level",
    )
    args = parser.parse_args()

    if args.config:
        load_activity_config(args.config)

    input_path, output_path = resolve_paths(args)

    if input_path.is_dir():
        count = process_directory(input_path, output_path, processor, backup=args.backup)
        print(f"Updated {count} files.")
    else:
        process_file(input_path, output_path, processor, backup=args.backup)


if __name__ == "__main__":
    main()
