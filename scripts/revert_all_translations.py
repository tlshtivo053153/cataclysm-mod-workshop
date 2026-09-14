#!/usr/bin/env python3
"""Revert ALL name translation objects back to strings."""

import sys
from pathlib import Path
from typing import Any

from common import (
    depth_exceeded,
    is_unchanged,
    revert_translation_field,
    run_standard_pipeline,
    snapshot,
)


def revert_all_name_fields(obj: Any, _depth: int = 0) -> Any:
    """Revert all name fields that are translation objects back to strings."""
    if depth_exceeded(_depth, "revert_all_translations"):
        return obj
    if isinstance(obj, dict):
        if "name" in obj:
            obj["name"] = revert_translation_field(obj["name"])
        if "description" in obj:
            obj["description"] = revert_translation_field(obj["description"])
        for v in obj.values():
            revert_all_name_fields(v, _depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            revert_all_name_fields(item, _depth + 1)
    return obj


def processor(data: Any, _path: Path) -> Any | None:
    if isinstance(data, (list, dict)):
        original = snapshot(data)
        if isinstance(data, list):
            for item in data:
                revert_all_name_fields(item)
        else:
            revert_all_name_fields(data)
        if is_unchanged(original, data):
            return None
        return data
    return None


def main() -> int:
    return run_standard_pipeline(
        "Revert all name/description translation objects to strings", processor
    )


if __name__ == "__main__":
    sys.exit(main())
