#!/usr/bin/env bash
# check_mods.sh — CDDAの組み込みモードチェック機能でMODを検証する
#
# Usage:
#   bash scripts/check_mods.sh <mod_id>                    (use shared config)
#   bash scripts/check_mods.sh --isolated <mod_id>         (use temp workdir)
#   bash scripts/check_mods.sh --check-errors <mod_id>     (also check debug.log for ERROR)
#   bash scripts/check_mods.sh --help                      (show this help)
#
# NOTE (C-2): Level2 is intentionally NOT run in CI (external/cdda/ is
# gitignored, cataclysm-tiles binary absent). Run manually after
# place_mod_for_test.sh; see rules/verification.md "Level2自動".
#
# Exit codes:
#   0 - mod check passed (and debug.log has no ERROR when --check-errors is used)
#   1 - usage error / missing prerequisites
#   2 - mod check failed (CDDA returned non-zero)
#   3 - timeout
#   4 - debug.log contains ERROR (only with --check-errors)

set -euo pipefail

ISOLATED=false
CHECK_ERRORS=false
TIMEOUT_SEC=90
CLEANUP_DIRS=()

show_help() {
    cat <<'EOF'
Usage: check_mods.sh [--isolated] [--check-errors] [--timeout N] <mod_id>
       check_mods.sh --help | -h

Level2: verify a mod with CDDA's built-in --check-mods engine check.

Options:
  --isolated      use a temp workdir (avoid shared-state pollution)
  --check-errors  also fail (exit 4) when debug.log contains ERROR lines
  --timeout N     timeout in seconds, 1-3600 (default: 90)
  --help, -h      show this help and exit 0

CI note: Level2 is intentionally NOT run in CI (external/cdda/ is
gitignored, cataclysm-tiles binary absent on runners).

Manual procedure (see rules/verification.md "Level2自動"):
  bash scripts/place_mod_for_test.sh --link mods/small/<mod_dir>/
  bash scripts/check_mods.sh --isolated <mod_id>

Exit codes:
  0 - passed | 1 - usage/prerequisites | 2 - check failed
  3 - timeout | 4 - debug.log ERROR (with --check-errors)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) show_help; exit 0 ;;
        --isolated) ISOLATED=true; shift ;;
        --check-errors) CHECK_ERRORS=true; shift ;;
        --timeout)
            if [ "$#" -lt 2 ]; then
                echo "Error: --timeout requires a value (seconds)" >&2
                echo "Usage: $0 [--isolated] [--check-errors] [--timeout N] <mod_id>" >&2
                exit 1
            fi
            TIMEOUT_SEC="$2"; shift 2 ;;
        *) break ;;
    esac
done

case "${TIMEOUT_SEC}" in
    ""|*[!0-9]*)
        echo "Error: --timeout must be a positive integer (got '${TIMEOUT_SEC}')" >&2
        exit 1 ;;
esac
# Canonicalize: strip leading zeros (sed is coreutils, always present with timeout).
# This accepts 01/007 as 1/7, rejects 0/00 as 0, and avoids octal confusion.
TIMEOUT_CANON="$(printf '%s' "${TIMEOUT_SEC}" | sed 's/^0*//')"
if [ -z "${TIMEOUT_CANON}" ]; then
    TIMEOUT_CANON="0"
fi
# Digit-length guard before arithmetic (prevents long-overflow bypass like
# 9999999999999999999999 slipping past -gt 3600 in [ ]).
if [ "${#TIMEOUT_CANON}" -gt 4 ]; then
    echo "Error: --timeout must be between 1 and 3600 (got '${TIMEOUT_SEC}')" >&2
    exit 1
fi
if [ "${TIMEOUT_CANON}" -lt 1 ] || [ "${TIMEOUT_CANON}" -gt 3600 ]; then
    echo "Error: --timeout must be between 1 and 3600 (got '${TIMEOUT_SEC}')" >&2
    exit 1
fi
TIMEOUT_SEC="${TIMEOUT_CANON}"

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [--isolated] [--check-errors] [--timeout N] <mod_id>"
    exit 1
fi

MOD_ID="$1"

