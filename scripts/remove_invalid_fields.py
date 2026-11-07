#!/usr/bin/env python3
"""Remove invalid JSON fields from CDDA mod files.

Field validity depends on context: some names (e.g. ``ammo``, ``magazine``)
are obsolete in old mods but fully valid in current CDDA data (item definitions,
item groups, vehicle loot, monster reproduction, ...).  Deleting by key name
alone destroys valid data, so removal is split into two rules loaded from
``rules/invalid_fields.json``:

- ``remove_always``: field names invalid in every context (e.g. ``armor_bullet``).
- ``remove_by_type``: ``{TYPE: [fields...]}`` — a field is removed only when the
  enclosing object's ``type`` matches.  Objects with a missing, non-string, or
  unlisted ``type`` keep the field with a stderr warning (conservative).

NOTE: ``remove_by_type`` is intentionally empty for now.  The 5 context-dependent
fields are valid in current CDDA so they must NOT be in ``remove_always``:
``ammo`` (GUN/item_group/vehicle_part/mapgen/monster-reproduction, NOT TOOL/AMMO),
``magazine`` (item_group/mapgen), ``sound_volume`` (sound/vehicle_data),
``baby_egg`` (MONSTER/baby_type nesting), ``charges_per_use`` (TOOL).
Do not repopulate ``remove_by_type`` without src/ reader evidence for
a specific TYPE.  ``relic_data`` is also valid (MAGIC.md: artifacts via
``relic_data``) and must NOT be listed for removal.

This script is repo-execution only: it reads ``PROJECT_ROOT/rules/...``, so it
is intentionally not console-script packaged.
"""

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from common import depth_exceeded, is_unchanged, run_standard_pipeline, snapshot

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVALID_FIELDS_PATH = PROJECT_ROOT / "rules" / "invalid_fields.json"


@dataclass
class InvalidFieldsConfig:
    """Type-aware removal rules."""

    remove_always: set[str] = field(default_factory=set)
    remove_by_type: dict[str, set[str]] = field(default_factory=dict)


def load_invalid_fields(path: Path | None = None) -> InvalidFieldsConfig:
    """Load and validate the removal rules from rules/invalid_fields.json.

    Expected format::

        {"remove_always": [...], "remove_by_type": {"TYPE": [...]}}.

    Raises ValueError on any schema violation (including the legacy bare-list
    format, which is rejected fail-closed so old destructive lists cannot
    silently resume deleting valid fields).
    """
    target = INVALID_FIELDS_PATH if path is None else path
    with open(target, encoding="utf-8") as f:
        raw = json.load(f)
    return parse_invalid_fields(raw)


def parse_invalid_fields(raw: Any) -> InvalidFieldsConfig:
    """Validate a decoded JSON value and build an InvalidFieldsConfig."""
    if isinstance(raw, list):
        raise ValueError(
            "legacy list format is no longer supported; use "
            '{"remove_always": [...], "remove_by_type": {...}}'
        )
    if not isinstance(raw, dict):
        raise ValueError(f"invalid format: top level must be an object, got {type(raw).__name__}")
    expected = {"remove_always", "remove_by_type"}
    unknown = set(raw) - expected
    if unknown:
        raise ValueError(f"invalid format: unknown keys {sorted(unknown)}")
    missing = expected - set(raw)
    if missing:
        raise ValueError(f"invalid format: missing keys {sorted(missing)}")

    always = _validated_name_list(raw["remove_always"], "remove_always")
    by_type_raw = raw["remove_by_type"]
    if not isinstance(by_type_raw, dict):
        raise ValueError("invalid format: remove_by_type must be an object")
    by_type: dict[str, set[str]] = {}
    for type_name, fields in by_type_raw.items():
        if not isinstance(type_name, str) or not type_name:
            raise ValueError("invalid format: remove_by_type keys must be non-empty strings")
        by_type[type_name] = _validated_name_list(fields, f"remove_by_type[{type_name}]")

    overlap = always & {f for fields in by_type.values() for f in fields}
    if overlap:
        raise ValueError(f"invalid format: fields in both rules: {sorted(overlap)}")
    return InvalidFieldsConfig(remove_always=always, remove_by_type=by_type)


def _validated_name_list(value: Any, context: str) -> set[str]:
    """Validate a list of field names, returning it as a set."""
    if not isinstance(value, list):
        raise ValueError(f"invalid format: {context} must be a list")
    for entry in value:
        if not isinstance(entry, str) or not entry:
            raise ValueError(f"invalid format: {context} entries must be non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"invalid format: {context} contains duplicates")
    return set(value)


def remove_invalid_fields(obj: Any, config: InvalidFieldsConfig, _depth: int = 0) -> Any:
    """Recursively remove invalid fields from a JSON object.

    ``remove_always`` names are deleted wherever they appear.  ``remove_by_type``
    names are deleted only from dicts whose ``type`` string is listed for that
    field; otherwise the field is kept and a warning is emitted.
    """
    if depth_exceeded(_depth, "remove_invalid_fields"):
        return obj
    if isinstance(obj, dict):
        keys_to_remove = [k for k in obj if k in config.remove_always]
        for k in keys_to_remove:
            del obj[k]
        _remove_by_type_fields(obj, config)
        for v in obj.values():
            remove_invalid_fields(v, config, _depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            remove_invalid_fields(item, config, _depth + 1)
    return obj


def _remove_by_type_fields(obj: dict[str, Any], config: InvalidFieldsConfig) -> None:
    """Apply the type-gated rule to a single dict in place."""
    if not config.remove_by_type:
        return
    gated = {f for fields in config.remove_by_type.values() for f in fields}
    present = gated & set(obj)
    if not present:
        return
    obj_type = obj.get("type")
    for name in sorted(present):
        allowed = isinstance(obj_type, str) and name in config.remove_by_type.get(obj_type, set())
        if allowed:
            del obj[name]
        else:
            print(
                f"Warning: keeping field {name!r} "
                f"(type {obj_type!r} is not listed for removal)",
                file=sys.stderr,
            )


def make_processor(config: InvalidFieldsConfig) -> Callable[[Any, Path], Any | None]:
    def processor(data: Any, _path: Path) -> Any | None:
        original = snapshot(data)
        if isinstance(data, list):
            for item in data:
                remove_invalid_fields(item, config)
        elif isinstance(data, dict):
            remove_invalid_fields(data, config)
        else:
            return None
        # No-op files return None so process_directory skips save+backup
        # (prevents ~ generation growth on repeated runs).
        if is_unchanged(original, data):
            return None
        return data

    return processor


def main() -> int:
    # Config is loaded in the setup hook (after parse_args) so --help
    # works even when the rules file is missing. The dispatch processor
    # delegates to the setup-built processor stored in state.
    state: dict[str, Callable[[Any, Path], Any | None]] = {}

    def _setup(_args: argparse.Namespace) -> int | None:
        if not INVALID_FIELDS_PATH.exists():
            print(f"Invalid fields list not found: {INVALID_FIELDS_PATH}", file=sys.stderr)
            return 1

        try:
            config = load_invalid_fields()
        except (OSError, ValueError) as e:
            # Note: json.JSONDecodeError subclasses ValueError, so malformed JSON
            # is covered here as well.
            print(f"Invalid fields list error: {e}", file=sys.stderr)
            return 1
        state["processor"] = make_processor(config)
        return None

    def _processor(data: Any, path: Path) -> Any | None:
        return state["processor"](data, path)

    return run_standard_pipeline(
        "Remove invalid JSON fields from CDDA mod files",
        _processor,
        setup=_setup,
    )


if __name__ == "__main__":
    sys.exit(main())
