#!/usr/bin/env bash
# validate.sh — mod内の全JSONファイルの構文チェック
set -euo pipefail

MOD_DIR="${1:-.}"
ERRORS=0

echo "=== JSON Validation: $MOD_DIR ==="

FILES=()
while IFS= read -r file; do
  FILES+=("$file")
done < <(find -H "$MOD_DIR" -type d -name .bak -prune -o -name "*.json" -print 2>/dev/null || true)
# NOTE (E-6): .bak exclusion is unified with common._is_backup_path
# (scripts/common.py): only paths with a `.bak` component relative to the
# base dir are skipped; ancestors of the base named `.bak` never exclude
# the base itself. `find ... -name .bak -prune` is the shell equivalent.

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "  ERROR: No JSON files found in $MOD_DIR" >&2
  exit 1
fi

# NOTE: パイプ経由の while read はサブシェルで実行されるため ERRORS が
# 親シェルに伝播しない。プロセス置換 < <(...) を使って同一シェルで実行する。
for file in "${FILES[@]}"; do
  if python3 -m json.tool "$file" > /dev/null 2>&1; then
    echo "  OK: $file"
  else
    echo "  NG: $file" >&2
    python3 -m json.tool "$file" 2>&1 | head -10 >&2 || true
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -eq 0 ]; then
  echo "=== All files passed ==="
else
  echo "=== $ERRORS file(s) failed ===" >&2
  exit 1
fi
