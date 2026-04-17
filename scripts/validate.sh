#!/bin/bash
# validate.sh — mod内の全JSONファイルの構文チェック

MOD_DIR="${1:-.}"
ERRORS=0

echo "=== JSON Validation: $MOD_DIR ==="

# NOTE: パイプ経由の while read はサブシェルで実行されるため ERRORS が
# 親シェルに伝播しない。プロセス置換 < <(...) を使って同一シェルで実行する。
while read -r file; do
  if python3 -m json.tool "$file" > /dev/null 2>&1; then
    echo "  OK: $file"
  else
    echo "  NG: $file"
    python3 -m json.tool "$file" 2>&1 | head -5
    ERRORS=$((ERRORS + 1))
  fi
done < <(find "$MOD_DIR" -name "*.json")

if [ "$ERRORS" -eq 0 ]; then
  echo "=== All files passed ==="
else
  echo "=== $ERRORS file(s) failed ==="
  exit 1
fi