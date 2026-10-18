#!/usr/bin/env bash
# PhotoCraft NVIDIA DDS Exporter - macOS Uninstaller
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

python3 installer/uninstall_mac.py
