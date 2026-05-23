#!/usr/bin/env python3
"""Revert ALL name translation objects back to strings."""

from common import run_standard_pipeline


def revert_all_name_fields(obj):
    """Revert all name fields that are translation objects back to strings."""
    if isinstance(obj, dict):
        if "name" in obj and isinstance(obj["name"], dict):
            if "str_sp" in obj["name"]:
                obj["name"] = obj["name"]["str_sp"]
            elif "str" in obj["name"]:
                obj["name"] = obj["name"]["str"]
        if "description" in obj and isinstance(obj["description"], dict):
            if "str_sp" in obj["description"]:
                obj["description"] = obj["description"]["str_sp"]
            elif "str" in obj["description"]:
                obj["description"] = obj["description"]["str"]
        for v in obj.values():
            revert_all_name_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            revert_all_name_fields(item)
    return obj


def processor(data, _path):
    if isinstance(data, list):
        for item in data:
            revert_all_name_fields(item)
    elif isinstance(data, dict):
        revert_all_name_fields(data)
    return data


def main():
    run_standard_pipeline("Revert all name/description translation objects to strings", processor)


if __name__ == "__main__":
    main()
