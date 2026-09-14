#!/usr/bin/env bash
# copy_mod_for_test.sh — Copy a mod into external/cdda/mods/ for testing
#
# DEPRECATED: use `bash scripts/place_mod_for_test.sh --copy <mod_dir>` instead.
# Removal: scheduled on 2026-12-31 (see rules/verification.md "非推奨の旧ラッパー").
# This wrapper will be deleted then; new usage is not recommended.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Warning: copy_mod_for_test.sh is deprecated; use 'bash scripts/place_mod_for_test.sh --copy <mod_dir>' instead. Removal on 2026-12-31." >&2
exec "$SCRIPT_DIR/place_mod_for_test.sh" --copy "$@"
