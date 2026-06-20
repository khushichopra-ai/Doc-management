#!/usr/bin/env bash
# Controlled dependency install for AKA backend.
# Installs CPU-only torch first to avoid the multi-GB CUDA wheels, then the
# rest of requirements.txt (torch already satisfied -> no CUDA pull).
set -eo pipefail
cd /home/user/FileManagement/backend

echo "[install] torch (CPU-only) ..."
pip install --no-input "torch>=2.0,<3.0" \
    --index-url https://download.pytorch.org/whl/cpu

echo "[install] remaining requirements ..."
pip install --no-input -r requirements.txt

echo "INSTALL_DONE_OK"
