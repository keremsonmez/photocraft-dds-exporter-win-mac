"""
PhotoCraft NVIDIA DDS Launcher for macOS
Triggered via photocraft-dds:// URL protocol from PhotoCraft menu or hotkey.
Activates PhotoCraft, captures active merged canvas via clipboard, and launches DDS Exporter.
"""

import sys
import os
import time
import subprocess
import traceback
import tempfile
from pathlib import Path

def get_app_support_dir():
    p = Path.home() / "Library" / "Application Support" / "Photocraft"
    p.mkdir(parents=True, exist_ok=True)
    return p

LOG_FILE = get_app_support_dir() / "launcher.log"

def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

log(f"macOS Launcher invoked with argv: {sys.argv}")

TEMP_PNG = os.path.join(tempfile.gettempdir(), "photocraft_active_texture.png")

def activate_and_copy_canvas():
    """Activates PhotoCraft on macOS and triggers Cmd+A -> Cmd+Shift+C -> Cmd+D."""
    osa_script = """
    try
        tell application "PhotoCraft" to activate
    on error
        -- If app bundle name is different, bring frontmost
    end try
    delay 0.05
    tell application "System Events"
        -- 1. Select All: Cmd + A
        keystroke "a" using {command down}
        delay 0.05
        -- 2. Copy Merged: Cmd + Shift + C
        keystroke "c" using {command down, shift down}
        delay 0.08
        -- 3. Deselect: Cmd + D
        keystroke "d" using {command down}
    end tell
    """
    try:
        subprocess.run(["osascript", "-e", osa_script], check=False, capture_output=True)
        log("Dispatched AppleScript keystrokes (Cmd+A, Cmd+Shift+C, Cmd+D)")
    except Exception as e:
        log(f"AppleScript keystroke error: {e}")

def grab_clipboard_image():
    """Grabs clipboard image on macOS using AppleScript, Pillow, or pngpaste."""
    time.sleep(0.05)

    # Method 1: AppleScript direct binary extraction
    osa_grab = f'''
    set outPath to "{TEMP_PNG}"
    try
        set theFile to (open for access POSIX file outPath with write permission)
        set eof theFile to 0
        try
            write (the clipboard as «class PNGf») to theFile
        on error
            write (the clipboard as TIFF picture) to theFile
        end try
        close access theFile
    on error err
        try
            close access file outPath
        end try
    end try
    '''
    try:
        subprocess.run(["osascript", "-e", osa_grab], capture_output=True, text=True, check=False)
        if os.path.exists(TEMP_PNG) and os.path.getsize(TEMP_PNG) > 100:
            from PIL import Image
            with Image.open(TEMP_PNG) as im:
                im.convert("RGBA").save(TEMP_PNG, "PNG")
            log(f"Captured canvas via AppleScript: {TEMP_PNG} ({os.path.getsize(TEMP_PNG)} bytes)")
            return TEMP_PNG
    except Exception as e:
        log(f"AppleScript clipboard grab attempt notice: {e}")

    # Method 2: Pillow ImageGrab
    for attempt in range(5):
        time.sleep(0.04)
        try:
            from PIL import ImageGrab, Image
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                img.save(TEMP_PNG, "PNG")
                log(f"Captured canvas via ImageGrab: {img.size} saved to {TEMP_PNG}")
                return TEMP_PNG
        except Exception as e:
            log(f"ImageGrab attempt {attempt} error: {e}")

    # Method 3: pngpaste (if installed via brew)
    if shutil_which("pngpaste"):
        try:
            subprocess.run(["pngpaste", TEMP_PNG], check=True, capture_output=True)
            if os.path.exists(TEMP_PNG) and os.path.getsize(TEMP_PNG) > 0:
                log(f"Captured canvas via pngpaste: {TEMP_PNG}")
                return TEMP_PNG
        except Exception as e:
            log(f"pngpaste failed: {e}")

    log("No image could be grabbed from clipboard.")
    return None

def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)

def find_exporter_script():
    """Locates photocraft_dds_exporter.py."""
    app_support = get_app_support_dir() / "photocraft_dds_exporter.py"
    if app_support.exists():
        return str(app_support)

    repo_script = Path(__file__).resolve().parent / "photocraft_dds_exporter.py"
    if repo_script.exists():
        return str(repo_script)

    return "photocraft_dds_exporter.py"

def main():
    try:
        log("Starting canvas capture...")
        activate_and_copy_canvas()
        captured_png = grab_clipboard_image()

        exporter_path = find_exporter_script()
        log(f"Exporter script path: {exporter_path}")

        args = [sys.executable, exporter_path]
        if captured_png and os.path.exists(captured_png):
            args.append(captured_png)

        log(f"Launching exporter process: {args}")
        p = subprocess.Popen(args)
        log(f"Exporter process started with PID: {p.pid}")
    except Exception as e:
        log(f"Fatal error in launcher: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
