import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


_PALETTE_FIELD_KEYS = (
    "terrain",
    "furniture",
    "items",
    "monsters",
    "traps",
    "fields",
    "vehicles",
    "nested",
)


def _extract_cdda_palette_fields(obj: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fields: dict[str, dict[str, Any]] = {}
    for key in _PALETTE_FIELD_KEYS:
        if key in obj and isinstance(obj[key], dict):
            fields[key] = obj[key]
    palettes = obj.get("palettes")
    if isinstance(palettes, list) and all(isinstance(p, str) for p in palettes):
        fields["palettes"] = {p: {} for p in palettes}
    elif isinstance(palettes, str):
        fields["palettes"] = {palettes: {}}
    return fields


def _cdda_list_to_palettes(items: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for obj in items:
        if isinstance(obj, dict) and obj.get("type") == "palette":
            pid = obj.get("id")
            if pid:
                result[pid] = _extract_cdda_palette_fields(obj)
    return result


def _cdda_dict_to_palettes(obj: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pid = obj.get("id")
    if pid:
        return {pid: _extract_cdda_palette_fields(obj)}
    return {}


def _load_json_palettes(path: Path) -> dict[str, dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Failed to load palettes from %s: %s", path, e)
        return {}

    if isinstance(raw, list):
        return _cdda_list_to_palettes(raw)
    if isinstance(raw, dict):
        if raw.get("type") == "palette":
            return _cdda_dict_to_palettes(raw)
        if all(isinstance(v, dict) for v in raw.values()):
            return raw
        logger.warning(
            "Skipping %s — dict JSON without 'type: palette' "
            "must contain only dict values (palette field mappings)",
            path,
        )
        return {}
    return {}


def _load_all_palettes(palette_paths: list[Path] | None = None) -> dict[str, dict[str, Any]]:
    builtin_path = Path(__file__).resolve().parent / "palettes.json"
    merged: dict[str, dict[str, Any]] = {}
    merged.update(_load_json_palettes(builtin_path))
    if palette_paths:
        for path in palette_paths:
            if path.is_file() and path.suffix == ".json":
                merged.update(_load_json_palettes(path))
            elif path.is_dir():
                for f in sorted(path.glob("*.json")):
                    merged.update(_load_json_palettes(f))
    return _resolve_palette_inheritance(merged)


def _resolve_palette_inheritance(
    palettes: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}

    def _resolve(name: str, seen: tuple[str, ...]) -> dict[str, Any]:
        if name in resolved:
            return resolved[name]
        if name in seen:
            logger.warning("Circular palette inheritance detected: %s", " -> ".join([*seen, name]))
            return {}
        raw = palettes.get(name)
        if raw is None:
            return {}
        parents = raw.get("palettes", {})
        parent_names = list(parents.keys()) if isinstance(parents, dict) else []
        out: dict[str, dict[str, Any]] = {}
        for parent in parent_names:
            parent_fields = _resolve(parent, (*seen, name))
            for key, mapping in parent_fields.items():
                if key == "palettes" or not isinstance(mapping, dict):
                    continue
                out.setdefault(key, {}).update(mapping)
        for key, mapping in raw.items():
            if key == "palettes" or not isinstance(mapping, dict):
                continue
            out.setdefault(key, {}).update(mapping)
        resolved[name] = out
        return out

    for pname in list(palettes.keys()):
        _resolve(pname, ())
    return resolved


class PaletteRegistry:
    """Registry of CDDA palette definitions, keyed by palette ID."""

    def __init__(self, palette_paths: list[Path] | None = None) -> None:
        self._palettes = _load_all_palettes(palette_paths)
        self._unknown_reported: set[str] = set()

    def get_palette(self, name: str) -> dict[str, Any] | None:
        palette = self._palettes.get(name)
        if palette is None and name not in self._unknown_reported:
            self._unknown_reported.add(name)
            logger.info("Unknown palette '%s' — skipping", name)
        return palette

    def is_char_known(self, palette_name: str, char: str) -> bool:
        palette = self.get_palette(palette_name)
        if palette is None:
            return False
        return any(
            isinstance(palette.get(key), dict) and char in palette[key]
            for key in _PALETTE_FIELD_KEYS
        )

    def explain_char(self, palette_name: str, char: str) -> str | None:
        palette = self.get_palette(palette_name)
        if palette is None:
            return None
        for key in _PALETTE_FIELD_KEYS:
            entry = palette.get(key, {}).get(char)
            if entry is None:
                continue
            if isinstance(entry, dict):
                if not entry:
                    continue
                if "ter" in entry:
                    return cast(str, entry["ter"])
                if "terrain" in entry:
                    return cast(str, entry["terrain"])
                continue
            return cast(str, entry)
        return None


_default_registry: PaletteRegistry | None = None


def get_registry(palette_paths: list[Path] | None = None) -> PaletteRegistry:
    global _default_registry
    if palette_paths is not None:
        return PaletteRegistry(palette_paths)
    if _default_registry is None:
        _default_registry = PaletteRegistry()
    return _default_registry


def get_palette(name: str) -> dict[str, Any] | None:
    return get_registry().get_palette(name)


def is_char_known(palette_name: str, char: str) -> bool:
    return get_registry().is_char_known(palette_name, char)
