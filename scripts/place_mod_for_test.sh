#!/bin/bash
# place_mod_for_test.sh — Copy or symlink a mod into external/cdda/mods/ for testing
#
# Usage:
#   bash scripts/place_mod_for_test.sh mods/Magiclysm_with_Random_Dungeons-0I         (copy)
#   bash scripts/place_mod_for_test.sh --link mods/Magiclysm_with_Random_Dungeons-0I  (symlink)
#
# The mod name in external/cdda/mods/ will match the basename of the source directory.

set -euo pipefail

LINK_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --link) LINK_MODE=true; shift ;;
        *) break ;;
    esac
done

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [--link] <path-to-mod-directory>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SRC_DIR="$1"
MOD_NAME="$(basename "$SRC_DIR")"
DEST_DIR="${PROJECT_ROOT}/external/cdda/mods/${MOD_NAME}"

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
elif [ -e "$DEST_DIR" ]; then
    echo "Removing existing file: $DEST_DIR"
    rm -f "$DEST_DIR"
fi

mkdir -p "$(dirname "$DEST_DIR")"

if [ "$LINK_MODE" = true ]; then
    ln -s "$(realpath "$SRC_DIR")" "$DEST_DIR"
    echo "Linked: $DEST_DIR -> $(realpath "$SRC_DIR")"
else
    cp -r "$SRC_DIR" "$DEST_DIR"
    echo "Copied: $SRC_DIR -> $DEST_DIR"
fi
