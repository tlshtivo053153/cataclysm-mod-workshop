#!/usr/bin/env python3
"""Revert ALL name translation objects back to strings."""

import copy
import sys

from common import MAX_RECURSION_DEPTH, revert_translation_field, run_standard_pipeline

MAX_DEPTH = MAX_RECURSION_DEPTH


def revert_all_name_fields(obj, _depth=0):
    """Revert all name fields that are translation objects back to strings."""
    if _depth > MAX_DEPTH:
        if _depth == MAX_DEPTH + 1:
            print(
                f"Warning: max recursion depth ({MAX_DEPTH}) exceeded in revert_all_translations",
                file=sys.stderr,
            )
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


def processor(data, _path):
    if isinstance(data, (list, dict)):
        original = copy.deepcopy(data)
        if isinstance(data, list):
            for item in data:
                revert_all_name_fields(item)
        else:
            revert_all_name_fields(data)
        if data == original:
            return None
        return data
    return None


def main():
    run_standard_pipeline("Revert all name/description translation objects to strings", processor)


if __name__ == "__main__":
    main()
