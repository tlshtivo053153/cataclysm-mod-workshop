#!/usr/bin/env python3
"""CI-level mod validation: enumerate mods, validate JSON syntax, check modinfo, detect duplicate IDs."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import _is_backup_path

REQUIRED_MODINFO_FIELDS = {"type", "id", "name"}


def find_mod_dirs(base_dir: Path) -> list[Path]:
    """Find mod directories containing a modinfo.json file (recursive).

    `.bak` directories under base_dir are excluded so post-conversion
    backups are not detected as separate mods (Duplicate mod ID guard).
    Only the path relative to base_dir is inspected (see
    common._is_backup_path).
    """

    mod_dirs = sorted(
        {
            modinfo.parent
            for modinfo in base_dir.rglob("modinfo.json")
            if not _is_backup_path(base_dir, modinfo)
        },
        key=str,
    )
    return mod_dirs


def collect_mod_ids(mod_dirs: list[Path]) -> tuple[dict[str, list[Path]], list[Path]]:
    """Extract mod IDs from modinfo.json, grouping directories by ID.

    Returns (id_map, error_dirs).  error_dirs are directories whose modinfo.json
    could not be parsed or was missing required fields.
    """
    id_map: dict[str, list[Path]] = {}
    error_dirs: list[Path] = []

    for mod_dir in mod_dirs:
        modinfo_path = mod_dir / "modinfo.json"
        try:
            with open(modinfo_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"ERROR: Cannot parse modinfo.json in {mod_dir}: {e}", file=sys.stderr)
            error_dirs.append(mod_dir)
            continue

        if isinstance(data, list) and len(data) > 0:
            entry = data[0]
        elif isinstance(data, dict):
            entry = data
        else:
            print(f"ERROR: Unexpected modinfo.json format in {mod_dir}", file=sys.stderr)
            error_dirs.append(mod_dir)
            continue

        if not isinstance(entry, dict):
            print(f"ERROR: Unexpected modinfo.json format in {mod_dir}", file=sys.stderr)
            error_dirs.append(mod_dir)
            continue

        missing = REQUIRED_MODINFO_FIELDS - set(entry.keys())
        if missing:
            print(f"ERROR: {mod_dir}/modinfo.json missing fields: {missing}", file=sys.stderr)
            error_dirs.append(mod_dir)
            continue

        if entry.get("type") != "MOD_INFO":
            print(
                f"ERROR: {mod_dir}/modinfo.json has type={entry.get('type')!r}, expected MOD_INFO",
                file=sys.stderr,
            )
            error_dirs.append(mod_dir)
            continue

        mod_id = entry["id"]
        if not isinstance(mod_id, str) or not mod_id:
            print(
                f"ERROR: {mod_dir}/modinfo.json has invalid id: {mod_id!r}",
                file=sys.stderr,
            )
            error_dirs.append(mod_dir)
            continue
        id_map.setdefault(mod_id, []).append(mod_dir)

    return id_map, error_dirs


def run_validate(mod_dir: Path) -> bool:
    """Run validate.sh on a mod directory. Returns True on success."""
    script = Path(__file__).resolve().parent / "validate.sh"
    result = subprocess.run(
        ["bash", str(script), str(mod_dir)],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all mods in a base directory")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Base directory to scan for mods recursively (default: mods relative to project root)",
    )
    args = parser.parse_args()

    if args.base_dir is not None:
        base = args.base_dir
    else:
        project_root = Path(__file__).resolve().parent.parent
        base = project_root / "mods"

    if not base.exists():
        print(f"ERROR: mod base directory not found: {base}", file=sys.stderr)
        return 1

    mod_dirs = find_mod_dirs(base)
    if not mod_dirs:
        print("ERROR: No mod directories found (missing modinfo.json)", file=sys.stderr)
        return 1

    print(f"Found {len(mod_dirs)} mod(s) in {base}")

    id_map, error_dirs = collect_mod_ids(mod_dirs)

    errors = len(error_dirs)

    for mod_id, dirs in id_map.items():
        if len(dirs) > 1:
            print(
                f"ERROR: Duplicate mod ID '{mod_id}' in: {', '.join(str(d) for d in dirs)}",
                file=sys.stderr,
            )
            errors += 1

    for mod_dir in mod_dirs:
        print(f"\n--- Validating {mod_dir} ---")
        if not run_validate(mod_dir):
            errors += 1

    if errors > 0:
        print(f"\nERROR: {errors} validation failure(s) detected", file=sys.stderr)
        return 1

    print(f"\nAll {len(mod_dirs)} mod(s) passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
