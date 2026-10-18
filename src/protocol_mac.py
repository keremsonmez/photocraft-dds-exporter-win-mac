"""
macOS URL Protocol Handler for photocraft-dds://
Creates a native macOS Application Bundle with CFBundleURLTypes and registers it
with LaunchServices (lsregister) to handle photocraft-dds:// URLs.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

LSREGISTER_PATHS = [
    "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister",
    "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"
]

def find_lsregister():
    for p in LSREGISTER_PATHS:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return "lsregister"

def get_default_app_path():
    user_apps = Path.home() / "Applications"
    user_apps.mkdir(parents=True, exist_ok=True)
    return user_apps / "PhotoCraft DDS Exporter.app"

def create_mac_app_bundle(target_app_path=None):
    """
    Builds the PhotoCraft DDS Exporter.app bundle with Info.plist declaring photocraft-dds:// scheme.
    """
    app_path = Path(target_app_path) if target_app_path else get_default_app_path()
    contents = app_path / "Contents"
    macos_dir = contents / "MacOS"
    resources_dir = contents / "Resources"

    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    # 1. Info.plist
    info_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.storytold.photocraft.ddsexporter</string>
    <key>CFBundleName</key>
    <string>PhotoCraft DDS Exporter</string>
    <key>CFBundleDisplayName</key>
    <string>PhotoCraft DDS Exporter</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleExecutable</key>
    <string>photocraft_dds_launcher</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>LSUIElement</key>
    <false/>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>PhotoCraft DDS Protocol</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>photocraft-dds</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
"""
    with open(contents / "Info.plist", "w", encoding="utf-8") as f:
        f.write(info_plist)

    # 2. Executable launcher script
    launcher_sh = f"""#!/usr/bin/env bash
# PhotoCraft DDS Protocol Handler Launcher Wrapper
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" >/dev/null 2>&1 && pwd )"

# Locate Python 3
PYTHON_BIN="$(which python3 2>/dev/null || echo "/usr/bin/python3")"

APP_SUPPORT="$HOME/Library/Application Support/Photocraft"
SCRIPT_TARGET="$APP_SUPPORT/photocraft_dds_launcher_mac.py"
if [ ! -f "$SCRIPT_TARGET" ]; then
    SCRIPT_TARGET="$APP_SUPPORT/photocraft_dds_launcher.py"
fi

exec "$PYTHON_BIN" "$SCRIPT_TARGET" "$@"
"""
    exec_path = macos_dir / "photocraft_dds_launcher"
    with open(exec_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(launcher_sh)

    # chmod +x
    try:
        os.chmod(exec_path, 0o755)
    except Exception:
        pass

    return str(app_path)

def register_protocol(app_path=None):
    """
    Registers the photocraft-dds:// protocol on macOS using LaunchServices.
    """
    if not app_path or not os.path.exists(app_path):
        app_path = create_mac_app_bundle(app_path)

    lsregister = find_lsregister()
    cmd = [lsregister, "-f", "-R", "-trusted", str(app_path)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return True, f"Protocol photocraft-dds:// successfully registered via {app_path}"
        else:
            return True, f"Application bundle created at {app_path} (lsregister exit: {res.returncode})"
    except Exception as e:
        return True, f"Application bundle ready at {app_path} (Note: {e})"

def unregister_protocol(app_path=None):
    """
    Unregisters the photocraft-dds:// protocol and deletes the app bundle.
    """
    target = Path(app_path) if app_path else get_default_app_path()
    lsregister = find_lsregister()

    msg = ""
    if target.exists():
        try:
            subprocess.run([lsregister, "-u", str(target)], check=False, capture_output=True)
            shutil.rmtree(target)
            msg = f"Protocol photocraft-dds:// unregistered and {target} removed."
        except Exception as e:
            msg = f"Failed removing app bundle: {e}"
    else:
        msg = "App bundle not found; nothing to unregister."

    return True, msg
