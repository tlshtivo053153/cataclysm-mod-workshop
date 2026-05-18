#!/bin/bash
# copy_mod_for_test.sh — Copy a mod into external/cdda/mods/ for testing
#
# Usage:
#   bash scripts/copy_mod_for_test.sh mods/Magiclysm_with_Random_Dungeons-0I
#
# The mod name in external/cdda/mods/ will match the basename of the source directory.

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

cp -r "$SRC_DIR" "$DEST_DIR"
echo "Copied: $SRC_DIR -> $DEST_DIR"
