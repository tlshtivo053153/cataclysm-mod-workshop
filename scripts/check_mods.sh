#!/usr/bin/env bash
# check_mods.sh — CDDAの組み込みモードチェック機能でMODを検証する
#
# Usage:
#   bash scripts/check_mods.sh <mod_id>

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <mod_id>"
    exit 1
fi

MOD_ID="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CDDA_DIR="${PROJECT_ROOT}/external/cdda"

if [ ! -d "${CDDA_DIR}" ]; then
    echo "Error: CDDA directory not found: ${CDDA_DIR}"
    exit 1
fi

if [ ! -f "${CDDA_DIR}/cataclysm-tiles" ]; then
    echo "Error: cataclysm-tiles binary not found: ${CDDA_DIR}/cataclysm-tiles"
    exit 1
fi

# debug.log をクリア
mkdir -p "${CDDA_DIR}/config"
: > "${CDDA_DIR}/config/debug.log"

echo "Running mod check for: ${MOD_ID}"
cd "${CDDA_DIR}"
EXIT_CODE=0
timeout 30 ./cataclysm-tiles --check-mods "${MOD_ID}" 2>&1 || EXIT_CODE=$?

if [ "${EXIT_CODE}" -eq 124 ]; then
    echo "Error: Mod check timed out after 30 seconds" >&2
fi

exit "${EXIT_CODE}" 