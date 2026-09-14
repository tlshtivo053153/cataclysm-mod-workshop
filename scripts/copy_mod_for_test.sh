#!/bin/bash
# copy_mod_for_test.sh — Copy a mod into external/cdda/mods/ for testing
#
# Deprecated: use `bash scripts/place_mod_for_test.sh --copy <mod_dir>` instead.

exec "$(dirname "${BASH_SOURCE[0]}")/place_mod_for_test.sh" --copy "$@"