# Sanitize MOD_ID before any filesystem use (logs, grep, CDDA args).
# Dots are allowed for third-party IDs (e.g. PSY_magi_spells_0.G); '..',
# slashes, backslashes, leading -/. (option/hidden-file injection) are rejected.
case "${MOD_ID}" in
    ""|-*|.*|*/*|*\\*|*..*)
        echo "Error: invalid mod_id: '${MOD_ID}'" >&2
        exit 1 ;;
esac
case "${MOD_ID}" in
    *[!A-Za-z0-9_.-]*)
        echo "Error: invalid mod_id (allowed: [A-Za-z0-9_.-]): '${MOD_ID}'" >&2
        exit 1 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CDDA_DIR="${PROJECT_ROOT}/external/cdda"

# --- Prerequisites -----------------------------------------------------------

if [ ! -d "${CDDA_DIR}" ]; then
    echo "Error: CDDA directory not found: ${CDDA_DIR}"
    exit 1
fi

if [ ! -f "${CDDA_DIR}/cataclysm-tiles" ]; then
    echo "Error: cataclysm-tiles binary not found: ${CDDA_DIR}/cataclysm-tiles"
    exit 1
fi

if ! command -v timeout >/dev/null 2>&1; then
    echo "Error: 'timeout' command not found (coreutils required)" >&2
    exit 1
fi

# --- CDDA version check ------------------------------------------------------
# CDDA 0.I RC is the target.  Log version if the binary supports --version.
if CDDA_VER="$(timeout 10 "${CDDA_DIR}/cataclysm-tiles" --version 2>&1)"; then
    echo "CDDA version: ${CDDA_VER}"
else
    echo "Note: cataclysm-tiles does not support --version; version unknown"
fi

# --- Mod presence check ------------------------------------------------------
# CDDA --check-mods は指定IDのmodが見つからない場合もベースゲーム全体を
# チェックし、無関係な既存エラーで失敗するため、事前に配置を検証する。
if [ ! -d "${CDDA_DIR}/mods" ]; then
    echo "Error: mods directory not found: ${CDDA_DIR}/mods (place the mod first with place_mod_for_test.sh)" >&2
    exit 1
fi

# Exact ID match via python (avoids substring false positives from
# dependencies/descriptions that a plain grep -F "\"ID\"" would hit).
# Falls back to grep -F only when python3 is unavailable.
MOD_FOUND=false
if command -v python3 >/dev/null 2>&1; then
    if MOD_ID="${MOD_ID}" MODS_DIR="${CDDA_DIR}/mods" python3 -c '
import json, os, sys
wanted = os.environ["MOD_ID"]
base = os.environ["MODS_DIR"]
found = False
try:
    names = os.listdir(base)
except OSError:
    sys.exit(1)
for name in names:
    p = os.path.join(base, name, "modinfo.json")
    if not os.path.isfile(p):
        continue
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        continue
    entries = data if isinstance(data, list) else [data]
    for e in entries:
        if isinstance(e, dict) and e.get("id") == wanted:
            found = True
            break
    if found:
        break
sys.exit(0 if found else 1)
'; then
        MOD_FOUND=true
    fi
elif grep -rqF -- "\"${MOD_ID}\"" "${CDDA_DIR}"/mods/*/modinfo.json 2>/dev/null; then
    MOD_FOUND=true
fi
if [ "${MOD_FOUND}" != true ]; then
    echo "Error: mod ID '${MOD_ID}' not found in ${CDDA_DIR}/mods/" >&2
    echo "Hint: run 'bash scripts/place_mod_for_test.sh <mod_dir>' first" >&2
    echo "Hint: the mod_id is the 'id' value in modinfo.json, not the directory name" >&2
    exit 1
fi

# --- Work directory setup ----------------------------------------------------

