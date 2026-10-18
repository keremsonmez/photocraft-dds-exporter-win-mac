#!/usr/bin/env bash
# PhotoCraft - Automated macOS nvcompress Builder
# Compiles NVIDIA Texture Tools (nvcompress, nvdecompress, nvddsinfo) for Apple Silicon and Intel Macs.
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd )"
OUT_DIR="$REPO_ROOT/bin/nvidia_tools_mac"
APP_SUPPORT_DIR="$HOME/Library/Application Support/Photocraft/nvidia_tools"

mkdir -p "$OUT_DIR"
mkdir -p "$APP_SUPPORT_DIR"

echo "==================================================="
echo " Compiling NVIDIA Texture Tools for macOS"
echo "==================================================="
echo ""

# Check prerequisites
if ! command -v cmake &> /dev/null; then
    echo "[!] CMake not found. Installing via Homebrew if available..."
    if command -v brew &> /dev/null; then
        brew install cmake
    else
        echo "[ERROR] Please install CMake: https://cmake.org/download/ or 'brew install cmake'"
        exit 1
    fi
fi

if ! command -v git &> /dev/null; then
    echo "[ERROR] Git not found. Please install Xcode Command Line Tools: xcode-select --install"
    exit 1
fi

BUILD_TMP="/tmp/nvtt_build_mac"
rm -rf "$BUILD_TMP"
mkdir -p "$BUILD_TMP"

echo "[1/4] Cloning nvidia-texture-tools repository..."
git clone --depth 1 https://github.com/castano/nvidia-texture-tools.git "$BUILD_TMP"

echo "[2/4] Configuring with CMake for macOS..."
cd "$BUILD_TMP"
mkdir -p build && cd build

# Configure CMake with flags suitable for Apple Clang
cmake -DCMAKE_BUILD_TYPE=Release \
      -DNVTT_SHARED=OFF \
      -DCMAKE_CXX_FLAGS="-Wno-error=implicit-function-declaration -Wno-error=incompatible-pointer-types" \
      ..

echo "[3/4] Building nvcompress, nvdecompress, and nvddsinfo..."
NCPU=$(sysctl -n hw.ncpu 2>/dev/null || echo 4)
make -j"$NCPU" nvcompress nvdecompress nvddsinfo || true

echo "[4/4] Installing binaries..."
INSTALLED=0
for bin in src/nvtt/tools/nvcompress src/nvtt/tools/nvdecompress src/nvtt/tools/nvddsinfo bin/nvcompress bin/nvdecompress bin/nvddsinfo; do
    if [ -f "$bin" ]; then
        B_NAME=$(basename "$bin")
        cp "$bin" "$OUT_DIR/$B_NAME"
        cp "$bin" "$APP_SUPPORT_DIR/$B_NAME"
        chmod +x "$OUT_DIR/$B_NAME" "$APP_SUPPORT_DIR/$B_NAME"
        echo "      ✓ Installed: $B_NAME"
        INSTALLED=1
    fi
done

if [ "$INSTALLED" -eq 1 ]; then
    echo ""
    echo "🎉 nvcompress successfully compiled and installed for macOS!"
    echo "Binaries saved to: $OUT_DIR"
    echo "and: $APP_SUPPORT_DIR"
else
    echo ""
    echo "[!] Note: Automatic build encountered an issue. The built-in Python DDS Engine will continue handling all exports."
fi
