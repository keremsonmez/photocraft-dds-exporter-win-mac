"""
PhotoCraft NVIDIA DDS Launcher (Cross-Platform)
Routes to platform-specific launcher logic:
- macOS: AppleScript activation, Cmd+A -> Cmd+Shift+C -> Cmd+D, clipboard extraction
- Windows: ctypes.windll.user32, keybd_event, ImageGrab
"""

import sys
import os

if sys.platform == "darwin":
    try:
        from photocraft_dds_launcher_mac import main
    except ImportError:
        from src.photocraft_dds_launcher_mac import main
else:
    # Windows / Fallback
    try:
        from photocraft_dds_launcher_win import main
    except ImportError:
        # Fallback inline or legacy launcher
        import time
        import subprocess
        from PIL import Image, ImageGrab
        import tempfile

        def main():
            temp_png = os.path.join(tempfile.gettempdir(), "photocraft_active_texture.png")
            try:
                img = ImageGrab.grabclipboard()
                if isinstance(img, Image.Image):
                    img.save(temp_png, "PNG")
            except Exception:
                pass

            script_dir = os.path.dirname(__file__)
            exporter = os.path.join(script_dir, "photocraft_dds_exporter.py")
            cmd = [sys.executable, exporter]
            if os.path.exists(temp_png):
                cmd.append(temp_png)
            subprocess.Popen(cmd)

if __name__ == "__main__":
    main()