if [ "${ISOLATED}" = true ]; then
    WORKDIR="$(mktemp -d -t cdda-check-XXXXXX)"
    echo "Isolated workdir: ${WORKDIR}"

    # Copy config skeleton (empty config to avoid shared state pollution)
    mkdir -p "${WORKDIR}/config"
    mkdir -p "${WORKDIR}/save"
    mkdir -p "${WORKDIR}/memorial"
    mkdir -p "${WORKDIR}/graveyard"

    # Symlink mods so the target mod is discoverable
    if [ -d "${CDDA_DIR}/mods" ]; then
        ln -s "$(realpath "${CDDA_DIR}/mods")" "${WORKDIR}/mods"
    fi
    if [ -d "${CDDA_DIR}/data" ]; then
        ln -s "$(realpath "${CDDA_DIR}/data")" "${WORKDIR}/data"
    fi
    if [ -d "${CDDA_DIR}/gfx" ]; then
        ln -s "$(realpath "${CDDA_DIR}/gfx")" "${WORKDIR}/gfx"
    fi

    # Override: use our own config dir
    CONFIG_OVERRIDE=("--userdir" "${WORKDIR}")
    DEBUG_LOG="${WORKDIR}/config/debug.log"
    CLEANUP_DIRS=("${WORKDIR}")
else
    # Shared mode: clear shared state (original behavior)
    mkdir -p "${CDDA_DIR}/config"
    : > "${CDDA_DIR}/config/debug.log"
    # config/flexcache is the legacy cache path; 0.I also caches mod JSON
    # flexbuffers under <userdir>/cache/mods, which must be cleared or
    # edited mod files trigger "Stale game data detected".
    rm -rf "${CDDA_DIR}/config/flexcache" "${CDDA_DIR}/cache/mods"

    CONFIG_OVERRIDE=()
    DEBUG_LOG="${CDDA_DIR}/config/debug.log"
fi

# shellcheck disable=SC2329  # invoked indirectly via trap ... EXIT
cleanup() {
    if [ "${#CLEANUP_DIRS[@]}" -gt 0 ]; then
        if [ -f "${DEBUG_LOG}" ] && [ -s "${DEBUG_LOG}" ]; then
            DEST_LOG="${PROJECT_ROOT}/logs/check_${MOD_ID}_$(date +%Y%m%d_%H%M%S).log"
            mkdir -p "$(dirname "${DEST_LOG}")"
            cp "${DEBUG_LOG}" "${DEST_LOG}"
            echo "Saved debug log: ${DEST_LOG}"
        fi
        rm -rf "${CLEANUP_DIRS[@]}"
    fi
}
trap cleanup EXIT

# --- Run mod check -----------------------------------------------------------

echo "Running mod check for: ${MOD_ID}"
EXIT_CODE=0
(
    cd "${CDDA_DIR}"
    timeout "${TIMEOUT_SEC}" ./cataclysm-tiles \
        "${CONFIG_OVERRIDE[@]}" \
        --check-mods "${MOD_ID}" 2>&1
) || EXIT_CODE=$?

# --- Result handling ---------------------------------------------------------

if [ "${EXIT_CODE}" -eq 124 ]; then
    echo "Error: Mod check timed out after ${TIMEOUT_SEC} seconds" >&2
    exit 3
fi

if [ "${EXIT_CODE}" -ne 0 ]; then
    echo "Error: CDDA mod check failed (exit code ${EXIT_CODE})" >&2
    if [ -f "${DEBUG_LOG}" ]; then
        echo "--- debug.log (last 20 lines) ---" >&2
        tail -20 "${DEBUG_LOG}" >&2
        echo "--- end debug.log ---" >&2
    fi
    exit 2
fi

# --- debug.log ERROR check (optional) ----------------------------------------

if [ "${CHECK_ERRORS}" = true ]; then
    if [ ! -f "${DEBUG_LOG}" ]; then
        echo "Warning: --check-errors requested but debug.log not found: ${DEBUG_LOG}" >&2
        echo "Warning: skipping ERROR check" >&2
    else
        ERROR_COUNT=$(grep -cw "ERROR" "${DEBUG_LOG}" 2>/dev/null || true)
        ERROR_COUNT=${ERROR_COUNT:-0}
        if [ "${ERROR_COUNT}" -gt 0 ]; then
            echo "Error: debug.log contains ${ERROR_COUNT} ERROR line(s)" >&2
            echo "--- ERROR lines ---" >&2
            grep -w "ERROR" "${DEBUG_LOG}" >&2
            echo "--- end ERROR lines ---" >&2
            exit 4
        fi
        echo "debug.log: no ERROR lines found"
    fi
fi

echo "Mod check passed: ${MOD_ID}"
exit 0
