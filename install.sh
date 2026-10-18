#!/usr/bin/env bash
# PhotoCraft NVIDIA DDS Exporter - macOS Quick Installer
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

echo "==================================================="
echo " PhotoCraft DDS Exporter Installer for macOS"
echo "==================================================="
echo ""

# Check python3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not found in PATH."
    echo "Please install Python 3 using Homebrew ('brew install python3') or from https://www.python.org/"
    exit 1
fi

python3 installer/install_mac.py
