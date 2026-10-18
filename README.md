# PhotoCraft DDS Exporter (Windows & macOS) 🚀

> **DirectDraw Surface (DDS) Texture Exporter with Full Normal Map & Mipmap Generator for PhotoCraft**
> **Hardware-accelerated on Windows (NVIDIA CUDA v3.2.5) & Native Multi-Engine on macOS (Apple Silicon & Intel)**

An open-source, Photoshop-comparable **DDS Texture Exporter** integration for [PhotoCraft](https://github.com/storytold/photocraft). Provides complete block compression (BC1–BC7), height-to-normal map generation, mipmap filtering, live channel inspection, and native hotkey (`F10`) integration across both **Windows** and **macOS**.

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-blue.svg)](#)
[![NVIDIA CUDA](https://img.shields.io/badge/NVIDIA-CUDA%20v3.2.5-76b900.svg)](#)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-M1%20%2F%20M2%20%2F%20M3%20%2F%20M4-black.svg?logo=apple)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PhotoCraft](https://img.shields.io/badge/PhotoCraft-v1.x-purple.svg)](#)

[🇹🇷 Türkçe Dokümantasyon için tıklayın (README_TR.md)](README_TR.md)

---

## ✨ Features

- ⚡ **High-Performance Compression Engines:**
  - **Windows:** Official **NVIDIA NVTT 3.2.5 CUDA** acceleration (~0.15s to 0.25s for 2K/4K textures).
  - **macOS:** Native multi-engine pipeline (`nvcompress` Mach-O binary, `texconv`, AMD `compressonator`, or built-in Python DDS engine).
- 🎨 **All Compression Formats (BCn Block Compression):**
  - **BC7** (Highest quality, modern games, full smooth alpha)
  - **BC1 / DXT1** (Opaque diffuse textures, 1:8 compression)
  - **BC1a** (1-bit cutout alpha)
  - **BC3 / DXT5** (Smooth interpolated alpha)
  - **BC5** (Dedicated 2-channel RG Normal Maps)
  - **BC4** (Single-channel grayscale / height / roughness)
  - **BC6H** (HDR / floating-point textures)
  - **RGBA** (32-bit uncompressed)
- 🧭 **Complete Height-to-Normal Map Generator:**
  - **7 Height Sources:** `Alpha Channel`, `Average RGB`, `Max RGB`, `Screen RGB`, `Red`, `Green`, `Blue`
  - **6 Filter Types:** `4 Sample`, `3x3` (Sobel), `5x5`, `7x7`, `9x9`, `dUdV`
  - **Seamless Tiling:** Wrap boundary mode (repeat vs clamp)
  - **DirectX / OpenGL Flip:** `Invert X` and `Invert Y` (essential for Unreal Engine, GTA V, FiveM, Unity)
  - **Sliders:** Real-time `Scale` (bump intensity) and `Min Z` control, vector normalization
- 📐 **Mipmap Filtering Pipeline:** Kaiser, Box, Triangle, Mitchell-Netravali, Min, Max filters & custom minimum mip clamp.
- 🪄 **Live 2D Image Effects:** Negative, Lighter, Darker, Contrast, Blur, Sharpen, 2D Convolution.
- 👁️ **Channel Isolation & Live Preview:** Inspect individual channels: `RGBA`, `RGB`, `Alpha`, `Red`, `Green`, `Blue`.
- ⌨️ **Native Hotkey & Menu Integration:**
  - Mapped directly to **`F10`**
  - Automatically captures the active canvas and opens the exporter pre-loaded!

---

## 📦 Quick Installation (1-Click)

Select your operating system below for 1-click automated setup:

### 🪟 Windows Installation

#### Prerequisites
- Windows 10 / 11 (64-bit)
- [Python 3.8+](https://www.python.org/downloads/) installed with *"Add Python to PATH"* checked.
- [PhotoCraft](https://github.com/storytold/photocraft) installed.

#### Steps
1. Open the project folder and double-click **`install.bat`** (or run `python installer/install.py`).
2. The installer will automatically:
   - Install required Python dependencies (`customtkinter`, `pillow`, `numpy`).
   - Copy NVIDIA CUDA binaries and scripts to `%APPDATA%\Photocraft\`.
   - Register the `photocraft-dds://` system protocol in Windows Registry (`HKCU`).
   - Patch `photocraft.exe` in-place (creating a clean `.original` backup).
   - Configure the `F10` hotkey.
3. Launch PhotoCraft and press `F10`!

---

### 🍏 macOS Installation

#### Prerequisites
- macOS 10.15 Catalina or newer (Apple Silicon M1/M2/M3/M4 or Intel).
- Python 3.8+ installed (`python3 --version`).
- [PhotoCraft](https://github.com/storytold/photocraft) installed in `/Applications` or `~/Applications`.

#### Steps
1. Open Terminal in the project folder and run:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   *(Or run `python3 installer/install_mac.py`)*
2. The installer will automatically:
   - Install required Python dependencies (`customtkinter`, `pillow`, `numpy`).
   - Deploy exporter runtime files to `~/Library/Application Support/Photocraft/`.
   - Create `PhotoCraft DDS Exporter.app` in `~/Applications/` and register `photocraft-dds://` via LaunchServices (`lsregister`).
   - Patch `PhotoCraft.app` Mach-O binary (creating a clean `.original` backup).
   - Ad-hoc re-sign the app with `codesign --force --deep --sign -` to ensure Gatekeeper compatibility.
   - Configure the `F10` hotkey in `preferences.json`.
3. Launch PhotoCraft and press `F10`!

---

## 🎮 How to Use

1. Open **PhotoCraft** and work on your texture or artwork.
2. Press **`F10`** on your keyboard (or open `PhotoCraft DDS Exporter` from your applications).
3. The exporter window appears with your active canvas pre-loaded in real-time.
4. Select your **Image Type**, **Format** (e.g. BC7 or BC5 Normal Map), **Mipmap Filter**, or generate Normal Maps.
5. Click **`Save as DDS`** — choose your destination and filename.
6. The file is compressed and exported in seconds!

---

## 🔬 Technical Architecture

Traditional mods require decompiling Rust source code and managing heavy toolchains. This project uses a clean **zero-overhead URL Protocol Bridge**:

```
[ PhotoCraft UI (Press F10 / File > Export) ]
                   │
                   ▼
       Redirect to photocraft-dds://export
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    [ Windows ]          [ macOS ]
  HKCU Registry      macOS LaunchServices
         │                   │
         ▼                   ▼
photocraft_dds_launcher  PhotoCraft DDS Exporter.app
  ├── Windows user32       ├── AppleScript System Events
  │   (Ctrl+Shift+C)       │   (Cmd+Shift+C)
  └── ImageGrab            └── Pasteboard / AppleScript capture
         │                   │
         └─────────┬─────────┘
                   ▼
       photocraft_dds_exporter.py
                   │
                   ▼
  Multi-Engine Texture Compressor
  ├── Windows: NVIDIA CUDA nvcompress 3.2.5
  └── macOS: nvcompress / texconv / Native DDS Engine
```

- **Non-destructive:** Creates a clean `.original` backup of the executable on first run.
- **No Administrator / Root Rights Needed:** Installs into user space (`HKCU` / `%APPDATA%` on Windows, `~/Applications` / `~/Library` on macOS).
- **No Background Resource Usage:** Triggers only on demand via the OS protocol.

---

## 🛠️ Optional: Compiling `nvcompress` on macOS

On macOS, the built-in Python DDS engine works out-of-the-box for all standard formats. If you want native C++ compilation of `nvcompress` using Apple Clang:

```bash
chmod +x bin/build_nvcompress_mac.sh
./bin/build_nvcompress_mac.sh
```

---

## 🗑️ Uninstallation

Select your operating system to cleanly restore PhotoCraft:

### 🪟 Windows
Double-click **`uninstall.bat`** (or run `python installer/uninstall.py`).  
Restores `photocraft.exe.original`, removes the Windows Registry protocol, and cleans `preferences.json`.

### 🍏 macOS
Run in Terminal:
```bash
chmod +x uninstall.sh
./uninstall.sh
```
*(Or run `python3 installer/uninstall_mac.py`)*  
Restores `PhotoCraft.app` binary, re-signs it with `codesign`, unregisters the protocol, and removes `PhotoCraft DDS Exporter.app`.

---

## 📄 License & Credits

- **PhotoCraft DDS Exporter:** Released under the [MIT License](LICENSE).
- **NVIDIA Texture Tools (NVTT):** Copyright © NVIDIA Corporation.
- **PhotoCraft:** Copyright © Storytold & PhotoCraft contributors.
