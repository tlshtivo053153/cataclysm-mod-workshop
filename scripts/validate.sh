#!/usr/bin/env bash
# validate.sh — mod内の全JSONファイルの構文チェック
set -euo pipefail

MOD_DIR="${1:-.}"
ERRORS=0

if ! command -v python3 >/dev/null 2>&1; then
  echo "  ERROR: python3 not found (required for JSON validation)" >&2
  exit 1
fi

if [ ! -e "$MOD_DIR" ]; then
  echo "  ERROR: path not found: $MOD_DIR" >&2
  exit 1
fi

echo "=== JSON Validation: $MOD_DIR ==="

FILES=()
while IFS= read -r file; do
  FILES+=("$file")
done < <(find -H "$MOD_DIR" -type d \( -name .bak -o -name '*~' \) -prune -o -name "*.json" -print 2>/dev/null)
# NOTE (E-6): backup exclusion is unified with common._is_backup_path
# (scripts/common.py): paths with a `.bak` component or trailing `~`
# (`data.json~`, `data.json~1`, `mydir~`) relative to the base dir are
# skipped; ancestors of the base named `.bak` never exclude the base
# itself. `find ... -prune` is the shell equivalent. `*.json~*` never
# matches `-name "*.json"` anyway; the prune keeps `mydir~/a.json`
# from being found via a backup directory.

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "  ERROR: No JSON files found in $MOD_DIR" >&2
  exit 1
fi

# Single Python process validates all files (was: one `python3 -m json.tool`
# per file). Output format (`OK:`/`NG:`/`All files passed`) is unchanged.
# shortcut: error count rides on the exit code (caps at 255), upgrade to a
# count file when a single mod routinely reports 255+ bad JSONs.
python3 - "${FILES[@]}" <<'PY'
import json
import sys

errors = 0
for path in sys.argv[1:]:
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
        print(f"  OK: {path}")
    except Exception as e:
        print(f"  NG: {path}", file=sys.stderr)
        print(str(e)[:1000], file=sys.stderr)
        errors += 1
sys.exit(min(errors, 255))
PY
ERRORS=$?

if [ "$ERRORS" -eq 0 ]; then
  echo "=== All files passed ==="
else
  echo "=== $ERRORS file(s) failed ===" >&2
  exit 1
fi
