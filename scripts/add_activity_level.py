#!/usr/bin/env python3
"""Add activity_level to all recipe objects in JSON files."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import is_unchanged, run_standard_pipeline, snapshot

DEFAULT_ACTIVITY = "LIGHT_EXERCISE"

_activity_map: dict[str, str] = {}


def load_activity_config(config_path: Path) -> None:
    """Load subcategory -> activity_level mapping with validation.

    Raises OSError/ValueError with a clean message on missing/unparseable
    files or invalid schema (must be a JSON object of str -> str).
    """
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {config_path}", file=sys.stderr)
        raise
    except UnicodeDecodeError as e:
        print(f"ERROR: Cannot decode {config_path} as UTF-8: {e}", file=sys.stderr)
        raise
    except OSError as e:
        print(f"ERROR: Cannot read config {config_path}: {e}", file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print(f"JSON parse error in {config_path}: {e}", file=sys.stderr)
        raise
    if not isinstance(data, dict):
        print(
            f"ERROR: Invalid activity config {config_path}: "
            f"expected JSON object, got {type(data).__name__}",
            file=sys.stderr,
        )
        raise ValueError(f"Invalid activity config: {config_path}")
    invalid = {
        k: v for k, v in data.items() if not isinstance(k, str) or not isinstance(v, str) or not v
    }
    if invalid:
        print(
            f"ERROR: Invalid activity config {config_path}: "
            f"all keys/values must be strings (bad: {sorted(invalid)[:5]})",
            file=sys.stderr,
        )
        raise ValueError(f"Invalid activity config: {config_path}")
    _activity_map.clear()
    _activity_map.update(data)


def add_activity_level(data: list[Any]) -> list[Any]:
    for obj in data:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "recipe":
            continue
        if isinstance(obj.get("activity_level"), str) and obj["activity_level"]:
            continue

        subcategory = obj.get("subcategory", "")
        activity = _activity_map.get(subcategory, DEFAULT_ACTIVITY)

        new_obj: dict[str, Any] = {}
        for key, value in obj.items():
            if key == "activity_level":
                continue
            new_obj[key] = value
            if key == "type":
                new_obj["activity_level"] = activity
        obj.clear()
        obj.update(new_obj)
    return data


def processor(data: Any, _path: Path) -> Any | None:
    if not isinstance(data, list):
        return None
    original = snapshot(data)
    result = add_activity_level(data)
    if is_unchanged(original, result):
        return None
    return result


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="JSON file mapping subcategory to activity_level",
    )


def _setup(args: argparse.Namespace) -> int | None:
    if args.config:
        try:
            load_activity_config(args.config)
        except (OSError, ValueError):
            return 1
    return None


def main() -> int:
    return run_standard_pipeline(
        "Add activity_level to recipe objects",
        processor,
        configure=_configure,
        setup=_setup,
    )


if __name__ == "__main__":
    sys.exit(main())
