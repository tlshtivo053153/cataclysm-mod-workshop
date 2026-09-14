#!/usr/bin/env python3
"""Remove ARMOR_BULLET and ARMOR_BALLISTIC values from enchantment definitions."""

import sys
from pathlib import Path
from typing import Any

from common import depth_exceeded, is_unchanged, run_standard_pipeline, snapshot

TARGET_VALUES = {"ARMOR_BULLET", "ARMOR_BALLISTIC"}


def clean_object(obj: Any, _depth: int = 0) -> Any:
    if depth_exceeded(_depth, "remove_armor_bullet"):
        return obj
    if not isinstance(obj, dict):
        return obj

    if "value" in obj and isinstance(obj["value"], str) and obj["value"] in TARGET_VALUES:
        return None

    for key, value in list(obj.items()):
        if isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    cleaned = clean_object(item, _depth + 1)
                    if cleaned is not None:
                        new_list.append(cleaned)
                else:
                    new_list.append(item)
            obj[key] = new_list
        elif isinstance(value, dict):
            cleaned = clean_object(value, _depth + 1)
            if cleaned is None:
                del obj[key]
            else:
                obj[key] = cleaned
    return obj


def processor(data: Any, _path: Path) -> Any | None:
    if not isinstance(data, (list, dict)):
        return None
    original: Any = snapshot(data)
    if isinstance(data, list):
        cleaned: Any = [clean_object(item) for item in data]
        cleaned = [item for item in cleaned if item is not None]
        if is_unchanged(original, cleaned):
            return None
        return cleaned
    result: Any = clean_object(data)
    if result is None:
        # Top-level dict itself matched TARGET_VALUES; nothing sensible
        # to save, so treat as skipped rather than writing null.
        return None
    if is_unchanged(original, result):
        return None
    return result


def main() -> int:
    return run_standard_pipeline("Remove ARMOR_BULLET/BALLISTIC enchantment values", processor)


if __name__ == "__main__":
    sys.exit(main())
