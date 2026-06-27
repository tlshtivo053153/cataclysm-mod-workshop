"""Tier-0 constants shared across the mapgen compiler package.

This module has no dependencies on other mapgen modules and may be imported
freely from anywhere in the package.
"""

STAIR_CHARS: set[str] = {">", "<", "*", "^"}
FALLBACK_DOOR_CHAR: str = "+"

KNOWN_KEYS: set[str] = {
    "om_terrain",
    "fill_ter",
    "palette",
    "rooms",
    "doors",
    "features",
    "global",
    "canvas",
    "layout",
    "auto_doors",
    "default_door_char",
    "no_door",
}

COMPILER_KEYS: set[str] = {"fill_ter", "rows", "palettes"}

_RELATIVE_KEYS: set[str] = {"right_of", "left_of", "above", "below", "inside", "align", "gap"}
