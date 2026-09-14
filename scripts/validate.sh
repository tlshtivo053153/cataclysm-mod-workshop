#!/bin/bash
# validate.sh — mod内の全JSONファイルの構文チェック
set -euo pipefail

MOD_DIR="${1:-.}"
ERRORS=0

echo "=== JSON Validation: $MOD_DIR ==="

FILES=()
while IFS= read -r file; do
  FILES+=("$file")
done < <(find -H "$MOD_DIR" -type d -name .bak -prune -o -name "*.json" -print 2>/dev/null || true)

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "  ERROR: No JSON files found in $MOD_DIR"
  exit 1
fi

# NOTE: パイプ経由の while read はサブシェルで実行されるため ERRORS が
# 親シェルに伝播しない。プロセス置換 < <(...) を使って同一シェルで実行する。
for file in "${FILES[@]}"; do
  if python3 -m json.tool "$file" > /dev/null 2>&1; then
    echo "  OK: $file"
  else
    echo "  NG: $file"
    python3 -m json.tool "$file" 2>&1 | head -10 || true
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -eq 0 ]; then
  echo "=== All files passed ==="
else
  echo "=== $ERRORS file(s) failed ==="
  exit 1
fi
