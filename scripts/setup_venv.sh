#!/usr/bin/env bash
set -euo pipefail
# Local CI reproduction entrypoint (E-7):
# - Python deps come from requirements-dev.txt (single source of truth, same
#   file CI installs; keeps PyYAML capitalization/pins in one place).
# - shellcheck is not a pip package; see the hint at the end for shell-job parity.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

echo "Setting up Python virtual environment for CDDA Mod Framework..."

if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo "Created virtual environment at ${VENV_DIR}"
else
    echo "Virtual environment already exists at ${VENV_DIR}"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip
# E-7: install pinned dev deps (was unpinned ad-hoc list).
pip install -r "${PROJECT_ROOT}/requirements-dev.txt"

# CI shell-job parity: local install hint only, no auto-install.
if ! command -v shellcheck >/dev/null 2>&1; then
    echo "shellcheck not found (CI shell job needs it). Install via:"
    echo "  sudo apt-get install -y shellcheck  # Debian/Ubuntu"
    echo "  brew install shellcheck              # macOS"
else
    shellcheck --version
fi

echo ""
echo "Setup complete. To activate the environment, run:"
echo "  source ${VENV_DIR}/bin/activate"
