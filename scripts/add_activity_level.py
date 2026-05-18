#!/usr/bin/env python3
"""
Add activity_level to all recipe objects in JSON files.
"""
import json
import sys
from pathlib import Path

# Mapping from subcategory to activity_level
ACTIVITY_MAP = {
    "CSC_PSY_MAGI_EQUIPMENT": "BRISK_EXERCISE",
    "CSC_PSY_MAGI_UPGRADE": "BRISK_EXERCISE",
    "CSC_PSY_MAGI_ROBOT": "MODERATE_EXERCISE",
    "CSC_PSY_MAGI_SCROLL": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_ENHANCEMENT": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_HONEY": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_NORMALSPELLS": "LIGHT_EXERCISE",
    "CSC_PSY_MAGI_ULTIMATESPELLS": "LIGHT_EXERCISE",
}

DEFAULT_ACTIVITY = "LIGHT_EXERCISE"


def add_activity_level(data: list) -> list:
    for obj in data:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "recipe":
            continue
        if "activity_level" in obj:
            continue

        subcategory = obj.get("subcategory", "")
        activity = ACTIVITY_MAP.get(subcategory, DEFAULT_ACTIVITY)

        # Insert activity_level right after "type" for readability
        new_obj = {}
        for key, value in obj.items():
            new_obj[key] = value
            if key == "type":
                new_obj["activity_level"] = activity
        obj.clear()
        obj.update(new_obj)
    return data


def process_file(path: Path) -> None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"Skip {path}: root is not a list")
        return

    modified = add_activity_level(data)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(modified, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Updated: {path}")


def main():
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("external/cdda/mods/Magiclysm_with_Random_Dungeons-0I/recipes")
    if not target_dir.exists():
        print(f"Directory not found: {target_dir}")
        sys.exit(1)

    for json_file in sorted(target_dir.rglob("*.json")):
        try:
            process_file(json_file)
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
