#!/usr/bin/env python3
import json
import sys
from pathlib import Path

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

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    data = json.loads(content)
    if isinstance(data, list):
        data = [clean_object(item) for item in data]
        data = [item for item in data if item is not None]
    elif isinstance(data, dict):
        data = clean_object(data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")

def main():
    target_dir = Path(sys.argv[1])
    for filepath in target_dir.rglob("*.json"):
        try:
            process_file(filepath)
            print(f"Processed: {filepath}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
