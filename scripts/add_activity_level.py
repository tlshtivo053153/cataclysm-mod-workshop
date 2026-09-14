#!/usr/bin/env python3
"""Add activity_level to all recipe objects in JSON files."""

import copy
import json
import sys
from pathlib import Path
from typing import Any

from common import create_parser, process_directory, process_file, resolve_paths

DEFAULT_ACTIVITY = "LIGHT_EXERCISE"

_activity_map: dict[str, str] = {}


def load_activity_config(config_path: Path) -> None:
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    _activity_map.clear()
    _activity_map.update(data)


def add_activity_level(data: list[Any]) -> list[Any]:
    for obj in data:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "recipe":
            continue
        if "activity_level" in obj:
            continue

        subcategory = obj.get("subcategory", "")
        activity = _activity_map.get(subcategory, DEFAULT_ACTIVITY)

        new_obj: dict[str, Any] = {}
        for key, value in obj.items():
            new_obj[key] = value
            if key == "type":
                new_obj["activity_level"] = activity
        obj.clear()
        obj.update(new_obj)
    return data


def processor(data: Any, _path: Path) -> Any | None:
    if not isinstance(data, list):
        return None
    original = copy.deepcopy(data)
    result = add_activity_level(data)
    if result == original:
        return None
    return result


def main() -> None:
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
        result = process_directory(input_path, output_path, processor, backup=args.backup)
    else:
        result = process_file(input_path, output_path, processor, backup=args.backup)

    print(
        f"Updated {result.processed} files, skipped {result.skipped}, " f"failed {result.failed}."
    )

    if result.has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
