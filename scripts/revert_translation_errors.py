#!/usr/bin/env python3
"""Revert name fields from translation objects back to strings for types that don't support it."""

from common import revert_translation_field, run_standard_pipeline

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
        if obj_type in TYPES_WITH_STRING_NAME and "name" in obj:
            obj["name"] = revert_translation_field(obj["name"])
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
    run_standard_pipeline("Revert translation objects for name fields on unsupported types", processor)


if __name__ == "__main__":
    main()
