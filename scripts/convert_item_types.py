#!/usr/bin/env python3
"""Convert old item types to new unified ITEM type with subtypes for CDDA 0.I."""

from common import run_standard_pipeline

TYPE_MAP = {
    "TOOL": ["TOOL"],
    "GUN": ["GUN"],
    "ARMOR": ["ARMOR"],
    "TOOL_ARMOR": ["TOOL", "ARMOR"],
    "COMESTIBLE": ["COMESTIBLE"],
    "GENERIC": ["GENERIC"],
    "BOOK": ["BOOK"],
    "AMMO": ["AMMO"],
    "MAGAZINE": ["MAGAZINE"],
    "GUNMOD": ["GUNMOD"],
    "BIONIC_ITEM": ["BIONIC_ITEM"],
    "SEED": ["SEED"],
    "MILLING": ["MILLING"],
    "PET_ARMOR": ["PET_ARMOR"],
    "WHEEL": ["WHEEL"],
    "ENGINE": ["ENGINE"],
    "BREWABLE": ["BREWABLE"],
    "ARTIFACT": ["ARTIFACT"],
    "TOOLMOD": ["TOOLMOD"],
    "COMPOSTABLE": ["COMPOSTABLE"],
}


def convert_object(obj):
    if not isinstance(obj, dict):
        return obj

    if "type" in obj and obj["type"] in TYPE_MAP:
        old_type = obj["type"]
        obj["type"] = "ITEM"
        obj["subtypes"] = TYPE_MAP[old_type]

    # Recurse into known list fields that may contain objects
    for key, value in obj.items():
        if isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    new_list.append(convert_object(item))
                else:
                    new_list.append(item)
            obj[key] = new_list
        elif isinstance(value, dict):
            obj[key] = convert_object(value)

    return obj


def processor(data, _path):
    if isinstance(data, list):
        return [convert_object(item) for item in data]
    elif isinstance(data, dict):
        return convert_object(data)
    return data


def main():
    run_standard_pipeline("Convert old item types to unified ITEM type", processor)


if __name__ == "__main__":
    main()
