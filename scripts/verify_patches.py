#!/usr/bin/env python3
"""Verify patch set structural integrity.

Checks:
  - README.md exists and lists all .patch files
  - All listed .patch files exist
  - Application order is numbered sequentially
  - Baseline is documented
"""

import re
import sys
from pathlib import Path

PATCH_NUM_RE = re.compile(r"^\d+[._]")


def check_patch_set(patch_dir: Path) -> list[str]:
    errors: list[str] = []
    readme = patch_dir / "README.md"

    if not readme.exists():
        errors.append(f"Missing README.md in {patch_dir}")
        return errors

    readme_text = readme.read_text(encoding="utf-8")

    if "## 適用順序" not in readme_text and "## Application Order" not in readme_text:
        errors.append(f"{readme}: No application order section found")

    if "ベースライン" not in readme_text and "Baseline" not in readme_text:
        errors.append(f"{readme}: No baseline documented")

    patch_files = sorted(p for p in patch_dir.glob("*.patch"))
    if not patch_files:
        errors.append(f"{patch_dir}: No .patch files found")
        return errors

    expected_numbers = list(range(1, len(patch_files) + 1))
    for pf, expected in zip(patch_files, expected_numbers, strict=True):
        match = PATCH_NUM_RE.match(pf.name)
        if not match:
            errors.append(f"{pf.name}: Filename does not start with a number")
            continue
        num = int(match.group().rstrip("._"))
        if num != expected:
            errors.append(
                f"{pf.name}: Expected patch number {expected}, got {num}. "
                f"Check order: {[p.name for p in patch_files]}"
            )
            break

    listed_names = set()
    for line in readme_text.splitlines():
        m = re.search(r"(\d+[_\w-]*\.patch)", line)
        if m:
            listed_names.add(m.group(1))

    actual_names = {p.name for p in patch_files}
    if listed_names != actual_names:
        missing_in_readme = actual_names - listed_names
        missing_on_disk = listed_names - actual_names
        if missing_in_readme:
            errors.append(f"Patch files not listed in README: {missing_in_readme}")
        if missing_on_disk:
            errors.append(f"Patch files listed in README but missing: {missing_on_disk}")

    return errors


def main() -> int:
    patches_root = Path("patches")
    if not patches_root.exists():
        print("patches/ directory not found", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for patch_set in sorted(patches_root.iterdir()):
        if patch_set.is_dir() and not patch_set.name.startswith("."):
            errors = check_patch_set(patch_set)
            if errors:
                all_errors.extend(errors)
                print(f"\n{patch_set.name}:")
                for e in errors:
                    print(f"  ERROR: {e}", file=sys.stderr)
            else:
                patch_count = len(list(patch_set.glob("*.patch")))
                print(f"{patch_set.name}: OK ({patch_count} patches)")

    if all_errors:
        print(f"\n{len(all_errors)} error(s) found", file=sys.stderr)
        return 1

    print("\nAll patch sets valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
