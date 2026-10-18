"""
PhotoCraft NVIDIA DDS Exporter - One-Click Installer
Automatically sets up NVIDIA CUDA-accelerated DDS exporting for PhotoCraft.
"""

import sys
import os
import shutil
import json
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(REPO_ROOT, "src"))

import patcher
import protocol

BANNER = r"""
  ___ _         _        ___             __ _   
 | _ \ |_  ___ | |_ ___ / __|_ _ __ _  / _| |_ 
 |  _/ ' \/ _ \|  _/ _ \ (__| '_/ _` ||  _|  _|
 |_| |_||_\___/ \__\___/\___|_| \__,_| |_|  \__|
  NVIDIA Texture Tools DDS Exporter (CUDA v3.2.5)
===================================================
"""

def print_banner():
    print(BANNER)

def install_dependencies():
    print("[1/5] Checking and installing Python dependencies...")
    req_file = os.path.join(REPO_ROOT, "requirements.txt")
    if os.path.exists(req_file):
        cmd = [sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"]
        try:
            subprocess.run(cmd, check=True)
            print("      ✓ Python packages installed successfully.")
        except subprocess.CalledProcessError:
            print("      ! Warning: pip install encountered an issue. Continuing...")

def find_or_setup_photocraft_exe():
    print("[2/5] Locating PhotoCraft installation...")
    local_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "PhotoCraft")
    local_exe = os.path.join(local_dir, "photocraft.exe")

    pf_exe = r"C:\Program Files\PhotoCraft\photocraft.exe"

    if os.path.exists(local_exe):
        print(f"      ✓ Found PhotoCraft in LocalAppData: {local_exe}")
        return local_exe

    if os.path.exists(pf_exe):
        print(f"      ✓ Found PhotoCraft in Program Files: {pf_exe}")
        # To avoid requiring Administrator privileges on every run, copy to LocalAppData
        os.makedirs(local_dir, exist_ok=True)
        print(f"      -> Creating user-writable PhotoCraft instance at: {local_dir}")
        shutil.copy2(pf_exe, local_exe)
        # Create Desktop shortcut
        _create_desktop_shortcut(local_exe)
        return local_exe

    # Prompt user if installed in custom path
    print("      ! PhotoCraft not found in standard paths.")
    custom_path = input("      Please enter the full path to photocraft.exe: ").strip('"')
    if os.path.exists(custom_path) and os.path.isfile(custom_path):
        return custom_path

    raise FileNotFoundError("Could not find photocraft.exe on this system.")

def _create_desktop_shortcut(target_exe):
    try:
        desk_dir = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        if not os.path.exists(desk_dir):
            desk_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        lnk_path = os.path.join(desk_dir, "PhotoCraft.lnk")

        vbs = f"""
        Set sh = CreateObject("WScript.Shell")
        Set link = sh.CreateShortcut("{lnk_path}")
        link.TargetPath = "{target_exe}"
        link.WorkingDirectory = "{os.path.dirname(target_exe)}"
        link.Save
        """
        temp_vbs = os.path.join(os.environ.get("TEMP", ""), "make_lnk.vbs")
        with open(temp_vbs, "w") as f:
            f.write(vbs)
        subprocess.run(["cscript", "//nologo", temp_vbs], check=True)
        try: os.remove(temp_vbs)
        except: pass
        print(f"      ✓ Created Desktop shortcut: {lnk_path}")
    except Exception as e:
        print(f"      ! Could not create Desktop shortcut automatically: {e}")

def deploy_runtime_files():
    print("[3/5] Deploying NVIDIA Texture Tools and Exporter runtime...")
    appdata_dir = os.path.join(os.environ.get("APPDATA", ""), "Photocraft")
    tools_dst = os.path.join(appdata_dir, "nvidia_tools")
    os.makedirs(tools_dst, exist_ok=True)

    # 1. Copy nvidia_tools binaries
    tools_src = os.path.join(REPO_ROOT, "bin", "nvidia_tools")
    if os.path.exists(tools_src):
        for f in os.listdir(tools_src):
            src_file = os.path.join(tools_src, f)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, os.path.join(tools_dst, f))
        print("      ✓ NVIDIA CUDA binaries (nvcompress 3.2.5) installed.")

    # 2. Copy scripts to AppData/Photocraft
    src_dir = os.path.join(REPO_ROOT, "src")
    for script_name in ["photocraft_dds_exporter.py", "photocraft_dds_launcher.pyw"]:
        s_src = os.path.join(src_dir, script_name)
        s_dst = os.path.join(appdata_dir, script_name)
        if os.path.exists(s_src):
            shutil.copy2(s_src, s_dst)
    print("      ✓ Exporter GUI and Protocol Launcher installed.")

    return appdata_dir

def configure_preferences(appdata_dir):
    print("[4/5] Configuring F10 hotkey shortcut in PhotoCraft preferences...")
    pref_path = os.path.join(appdata_dir, "preferences.json")
    data = {}
    if os.path.exists(pref_path):
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
    print("      ✓ Hotkey mapped: [F10] -> File > Export > NVIDIA DDS…")

def main():
    print_banner()

    try:
        install_dependencies()
        exe_path = find_or_setup_photocraft_exe()
        appdata_dir = deploy_runtime_files()
        configure_preferences(appdata_dir)

        print("[5/5] Patching PhotoCraft binary and registering URL protocol...")
        ok, msg = patcher.patch_photocraft_exe(exe_path)
        if not ok:
            print(f"      ! Patcher warning: {msg}")
        else:
            print(f"      ✓ {msg}")

        launcher_path = os.path.join(appdata_dir, "photocraft_dds_launcher.pyw")
        ok, msg = protocol.register_protocol(launcher_path)
        if not ok:
            print(f"      ! Protocol warning: {msg}")
        else:
            print(f"      ✓ {msg}")

        print("\n===================================================")
        print("🎉 SUCCESS! PhotoCraft NVIDIA DDS Exporter Installed!")
        print("===================================================")
        print("How to use:")
        print("  1. Launch PhotoCraft.")
        print("  2. Open or create your image/texture.")
        print("  3. Press [F10] or click: File > Export > NVIDIA DDS…")
        print("  4. Choose your compression (BC7, BC1, BC3, Normal Map BC5) and click 'Save as DDS'!")
        print("===================================================\n")

    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
