#!/bin/bash
# place_mod_for_test.sh — Symlink (default) or copy a mod into external/cdda/mods/ for testing
#
# Usage:
#   bash scripts/place_mod_for_test.sh mods/small/my_mod/                    (symlink, default)
#   bash scripts/place_mod_for_test.sh --link mods/small/my_mod/             (symlink, explicit)
#   bash scripts/place_mod_for_test.sh --copy mods/small/my_mod/             (copy)
#   bash scripts/place_mod_for_test.sh --dry-run mods/small/my_mod/          (show plan only)
#   bash scripts/place_mod_for_test.sh --force --copy mods/...               (skip confirmation)
#
# The mod name in external/cdda/mods/ will match the basename of the source directory.
#
# NOTE: realpath -m is GNU-specific and not available on macOS (Linux/CI only).
# NOTE: Edit and convert mods on the repo side (mods/<mod>), not via external/cdda/mods.
#   Running converters via the symlink rewrites repo mods/ directly.
#   Ensure `git status --porcelain -- mods/<mod>` is clean before converting.

set -euo pipefail

LINK_FLAG=false
COPY_FLAG=false
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --link) LINK_FLAG=true; shift ;;
        --copy) COPY_FLAG=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --force) FORCE=true; shift ;;
        --) shift; break ;;
        --*) echo "Error: Unknown option: $1" >&2; echo "Usage: $0 [--link|--copy] [--dry-run] [--force] <path-to-mod-directory>" >&2; exit 1 ;;
        *) break ;;
    esac
done

if [ "$LINK_FLAG" = true ] && [ "$COPY_FLAG" = true ]; then
    echo "Error: --link and --copy are mutually exclusive" >&2
    echo "Usage: $0 [--link|--copy] [--dry-run] [--force] <path-to-mod-directory>" >&2
    exit 1
fi

LINK_MODE=true
if [ "$COPY_FLAG" = true ]; then
    LINK_MODE=false
fi

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [--link|--copy] [--dry-run] [--force] <path-to-mod-directory>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SRC_DIR="$1"
MOD_NAME="$(basename -- "$SRC_DIR")"

# --- Path validation (before any rm) -----------------------------------------
if [ -z "$MOD_NAME" ] || [ "$MOD_NAME" = "." ] || [ "$MOD_NAME" = ".." ] || [ "$MOD_NAME" = "/" ]; then
    echo "Error: invalid mod name derived from source: '$SRC_DIR'" >&2
    exit 1
fi
case "$MOD_NAME" in
    -*) echo "Error: invalid mod name (must not start with '-'): '$MOD_NAME'" >&2; exit 1 ;;
esac

SRC_REAL="$(realpath -m -- "$SRC_DIR")"
if [ ! -d "$SRC_REAL" ]; then
    echo "Error: Source directory does not exist: $SRC_DIR" >&2
    exit 1
fi

CDDA_MODS_DIR="${PROJECT_ROOT}/external/cdda/mods"
CDDA_MODS_REAL="$(realpath -m -- "$CDDA_MODS_DIR")"
DEST_DIR="${PROJECT_ROOT}/external/cdda/mods/${MOD_NAME}"
# NOTE: lexical join (not realpath on DEST_DIR) so an existing DEST symlink
# to SRC does not resolve DEST_REAL back to SRC before the prefix check.
DEST_REAL="${CDDA_MODS_REAL}/${MOD_NAME}"

if [ "$DEST_REAL" = "$CDDA_MODS_REAL" ]; then
    echo "Error: destination must be inside mods directory, got: $DEST_REAL" >&2
    exit 1
fi
case "${DEST_REAL}/" in
    "${CDDA_MODS_REAL}/"*) ;;
    *) echo "Error: destination escapes mods directory: $DEST_REAL" >&2; exit 1 ;;
esac

if [ "$SRC_REAL" = "$DEST_REAL" ]; then
    echo "Error: source and destination are the same: $SRC_REAL" >&2
    exit 1
fi

case "${DEST_REAL}/" in
    "${SRC_REAL}/"*)
        echo "Error: destination is inside source (self-reference): $DEST_REAL ⊂ $SRC_REAL" >&2
        exit 1
        ;;
esac
case "${SRC_REAL}/" in
    "${DEST_REAL}/"*)
        echo "Error: source is inside destination: $SRC_REAL ⊂ $DEST_REAL" >&2
        exit 1
        ;;
esac

# --dry-run wins over --force: never modify, even mkdir.
# NOTE: dry-run is evaluated before the idempotency early-exit so
# `... --dry-run` always prints the plan instead of "Already placed".
if [ "$DRY_RUN" = true ]; then
    if [ "$LINK_MODE" = true ]; then
        MODE="symlink"
    else
        MODE="copy"
    fi
    echo "[dry-run] mode: $MODE"
    echo "[dry-run] source: $SRC_REAL"
    echo "[dry-run] destination: $DEST_REAL"
    if [ -e "$DEST_DIR" ] || [ -L "$DEST_DIR" ]; then
        echo "[dry-run] would remove: $DEST_DIR"
    else
        echo "[dry-run] no existing destination to remove"
    fi
    if [ "$LINK_MODE" = true ]; then
        echo "[dry-run] would link: $DEST_DIR -> $SRC_REAL"
    else
        echo "[dry-run] would copy: $SRC_REAL -> $DEST_DIR"
    fi
    exit 0
