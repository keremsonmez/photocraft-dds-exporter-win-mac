"""
PhotoCraft Mach-O Binary Patcher for macOS
Safely patches the PhotoCraft Mach-O executable to redirect issue reporting URL
to the photocraft-dds:// protocol, and automatically re-signs the application bundle
using macOS codesign so Gatekeeper allows it to run smoothly.
"""

import os
import shutil
import subprocess
from pathlib import Path

TARGET_URL_PRIMARY = b"https://github.com/storytold/photocraft/issues"
PROTOCOL_URL = b"photocraft-dds://export\x00"

COMMON_MAC_PATHS = [
    Path("/Applications/PhotoCraft.app"),
    Path.home() / "Applications" / "PhotoCraft.app",
    Path("/Applications/Photocraft.app"),
    Path.home() / "Applications" / "Photocraft.app"
]

def find_photocraft_app():
    """Finds PhotoCraft.app on standard macOS application paths."""
    for p in COMMON_MAC_PATHS:
        if p.exists() and (p / "Contents" / "MacOS").exists():
            return p
    return None

def find_photocraft_binary(app_path):
    """Finds the main Mach-O executable inside PhotoCraft.app."""
    macos_dir = Path(app_path) / "Contents" / "MacOS"
    if not macos_dir.exists():
        return None
    # Check for 'photocraft' or first executable file
    expected = macos_dir / "photocraft"
    if expected.exists():
        return expected
    for f in macos_dir.iterdir():
        if f.is_file() and not f.name.startswith("."):
            return f
    return None

def is_patched(binary_path):
    """Checks if the Mach-O binary already has the photocraft-dds protocol."""
    try:
        with open(binary_path, "rb") as f:
            data = f.read()
            return b"photocraft-dds://export" in data
    except Exception:
        return False

def re_sign_app(app_path):
    """Re-signs the macOS Application bundle ad-hoc using codesign."""
    try:
        cmd = ["codesign", "--force", "--deep", "--sign", "-", str(app_path)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.returncode == 0
    except Exception:
        return False

def patch_photocraft_mac(app_path=None, create_backup=True):
    """
    Patches PhotoCraft.app executable in-place on macOS.
    Returns (success: bool, message: str)
    """
    if not app_path:
        app_path = find_photocraft_app()

    if not app_path or not os.path.exists(app_path):
        return False, "PhotoCraft.app not found in /Applications or ~/Applications."

    binary_path = find_photocraft_binary(app_path)
    if not binary_path or not binary_path.exists():
        return False, f"Could not locate main executable inside {app_path}"

    if is_patched(binary_path):
        return True, "PhotoCraft is already patched for photocraft-dds://."

    # Backup
    backup_path = Path(str(binary_path) + ".original")
    if create_backup and not backup_path.exists():
        try:
            shutil.copyfile(binary_path, backup_path)
        except Exception as e:
            return False, f"Failed creating backup: {e}"

    with open(binary_path, "rb") as f:
        data = bytearray(f.read())

    # Search for URL target
    pos = data.find(TARGET_URL_PRIMARY)
    if pos == -1:
        # Search for generic issues link
        generic_target = b"github.com/storytold/photocraft"
        pos = data.find(generic_target)

    if pos == -1:
        return False, "Target URL pattern not found in PhotoCraft binary. Unsupported version or already modified."

    # Prepare replacement with padding
    orig_chunk = data[pos : pos + len(TARGET_URL_PRIMARY)]
    replacement = PROTOCOL_URL + (b"\x00" * (len(orig_chunk) - len(PROTOCOL_URL)))

    data[pos : pos + len(replacement)] = replacement

    # Write patched binary
    try:
        with open(binary_path, "wb") as f:
            f.write(data)
    except PermissionError:
        return False, "Permission denied. Please run with sudo or check write permissions on PhotoCraft.app."
    except Exception as e:
        return False, f"Failed writing patched binary: {e}"

    # Re-sign the app bundle
    signed = re_sign_app(app_path)
    if signed:
        return True, f"Successfully patched and ad-hoc re-signed {app_path}!"
    else:
        return True, f"Successfully patched {app_path} (Note: could not re-sign; run 'codesign --force --deep --sign - {app_path}' if macOS complains)"

def restore_photocraft_mac(app_path=None):
    """Restores the original PhotoCraft binary from .original backup."""
    if not app_path:
        app_path = find_photocraft_app()

    if not app_path:
        return False, "PhotoCraft.app not found."

    binary_path = find_photocraft_binary(app_path)
    if not binary_path:
        return False, "PhotoCraft binary not found."

    backup_path = Path(str(binary_path) + ".original")
    if not backup_path.exists():
        return False, "No backup (.original) found to restore."

    try:
        shutil.copyfile(backup_path, binary_path)
        re_sign_app(app_path)
        return True, "Original PhotoCraft binary successfully restored and re-signed!"
    except Exception as e:
        return False, f"Failed restoring binary: {e}"
