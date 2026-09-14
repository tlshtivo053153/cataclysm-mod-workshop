#!/usr/bin/env python3
"""Revert name fields from translation objects back to strings for types that don't support it."""

import copy
import sys

from common import MAX_RECURSION_DEPTH, revert_translation_field, run_standard_pipeline

# Types that do NOT support translation objects for 'name' field
TYPES_WITH_STRING_NAME = {
    "MONSTER_FACTION",
    "monstergroup",
    # Add more if needed
}


MAX_DEPTH = MAX_RECURSION_DEPTH


def revert_name_fields(obj, _depth=0):
    """Revert name fields that are objects back to strings for unsupported types."""
    if _depth > MAX_DEPTH:
        if _depth == MAX_DEPTH + 1:
            print(
                f"Warning: max recursion depth ({MAX_DEPTH}) exceeded in "
                f"revert_translation_errors",
                file=sys.stderr,
            )
        return obj
    if isinstance(obj, dict):
        obj_type = obj.get("type", "")
        if obj_type in TYPES_WITH_STRING_NAME and "name" in obj:
            obj["name"] = revert_translation_field(obj["name"])
        for v in obj.values():
            revert_name_fields(v, _depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            revert_name_fields(item, _depth + 1)
    return obj


def processor(data, _path):
    if isinstance(data, (list, dict)):
        original = copy.deepcopy(data)
        if isinstance(data, list):
            for item in data:
                revert_name_fields(item)
        else:
            revert_name_fields(data)
        if data == original:
            return None
        return data
    return None


def main():
    run_standard_pipeline(
        "Revert translation objects for name fields on unsupported types", processor
    )


if __name__ == "__main__":
    main()
