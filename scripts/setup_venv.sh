#!/usr/bin/env bash
set -euo pipefail

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
pip install black ruff pytest mypy types-PyYAML

echo ""
echo "Setup complete. To activate the environment, run:"
echo "  source ${VENV_DIR}/bin/activate"
