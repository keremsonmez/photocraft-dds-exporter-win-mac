"""
PhotoCraft NVIDIA DDS Launcher
Triggered via photocraft-dds:// URL protocol from PhotoCraft menu or hotkey.
Captures active merged canvas via clipboard and launches NVIDIA DDS Exporter.
"""

import sys
import os
import time
import subprocess
import traceback
import ctypes
from ctypes import wintypes
from PIL import Image, ImageGrab

APPDATA_DIR = os.path.join(os.environ.get("APPDATA", ""), "Photocraft")
LOG_FILE = os.path.join(APPDATA_DIR, "launcher.log")

def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

log(f"Launcher invoked with argv: {sys.argv}")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_A = 0x41
VK_C = 0x43
VK_D = 0x44

KEYEVENTF_KEYUP = 0x0002

EXPORTER_SCRIPT = os.path.join(APPDATA_DIR, "photocraft_dds_exporter.py")
TEMP_PNG = os.path.join(os.environ.get("TEMP", ""), "photocraft_active_texture.png")

def find_photocraft_hwnd():
    found = []
    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                if "photocraft" in title:
                    found.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    if found:
        return found[0]
    return user32.GetForegroundWindow()

def empty_clipboard():
    try:
        if user32.OpenClipboard(None):
            user32.EmptyClipboard()
            user32.CloseClipboard()
    except Exception:
        pass

def send_key_combo():
    # 1. Select All: Ctrl + A
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_A, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_A, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.04)

    # 2. Copy Merged: Ctrl + Shift + C
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_SHIFT, 0, 0, 0)
    user32.keybd_event(VK_C, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.06)

    # 3. Deselect: Ctrl + D
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_D, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

def capture_canvas():
    hwnd = find_photocraft_hwnd()
    log(f"PhotoCraft hwnd: {hwnd}")
    if hwnd:
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.05)

    empty_clipboard()
    send_key_combo()

    for i in range(8):
        time.sleep(0.05)
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                img.save(TEMP_PNG, "PNG")
                log(f"Captured canvas image: {img.size} saved to {TEMP_PNG}")
                return TEMP_PNG
        except Exception as e:
            log(f"grabclipboard attempt {i} exception: {e}")

    log("No image captured from clipboard.")
    return None

def main():
    try:
        png_path = capture_canvas()

        python_exe = sys.executable
        pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        runner = pythonw_exe if os.path.exists(pythonw_exe) else python_exe

        args = [runner, EXPORTER_SCRIPT]
        if png_path and os.path.exists(png_path):
            args.append(png_path)

        log(f"Launching exporter: {args}")
        p = subprocess.Popen(args)
        log(f"Exporter launched, PID: {p.pid}")
    except Exception as e:
        log(f"Fatal error in launcher: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
