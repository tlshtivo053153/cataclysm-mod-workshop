#!/usr/bin/env python3
"""Remove invalid JSON fields from CDDA mod files."""

import json
import os
import sys
from pathlib import Path

# Invalid fields to remove (from debug.log analysis)
INVALID_FIELDS = {
    "method",
    "bashing",
    "armor_bullet", "armor_cut", "armor_bash", "armor_stab", 
    "armor_elec", "armor_acid", "armor_fire",
    "relic_data",
    "melee_cut", "cutting",
    "magazine",
    "passive_mods",
    "ammo",
    "mana_regen_multiplier", "mana_modifier",
    "stamina_regen_modifier",
    "sound_volume", "sound_msg",
    "no_deactivate_msg",
    "rot_spawn_chance",
    "baby_egg",
    "var_name",
    "standard_symbols",
    "hp_modifier",
    "charges_per_use",
    "countdown_destroy",
}

def remove_invalid_fields(obj):
    """Recursively remove invalid fields from a JSON object."""
    if isinstance(obj, dict):
        # Remove invalid fields
        keys_to_remove = [k for k in obj.keys() if k in INVALID_FIELDS]
        for k in keys_to_remove:
            del obj[k]
        # Recurse into remaining values
        for v in obj.values():
            remove_invalid_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            remove_invalid_fields(item)
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
            remove_invalid_fields(item)
    else:
        remove_invalid_fields(data)
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')
    
    return True

def main():
    mod_dir = Path("/home/tlsh/cataclysm/cdda_mod_framework/external/cdda/mods/Magiclysm_with_Random_Dungeons-0I")
    
    json_files = list(mod_dir.rglob("*.json"))
    print(f"Processing {len(json_files)} JSON files...")
    
    success_count = 0
    for json_file in json_files:
        if process_file(json_file):
            success_count += 1
    
    print(f"Successfully processed {success_count}/{len(json_files)} files.")

if __name__ == "__main__":
    main()
