# PhotoCraft NVIDIA DDS Exporter 🚀

> **CUDA-Accelerated DirectDraw Surface (DDS) Texture Exporter with Full Normal Map & Mipmap Generator for PhotoCraft**

An open-source, Photoshop-comparable **NVIDIA Texture Tools Exporter** integration for [PhotoCraft](https://github.com/storytold/photocraft). Powered by official **NVIDIA NVTT 3.2.5** CUDA hardware acceleration.

[![Platform](https://img.shields.io/badge/Platform-Windows%20x64-blue.svg)](#)
[![NVIDIA CUDA](https://img.shields.io/badge/NVIDIA-CUDA%20v3.2.5-76b900.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PhotoCraft](https://img.shields.io/badge/PhotoCraft-v1.x-purple.svg)](#)

[🇹🇷 Türkçe Dokümantasyon için tıklayın (README_TR.md)](README_TR.md)

---

## ✨ Features

- ⚡ **NVIDIA CUDA Hardware Acceleration:** Compresses 2K / 4K textures in ~0.15 to 0.25 seconds using official NVIDIA `nvcompress` 3.2.5.
- 🎨 **All Compression Formats:**
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
  - **Sliders:** Real-time `Scale` (bump intensity) and `Min Z` control
  - **Vector Normalization**
- 📐 **Mipmap Filtering Pipeline:**
  - Kaiser, Box, Triangle, Mitchell-Netravali, Min, Max filters
  - Custom Minimum Mipmap Size clamp
- 🪄 **Live 2D Image Effects:**
  - Negative, Lighter, Darker, Contrast More/Less, Smooth (Blur), Sharpen Soft/Medium, 2D Convolution
- 👁️ **Channel Isolation & Live Preview:**
  - Real-time dark GUI canvas preview
  - Inspect individual channels: `RGBA`, `RGB`, `Alpha`, `Red`, `Green`, `Blue`
- ⌨️ **Native Menu & Hotkey Integration:**
  - Mapped directly to **`F10`**
  - Appears natively under **`File` › `Export` › `NVIDIA DDS…`**
  - Automatically captures the active canvas and opens the exporter pre-loaded!

---

## 📦 Quick Installation (1-Click)

### Prerequisites
- Windows 10 / 11 (64-bit)
- [Python 3.8+](https://www.python.org/downloads/) installed with *"Add Python to PATH"* checked.
- [PhotoCraft](https://github.com/storytold/photocraft) installed.

### Installation Steps
1. Download or clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/photocraft-dds-exporter.git
   ```
2. Double-click **`install.bat`** (or run `python installer/install.py`).
3. The installer will automatically:
   - Install required Python dependencies (`customtkinter`, `pillow`, `numpy`).
   - Copy NVIDIA CUDA binaries and scripts to `%APPDATA%\Photocraft\`.
   - Register the `photocraft-dds://` system protocol.
   - Patch `photocraft.exe` in-place (creating a clean `.original` backup).
   - Configure the `F10` hotkey and File menu entry.
4. Launch PhotoCraft and enjoy!

---

## 🎮 How to Use

1. Open **PhotoCraft** and work on your texture/artwork.
2. Press **`F10`** on your keyboard (or click **`File` › `Export` › `NVIDIA DDS…`**).
3. The exporter window appears with your active canvas pre-loaded in real-time.
4. Select your **Image Type**, **Format** (e.g. BC7 or BC5 Normal Map), **Mipmap Filter**, or generate Normal Maps.
5. Click **`Save as DDS`** — a standard Windows *Save As* dialog prompts you for destination and filename.
6. CUDA compresses and exports your DDS file in ~0.2 seconds!

---

## 🔬 Technical Architecture (Why This is Clean & Safe)

Traditional mods require decompiling Rust source code and managing heavy Visual Studio C++ / Rust toolchains. This project uses a **zero-overhead URL Protocol Bridge**:

```
[ PhotoCraft UI (F10 / File > Export) ]
               │
               ▼
   links::COMMANDS table (in-place redirect)
               │
               ▼
   ShellExecute("photocraft-dds://export")
               │
               ▼
   HKCU\Software\Classes\photocraft-dds
               │
               ▼
   photocraft_dds_launcher.pyw
     ├── Grabs active canvas via clipboard (Ctrl+A -> Ctrl+Shift+C -> Ctrl+D)
     └── Launches photocraft_dds_exporter.py with preview pre-loaded
               │
               ▼
   NVIDIA NVTT 3.2.5 CUDA Engine (nvcompress.exe)
```

- **Non-destructive:** Creates a `photocraft.exe.original` backup on first run.
- **No Administrator Rights Needed:** Runs in user space (`HKCU` & `%APPDATA%`).
- **No Background Keylogger / Polling:** Zero background CPU usage; triggers only on demand via OS protocol.

---

## 🗑️ Uninstallation

Double-click **`uninstall.bat`** (or run `python installer/uninstall.py`).  
This cleanly restores `photocraft.exe.original`, removes the registry protocol, and cleans `preferences.json`.

---

## 📄 License & Credits

- **PhotoCraft NVIDIA DDS Exporter:** Released under the [MIT License](LICENSE).
- **NVIDIA Texture Tools (NVTT):** Copyright © NVIDIA Corporation.
- **PhotoCraft:** Copyright © Storytold & PhotoCraft contributors.
