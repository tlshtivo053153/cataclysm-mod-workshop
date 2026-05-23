#!/usr/bin/env python3
"""Remove ARMOR_BULLET and ARMOR_BALLISTIC values from enchantment definitions."""

from common import run_standard_pipeline

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
    run_standard_pipeline("Remove ARMOR_BULLET/BALLISTIC enchantment values", processor)


if __name__ == "__main__":
    main()
