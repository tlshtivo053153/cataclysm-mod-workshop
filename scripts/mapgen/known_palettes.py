import json
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_palettes() -> dict[str, dict[str, dict[str, str]]]:
    path = Path(__file__).resolve().parent / "palettes.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to load palettes from {path}: {e}", file=sys.stderr)
        return {}


def get_palette(name: str) -> dict[str, dict[str, str]] | None:
    return _load_palettes().get(name)


def is_char_known(palette_name: str, char: str) -> bool:
    palette = get_palette(palette_name)
    if palette is None:
        return False
    return char in palette.get("terrain", {}) or char in palette.get("furniture", {})
