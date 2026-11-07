#!/usr/bin/env python3
"""CI-level mod validation: enumerate mods, validate JSON syntax, check modinfo, detect duplicate IDs."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from common import _is_backup_path

REQUIRED_MODINFO_FIELDS = {"type", "id", "name"}


def find_mod_dirs(base_dir: Path) -> list[Path]:
    """Find mod directories containing a modinfo.json file (recursive).

    Backup paths (legacy `.bak` dirs and trailing-`~` names) under base_dir
    are excluded so post-conversion backups are not detected as separate
    mods (Duplicate mod ID guard). Only the path relative to base_dir is
    inspected (see common._is_backup_path).
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


def find_orphan_data_dirs(base_dir: Path) -> list[Path]:
    """Return category children with data/ but no modinfo.json.

    Scans mods/{small,medium,large,seen,unseen} direct children only.
    """
    orphans: list[Path] = []
    for category in ("small", "medium", "large", "seen", "unseen"):
        cat_dir = base_dir / category
        if not cat_dir.is_dir():
            continue
        for child in sorted(cat_dir.iterdir()):
            if not child.is_dir() or child.is_symlink():
                continue
            if (child / "data").is_dir() and not (child / "modinfo.json").is_file():
                orphans.append(child)
    return orphans


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


def run_validate(mod_dir: Path, timeout: int = 120, *, quiet: bool = False) -> bool:
    """Run validate.sh on a mod directory. Returns True on success.

    When quiet=True, per-file OK output is suppressed on success to keep
    CI logs small (F-1); output is still shown on failure.
    """
    script = Path(__file__).resolve().parent / "validate.sh"
    try:
        result = subprocess.run(
            ["bash", str(script), str(mod_dir)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        print(f"ERROR: validate.sh not found for {mod_dir}: {e}", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired as e:
        print(f"ERROR: validation timed out for {mod_dir}: {e}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"ERROR: Cannot run validation for {mod_dir}: {e}", file=sys.stderr)
        return False
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return False
    if not quiet:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    else:
        # Quiet success: suppress per-file OK lines; surface unexpected stderr.
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    return True


def _iter_json_objects(mod_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Collect all JSON objects in a mod dir (list or dict top-level).

    Files that fail to parse are skipped here; syntax errors are already
    reported by run_validate/validate.sh. Backup paths are excluded.
    """
    objects: list[tuple[Path, dict[str, Any]]] = []
    for json_file in sorted(mod_dir.rglob("*.json")):
        if _is_backup_path(mod_dir, json_file):
            continue
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if isinstance(entry, dict):
                objects.append((json_file, entry))
    return objects


def check_recipe_activity_level(
    mod_dir: Path, objects: list[tuple[Path, dict[str, Any]]] | None = None
) -> list[str]:
    """Check CORE.md recipe rule: every `type: recipe` needs `activity_level`.

    Returns a list of error messages (empty = pass).
    """
    if objects is None:
        objects = _iter_json_objects(mod_dir)
    errors: list[str] = []
    for json_file, entry in objects:
        if entry.get("type") != "recipe":
            continue
        level = entry.get("activity_level")
        if not isinstance(level, str) or not level:
            result = entry.get("result", "?")
            errors.append(
                f"{json_file}: recipe '{result}' missing required "
                "'activity_level' (rules/CORE.md recipe必須フィールド)"
            )
    return errors


def check_modinfo_dependencies(mod_dir: Path) -> list[str]:
    """Check CORE.md modinfo rule: `dependencies` must include `dda`.

    Returns a list of error messages (empty = pass). Unparseable modinfo
    is skipped here (already reported by collect_mod_ids).
    """
    modinfo_path = mod_dir / "modinfo.json"
    try:
        with open(modinfo_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    entry: Any = data[0] if isinstance(data, list) and data else data
    if not isinstance(entry, dict):
        return []
    deps = entry.get("dependencies")
    if not isinstance(deps, list) or "dda" not in deps:
        return [
            f"{mod_dir}/modinfo.json missing required dependency 'dda' "
            "in 'dependencies' (rules/CORE.md modinfo.json)"
        ]
    return []


def check_copy_from_references(
    mod_dir: Path, objects: list[tuple[Path, dict[str, Any]]] | None = None
) -> list[str]:
    """Check CORE.md copy-from rule: warn when target is not defined in-mod.

    Vanilla IDs (external/cdda) are unavailable in CI, so unknown targets
    are WARNING-level only and never fail validation. Returns warnings.
    """
    if objects is None:
        objects = _iter_json_objects(mod_dir)
    local_ids = {entry["id"] for _, entry in objects if isinstance(entry.get("id"), str)}
    local_ids |= {
        entry["abstract"] for _, entry in objects if isinstance(entry.get("abstract"), str)
    }
    warnings: list[str] = []
    for json_file, entry in objects:
        target = entry.get("copy-from")
        if not isinstance(target, str) or not target:
            continue
        if target not in local_ids:
            warnings.append(
                f"{json_file}: '{entry.get('id', '?')}' copy-from "
                f"'{target}' not defined in mod (verify in external/cdda/data/json/)"
            )
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all mods in a base directory")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Base directory to scan for mods recursively (default: mods relative to project root)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file OK output (F-1: keeps CI logs small; errors still shown)",
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

    orphans = find_orphan_data_dirs(base)
    for orphan in orphans:
        print(f"ERROR: {orphan} has data/ but no modinfo.json", file=sys.stderr)
    orphan_errors = len(orphans)
    if not mod_dirs:
        if orphan_errors:
            return 1
        print("ERROR: No mod directories found (missing modinfo.json)", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Found {len(mod_dirs)} mod(s) in {base}")

    id_map, error_dirs = collect_mod_ids(mod_dirs)

    errors = len(error_dirs) + orphan_errors

    for mod_id, dirs in id_map.items():
        if len(dirs) > 1:
            print(
                f"ERROR: Duplicate mod ID '{mod_id}' in: {', '.join(str(d) for d in dirs)}",
                file=sys.stderr,
            )
            errors += 1

    for mod_dir in mod_dirs:
        if not args.quiet:
            print(f"\n--- Validating {mod_dir} ---")
        if not run_validate(mod_dir, quiet=args.quiet):
            errors += 1
        # C-1: Level1 content rules from rules/CORE.md (beyond JSON syntax).
        objects = _iter_json_objects(mod_dir)
        for msg in check_recipe_activity_level(mod_dir, objects):
            print(f"ERROR: {msg}", file=sys.stderr)
            errors += 1
        for msg in check_modinfo_dependencies(mod_dir):
            print(f"ERROR: {msg}", file=sys.stderr)
            errors += 1
        for msg in check_copy_from_references(mod_dir, objects):
            print(f"WARNING: {msg}", file=sys.stderr)

    if errors > 0:
        print(f"\nERROR: {errors} validation failure(s) detected", file=sys.stderr)
        return 1

    print(f"\nAll {len(mod_dirs)} mod(s) passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
