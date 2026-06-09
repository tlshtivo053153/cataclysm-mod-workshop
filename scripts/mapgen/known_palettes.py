import json
import sys
from pathlib import Path


def _load_json_palettes(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to load palettes from {path}: {e}", file=sys.stderr)
        return {}


def _load_all_palettes(palette_paths: list[Path] | None = None) -> dict[str, dict[str, dict[str, str]]]:
    builtin_path = Path(__file__).resolve().parent / "palettes.json"
    merged: dict[str, dict[str, dict[str, str]]] = {}
    builtin = _load_json_palettes(builtin_path)
    if isinstance(builtin, dict):
        merged.update(builtin)
    if palette_paths:
        for path in palette_paths:
            if path.is_file() and path.suffix == ".json":
                data = _load_json_palettes(path)
                if isinstance(data, dict):
                    merged.update(data)
            elif path.is_dir():
                for f in sorted(path.glob("*.json")):
                    data = _load_json_palettes(f)
                    if isinstance(data, dict):
                        merged.update(data)
    return merged


class PaletteRegistry:
    def __init__(self, palette_paths: list[Path] | None = None) -> None:
        self._palettes = _load_all_palettes(palette_paths)
        self._unknown_reported: set[str] = set()

    def get_palette(self, name: str) -> dict[str, dict[str, str]] | None:
        palette = self._palettes.get(name)
        if palette is None and name not in self._unknown_reported:
            self._unknown_reported.add(name)
            print(f"Info: unknown palette '{name}' — skipping", file=sys.stderr)
        return palette

    def is_char_known(self, palette_name: str, char: str) -> bool:
        palette = self.get_palette(palette_name)
        if palette is None:
            return False
        return char in palette.get("terrain", {}) or char in palette.get("furniture", {})


_default_registry: PaletteRegistry | None = None


def get_registry(palette_paths: list[Path] | None = None) -> PaletteRegistry:
    global _default_registry
    if palette_paths is not None:
        return PaletteRegistry(palette_paths)
    if _default_registry is None:
        _default_registry = PaletteRegistry()
    return _default_registry


def get_palette(name: str) -> dict[str, dict[str, str]] | None:
    return get_registry().get_palette(name)


def is_char_known(palette_name: str, char: str) -> bool:
    return get_registry().is_char_known(palette_name, char)
