"""
PhotoCraft NVIDIA DDS Exporter - One-Click Uninstaller for macOS
Restores original PhotoCraft Mach-O binary, unregisters URL protocol, and cleans preferences.
"""

import sys
import os
import json
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(REPO_ROOT, "src"))

import patcher_mac
import protocol_mac

def main():
    print("===================================================")
    print("PhotoCraft DDS Exporter - macOS Uninstaller")
    print("===================================================\n")

    # 1. Restore Mach-O binary
    print("[1/3] Restoring original PhotoCraft binary...")
    app_path = patcher_mac.find_photocraft_app()
    if app_path:
        ok, msg = patcher_mac.restore_photocraft_mac(app_path)
        print(f"      {msg}")
    else:
        print("      PhotoCraft.app not found in standard paths.")

    # 2. Unregister Protocol & Delete App Bundle
    print("[2/3] Unregistering photocraft-dds:// and removing application bundle...")
    ok, msg = protocol_mac.unregister_protocol()
    print(f"      {msg}")

    # 3. Clean Preferences
    print("[3/3] Removing F10 shortcut from preferences.json...")
    pref_path = Path.home() / "Library" / "Application Support" / "Photocraft" / "preferences.json"
    if pref_path.exists():
        try:
            with open(pref_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "shortcuts" in data and "help.reportIssue" in data["shortcuts"]:
                del data["shortcuts"]["help.reportIssue"]
                with open(pref_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("      ✓ Cleaned preferences.json.")
            else:
                print("      Shortcut was not present in preferences.json.")
        except Exception as e:
            print(f"      ! Note: {e}")

    print("\n===================================================")
    print("Uninstallation Complete! PhotoCraft restored to default.")
    print("===================================================\n")

if __name__ == "__main__":
    main()
