"""
PhotoCraft NVIDIA DDS Exporter - One-Click Installer for macOS
Automatically sets up DDS exporting for PhotoCraft on Apple Silicon (M1/M2/M3/M4) and Intel Macs.
"""

import sys
import os
import shutil
import json
import subprocess
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(REPO_ROOT, "src"))

import patcher_mac
import protocol_mac
import dds_engine

BANNER = r"""
  ___ _         _        ___             __ _   
 | _ \ |_  ___ | |_ ___ / __|_ _ __ _  / _| |_ 
 |  _/ ' \/ _ \|  _/ _ \ (__| '_/ _` ||  _|  _|
 |_| |_||_\___/ \__\___/\___|_| \__,_| |_|  \__|
     macOS Edition — Texture Tools DDS Exporter
===================================================
"""

def print_banner():
    print(BANNER)

def install_dependencies():
    print("[1/6] Checking and installing Python dependencies...")
    req_file = os.path.join(REPO_ROOT, "requirements.txt")
    if os.path.exists(req_file):
        cmd = [sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"]
        try:
            subprocess.run(cmd, check=True)
            print("      ✓ Python packages installed successfully (customtkinter, pillow, numpy).")
        except subprocess.CalledProcessError:
            print("      ! Warning: pip install returned an issue. Continuing with existing packages...")

def locate_photocraft_app():
    print("[2/6] Locating PhotoCraft on macOS...")
    app_path = patcher_mac.find_photocraft_app()
    if app_path and os.path.exists(app_path):
        print(f"      ✓ Found PhotoCraft at: {app_path}")
        return app_path

    print("      ! PhotoCraft.app not found in standard /Applications or ~/Applications.")
    custom = input("      Please enter path to PhotoCraft.app (or press Enter to skip binary patch): ").strip().strip('"')
    if custom and os.path.exists(custom):
        return Path(custom)

    print("      -> Continuing without binary patching (You can still launch exporter directly).")
    return None

def deploy_runtime_files():
    print("[3/6] Deploying DDS Exporter runtime to ~/Library/Application Support/Photocraft...")
    app_dir = Path.home() / "Library" / "Application Support" / "Photocraft"
    app_dir.mkdir(parents=True, exist_ok=True)

    tools_dst = app_dir / "nvidia_tools"
    tools_dst.mkdir(parents=True, exist_ok=True)

    # 1. Copy source files
    src_dir = Path(REPO_ROOT) / "src"
    scripts = [
        "photocraft_dds_exporter.py",
        "photocraft_dds_launcher.py",
        "photocraft_dds_launcher_mac.py",
        "dds_engine.py",
        "protocol_mac.py",
        "patcher_mac.py"
    ]
    for s in scripts:
        s_src = src_dir / s
        if s_src.exists():
            shutil.copy2(s_src, app_dir / s)
    print("      ✓ Exporter GUI, macOS launcher, and DDS engines deployed.")

    # 2. Check for mac tools binaries
    tools_mac = Path(REPO_ROOT) / "bin" / "nvidia_tools_mac"
    if tools_mac.exists():
        for f in tools_mac.iterdir():
            if f.is_file():
                dst = tools_dst / f.name
                shutil.copy2(f, dst)
                os.chmod(dst, 0o755)
        print("      ✓ macOS texture tool binaries deployed.")

    return app_dir

def configure_preferences(app_dir):
    print("[4/6] Configuring F10 shortcut in PhotoCraft preferences...")
    pref_path = app_dir / "preferences.json"
    data = {}
    if pref_path.exists():
        try:
            with open(pref_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if "shortcuts" not in data or not isinstance(data["shortcuts"], dict):
        data["shortcuts"] = {}

    data["shortcuts"]["help.reportIssue"] = "F10"

    with open(pref_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("      ✓ Hotkey mapped: [F10] -> photocraft-dds:// Export")

def setup_protocol():
    print("[5/6] Creating macOS Application Bundle and registering photocraft-dds:// protocol...")
    user_apps = Path.home() / "Applications"
    target_app = user_apps / "PhotoCraft DDS Exporter.app"
    
    app_path = protocol_mac.create_mac_app_bundle(target_app)
    ok, msg = protocol_mac.register_protocol(app_path)
    if ok:
        print(f"      ✓ {msg}")
    else:
        print(f"      ! {msg}")
    return app_path

def patch_photocraft_binary(app_path):
    print("[6/6] Patching PhotoCraft binary and ad-hoc re-signing for macOS...")
    if not app_path:
        print("      - Skipping binary patch (PhotoCraft.app not located).")
        return

    ok, msg = patcher_mac.patch_photocraft_mac(app_path)
    if ok:
        print(f"      ✓ {msg}")
    else:
        print(f"      ! Note: {msg}")

def check_texture_engine():
    engine_name, engine_path = dds_engine.get_engine_description()
    print("\n---------------------------------------------------")
    print(f"🎯 Active Texture Engine: {engine_name}")
    if engine_path:
        print(f"   Binary location: {engine_path}")
    else:
        print("   Using built-in Python DDS Engine (supports RGBA, BC1, BC3, BC4, BC5).")
        print("   💡 Optional: For native Apple Silicon / Intel nvcompress speed,")
        print("      run: ./bin/build_nvcompress_mac.sh")
    print("---------------------------------------------------")

def main():
    print_banner()

    try:
        install_dependencies()
        app_path = locate_photocraft_app()
        app_dir = deploy_runtime_files()
        configure_preferences(app_dir)
        setup_protocol()
        patch_photocraft_binary(app_path)
        check_texture_engine()

        print("\n===================================================")
        print("🎉 SUCCESS! PhotoCraft DDS Exporter for macOS is Ready!")
        print("===================================================")
        print("How to use:")
        print("  1. Launch PhotoCraft on your Mac.")
        print("  2. Open or create your image/texture.")
        print("  3. Press [F10] (or launch 'PhotoCraft DDS Exporter.app' from ~/Applications).")
        print("  4. Customize formats (BC7, BC1, BC3, BC5 Normal Maps), mipmaps, or filters.")
        print("  5. Click 'Save as DDS'!")
        print("===================================================\n")

    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
