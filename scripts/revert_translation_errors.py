#!/usr/bin/env python3
"""Revert name fields from translation objects back to strings for types that don't support it."""

import json
import sys
from pathlib import Path

# Types that do NOT support translation objects for 'name' field
# Based on CDDA 0.I behavior
TYPES_WITH_STRING_NAME = {
    "MONSTER_FACTION",
    "monstergroup",
    # Add more if needed
}

def revert_name_fields(obj):
    """Revert name fields that are objects back to strings for unsupported types."""
    if isinstance(obj, dict):
        # Check if this object has a type that doesn't support translation objects
        obj_type = obj.get('type', '')
        if obj_type in TYPES_WITH_STRING_NAME:
            # Revert 'name' field if it's a translation object
            if 'name' in obj and isinstance(obj['name'], dict):
                if 'str_sp' in obj['name']:
                    obj['name'] = obj['name']['str_sp']
                elif 'str' in obj['name']:
                    obj['name'] = obj['name']['str']
        # Recurse into all values
        for v in obj.values():
            revert_name_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            revert_name_fields(item)
    return obj

def process_file(filepath):
    """Process a single JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
        return False
    
    # Handle both single objects and arrays
    if isinstance(data, list):
        for item in data:
            revert_name_fields(item)
    else:
        revert_name_fields(data)
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')
    
    return True

def main():
    mod_dir = Path("/home/tlsh/cataclysm/cdda_mod_framework/external/cdda/mods/Magiclysm_with_Random_Dungeons-0I")
    
    json_files = list(mod_dir.rglob("*.json"))
    print(f"Processing {len(json_files)} JSON files to revert name fields...")
    
    success_count = 0
    for json_file in json_files:
        if process_file(json_file):
            success_count += 1
    
    print(f"Successfully processed {success_count}/{len(json_files)} files.")

if __name__ == "__main__":
    main()
