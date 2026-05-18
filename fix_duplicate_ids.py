#!/usr/bin/env python3
import json
import re

# Read the file
with open('/home/tlsh/cataclysm/cdda_mod_framework/external/cdda/mods/Magiclysm_with_Random_Dungeons-0I/monsters/monstergroups.json', 'r') as f:
    content = f.read()

# Parse the JSON array
data = json.loads(content)

# Write back (this will remove duplicates as json.loads only keeps the last value for duplicate keys)
with open('/home/tlsh/cataclysm/cdda_mod_framework/external/cdda/mods/Magiclysm_with_Random_Dungeons-0I/monsters/monstergroups.json', 'w') as f:
    json.dump(data, f, indent=4)
    f.write('\n')

print("Fixed duplicate IDs in monstergroups.json")