fi

# Idempotency: already linked to the same source is success.
if [ -L "$DEST_DIR" ]; then
    EXIST_REAL="$(realpath -m -- "$DEST_DIR")"
    if [ "$EXIST_REAL" = "$SRC_REAL" ]; then
        echo "Already placed: $DEST_DIR -> $SRC_REAL"
        exit 0
    fi
fi

remove_dest() {
    if [ -L "$DEST_DIR" ]; then
        echo "Removing existing symlink: $DEST_DIR"
        rm -- "$DEST_DIR"
    elif [ -d "$DEST_DIR" ]; then
        echo "Removing existing directory: $DEST_DIR"
        rm -rf -- "$DEST_DIR"
    else
        echo "Removing existing file: $DEST_DIR"
        rm -f -- "$DEST_DIR"
    fi
}

confirm_overwrite() {
    if [ "$FORCE" != true ]; then
        if [ -d "$DEST_DIR" ] && [ ! -L "$DEST_DIR" ]; then
            echo "WARNING: This will permanently delete the directory: $DEST_DIR"
        else
            echo "WARNING: This will remove: $DEST_DIR"
        fi
        if [ -t 0 ]; then
            response=""
            read -r -p "Continue? [y/N] " response || true
        else
            echo "Non-interactive mode: use --force to skip confirmation" >&2
            exit 2
        fi
        case "$response" in
            [yY]|[yY][eE][sS]) ;;
            *) echo "Aborted."; exit 0 ;;
        esac
    fi
}

mkdir -p -- "$(dirname -- "$DEST_DIR")"

if [ "$LINK_MODE" = true ]; then
    if [ -e "$DEST_DIR" ] || [ -L "$DEST_DIR" ]; then
        confirm_overwrite
        remove_dest
    fi
    ln -s -- "$SRC_REAL" "$DEST_DIR"
    echo "Linked: $DEST_DIR -> $SRC_REAL"
else
    # Atomic copy: stage into temp dir, verify, then replace.
    # mktemp avoids predictable $$ paths; old DEST is kept until the new
    # tree is verified, and restored if the final mv fails.
    TMP_DEST="$(mktemp -d -- "${DEST_DIR}.tmp.XXXXXX")"
    OLD_DEST=""
    cleanup_tmp() {
        if [ -n "${TMP_DEST:-}" ] && [ -e "$TMP_DEST" ]; then
            rm -rf -- "$TMP_DEST"
        fi
        if [ -n "${OLD_DEST:-}" ] && [ -e "$OLD_DEST" ] && [ ! -e "$DEST_DIR" ]; then
            mv -- "$OLD_DEST" "$DEST_DIR" 2>/dev/null || true
        elif [ -n "${OLD_DEST:-}" ] && [ -e "$OLD_DEST" ]; then
            # mv succeeded but script failed later; keep old tree out of the way
            rm -rf -- "$OLD_DEST" 2>/dev/null || true
        fi
    }
    trap cleanup_tmp EXIT
    cp -a -- "$SRC_REAL/." "$TMP_DEST/"
    # Robust file count (newline-safe): count NUL-separated entries.
    SRC_COUNT="$(find "$SRC_REAL" -type f -print0 | tr -dc '\0' | wc -c)"
    TMP_COUNT="$(find "$TMP_DEST" -type f -print0 | tr -dc '\0' | wc -c)"
    if [ "$SRC_COUNT" != "$TMP_COUNT" ]; then
        echo "Error: copy verification failed (source files: $SRC_COUNT, copied: $TMP_COUNT)" >&2
        exit 1
    fi
    if [ -e "$SRC_REAL/modinfo.json" ] && [ ! -e "$TMP_DEST/modinfo.json" ]; then
        echo "Error: copy verification failed (modinfo.json missing after copy)" >&2
        exit 1
    fi
    if [ -e "$DEST_DIR" ] || [ -L "$DEST_DIR" ]; then
        confirm_overwrite
        # Unique non-existing path for rollback (mktemp -u: name only, no file).
        OLD_DEST="$(mktemp -u -- "${DEST_DIR}.old.XXXXXX")"
        rm -rf -- "$OLD_DEST"
        # Move old aside first so a failed final mv can be rolled back.
        if ! mv -- "$DEST_DIR" "$OLD_DEST"; then
            echo "Error: failed to move existing destination aside" >&2
            exit 1
        fi
        if ! mv -- "$TMP_DEST" "$DEST_DIR"; then
            echo "Error: failed to move staged copy into place; restoring original" >&2
            mv -- "$OLD_DEST" "$DEST_DIR" 2>/dev/null || true
            exit 1
        fi
        rm -rf -- "$OLD_DEST"
        OLD_DEST=""
    else
        if ! mv -- "$TMP_DEST" "$DEST_DIR"; then
            echo "Error: failed to move staged copy into place" >&2
            exit 1
        fi
    fi
    TMP_DEST=""
    trap - EXIT
    echo "Copied: $SRC_DIR -> $DEST_DIR"
fi
