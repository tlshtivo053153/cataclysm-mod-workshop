#!/bin/bash
# link_mod_for_test.sh — Create a symlink in external/cdda/mods/ for testing
#
# Deprecated: use `bash scripts/place_mod_for_test.sh --link <mod_dir>` instead.

exec "$(dirname "${BASH_SOURCE[0]}")/place_mod_for_test.sh" --link "$@"
