#!/bin/bash
# link_mod_for_test.sh — Create a symlink in external/cdda/mods/ for testing
#
# Usage:
#   bash scripts/link_mod_for_test.sh mods/Magiclysm_with_Random_Dungeons-0I
#
# The symlink name in external/cdda/mods/ will match the basename of the source directory.

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-mod-directory>"
    exit 1
fi

SRC_DIR="$1"
MOD_NAME="$(basename "$SRC_DIR")"
DEST_DIR="external/cdda/mods/$MOD_NAME"

if [ ! -d "$SRC_DIR" ]; then
    echo "Error: Source directory does not exist: $SRC_DIR"
    exit 1
fi

if [ -L "$DEST_DIR" ]; then
    echo "Removing existing symlink: $DEST_DIR"
    rm "$DEST_DIR"
elif [ -d "$DEST_DIR" ]; then
    echo "Removing existing directory: $DEST_DIR"
    rm -rf "$DEST_DIR"
fi

ln -s "$(realpath "$SRC_DIR")" "$DEST_DIR"
echo "Linked: $DEST_DIR -> $(realpath "$SRC_DIR")"
