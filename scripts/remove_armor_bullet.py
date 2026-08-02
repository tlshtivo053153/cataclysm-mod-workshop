#!/usr/bin/env python3
"""Remove ARMOR_BULLET and ARMOR_BALLISTIC values from enchantment definitions."""

import sys

from common import MAX_RECURSION_DEPTH, run_standard_pipeline

TARGET_VALUES = {"ARMOR_BULLET", "ARMOR_BALLISTIC"}


MAX_DEPTH = MAX_RECURSION_DEPTH


def clean_object(obj, _depth=0):
    if _depth > MAX_DEPTH:
        if _depth == MAX_DEPTH + 1:
            print(
                f"Warning: max recursion depth ({MAX_DEPTH}) exceeded in remove_armor_bullet",
                file=sys.stderr,
            )
        return obj
    if not isinstance(obj, dict):
        return obj

    if "value" in obj and obj["value"] in TARGET_VALUES:
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


def processor(data, _path):
    if isinstance(data, list):
        data = [clean_object(item) for item in data]
        data = [item for item in data if item is not None]
        return data
    elif isinstance(data, dict):
        return clean_object(data)
    return data


def main():
    run_standard_pipeline("Remove ARMOR_BULLET/BALLISTIC enchantment values", processor)


if __name__ == "__main__":
    main()
