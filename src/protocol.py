"""
Windows Registry URL Protocol Handler for photocraft-dds://
Enables seamless execution of the NVIDIA DDS Exporter without file-dialog popups.
"""

import sys
import os
import winreg

PROTOCOL_NAME = "photocraft-dds"
KEY_PATH = rf"Software\Classes\{PROTOCOL_NAME}"

def register_protocol(launcher_path=None):
    """
    Registers the custom photocraft-dds:// protocol in HKCU.
    Points to pythonw.exe running photocraft_dds_launcher.pyw.
    """
    if not launcher_path:
        launcher_path = os.path.join(
            os.environ.get("APPDATA", ""),
            "Photocraft",
            "photocraft_dds_launcher.pyw"
        )

    python_exe = sys.executable
    pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    runner = pythonw_exe if os.path.exists(pythonw_exe) else python_exe

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY_PATH) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:PhotoCraft DDS Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

        cmd_path = KEY_PATH + r"\shell\open\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_path) as key:
            cmd_str = f'"{runner}" "{launcher_path}" "%1"'
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, cmd_str)

        return True, "Protocol photocraft-dds:// successfully registered!"
    except Exception as e:
        return False, f"Failed registering protocol: {e}"

def unregister_protocol():
    """Deletes the custom photocraft-dds:// protocol key from HKCU."""
    def delete_subkeys(root, subkey):
        try:
            with winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS) as k:
                while True:
                    try:
                        child = winreg.EnumKey(k, 0)
                        delete_subkeys(root, f"{subkey}\\{child}")
                    except OSError:
                        break
            winreg.DeleteKey(root, subkey)
        except FileNotFoundError:
            pass
        except Exception:
            pass

    try:
        delete_subkeys(winreg.HKEY_CURRENT_USER, KEY_PATH)
        return True, "Protocol photocraft-dds:// successfully removed."
    except Exception as e:
        return False, f"Failed removing protocol: {e}"
