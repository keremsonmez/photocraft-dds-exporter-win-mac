"""
PhotoCraft NVIDIA DDS Exporter - One-Click Uninstaller
Restores original PhotoCraft binary and removes custom protocol and shortcuts.
"""

import sys
import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(REPO_ROOT, "src"))

import patcher
import protocol

def main():
    print("===================================================")
    print("PhotoCraft NVIDIA DDS Exporter - Uninstaller")
    print("===================================================\n")

    # 1. Restore binary
    local_exe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "PhotoCraft", "photocraft.exe")
    pf_exe = r"C:\Program Files\PhotoCraft\photocraft.exe"

    target_exe = local_exe if os.path.exists(local_exe) else (pf_exe if os.path.exists(pf_exe) else None)
    if target_exe:
        print(f"[1/3] Restoring original binary for: {target_exe}")
        ok, msg = patcher.restore_photocraft_exe(target_exe)
        print(f"      {msg}")
    else:
        print("[1/3] Could not find photocraft.exe automatically to restore.")

    # 2. Unregister protocol
    print("[2/3] Removing photocraft-dds:// URL protocol from Windows Registry...")
    ok, msg = protocol.unregister_protocol()
    print(f"      {msg}")

    # 3. Clean preferences
    print("[3/3] Removing F10 shortcut from preferences.json...")
    pref_path = os.path.join(os.environ.get("APPDATA", ""), "Photocraft", "preferences.json")
    if os.path.exists(pref_path):
        try:
            with open(pref_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "shortcuts" in data and "help.reportIssue" in data["shortcuts"]:
                del data["shortcuts"]["help.reportIssue"]
                with open(pref_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("      ✓ Cleaned preferences.json.")
        except Exception as e:
            print(f"      ! Note: {e}")

    print("\n===================================================")
    print("Uninstallation Complete! PhotoCraft restored to default.")
    print("===================================================\n")

if __name__ == "__main__":
    main()
