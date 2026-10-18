"""
PhotoCraft Binary Patcher
Safely modifies photocraft.exe in-place to redirect File > Export and hotkey
to the photocraft-dds:// custom URL protocol without requiring Rust recompilation.
"""

import os
import shutil
import struct

OFFSET_CATALOG_ENTRY = 0x5704500
OFFSET_INPLACE_LABEL = 0x5627710
OFFSET_URL_STRING    = 0x57C8D27
OFFSET_COMMAND_ENTRY = 0x57C8DD8

VA_PATH_FILE_EXPORT  = 0x1456ee700
VA_LABEL_NVIDIA_DDS  = 0x145628910
VA_ID_REPORT_ISSUE   = 0x1456eee83

PROTOCOL_URL         = b"photocraft-dds://export\x00"
PROTOCOL_URL_LEN     = 23
LABEL_TEXT           = "NVIDIA DDS…".encode("utf-8") # 13 bytes

def is_patched(exe_path):
    """Checks if the executable is already patched."""
    try:
        with open(exe_path, "rb") as f:
            f.seek(OFFSET_URL_STRING)
            return f.read(22) == b"photocraft-dds://expor"
    except Exception:
        return False

def patch_photocraft_exe(exe_path, create_backup=True):
    """
    Applies in-place binary modifications to photocraft.exe.
    Returns (success: bool, message: str)
    """
    if not os.path.exists(exe_path):
        return False, f"Executable not found at: {exe_path}"

    orig_backup = exe_path + ".original"
    if create_backup and not os.path.exists(orig_backup):
        shutil.copyfile(exe_path, orig_backup)

    with open(exe_path, "rb") as f:
        data = bytearray(f.read())

    # Safety checks
    if len(data) < OFFSET_COMMAND_ENTRY + 32:
        return False, "File size smaller than expected. Unsupported PhotoCraft version."

    # 1. Write URL string at 0x57C8D27
    data[OFFSET_URL_STRING : OFFSET_URL_STRING + len(PROTOCOL_URL)] = PROTOCOL_URL

    # 2. Update url_len in links::COMMANDS entry 4 (0x57C8DD8 + 24)
    data[OFFSET_COMMAND_ENTRY + 24 : OFFSET_COMMAND_ENTRY + 32] = struct.pack("<Q", PROTOCOL_URL_LEN)

    # 3. Write 'NVIDIA DDS…' into in-place string buffer at 0x5627710
    data[OFFSET_INPLACE_LABEL : OFFSET_INPLACE_LABEL + len(LABEL_TEXT)] = LABEL_TEXT

    # 4. Update CATALOG entry at 0x5704500:
    # Path -> ['File', 'Export'] (0x1456ee700, len 2)
    data[OFFSET_CATALOG_ENTRY : OFFSET_CATALOG_ENTRY + 8] = struct.pack("<Q", VA_PATH_FILE_EXPORT)
    data[OFFSET_CATALOG_ENTRY + 8 : OFFSET_CATALOG_ENTRY + 16] = struct.pack("<Q", 2)

    # Label -> 'NVIDIA DDS…' (0x145628910, len 13)
    data[OFFSET_CATALOG_ENTRY + 16 : OFFSET_CATALOG_ENTRY + 24] = struct.pack("<Q", VA_LABEL_NVIDIA_DDS)
    data[OFFSET_CATALOG_ENTRY + 24 : OFFSET_CATALOG_ENTRY + 32] = struct.pack("<Q", len(LABEL_TEXT))

    # ID -> 'help.reportIssue' (0x1456eee83, len 16)
    data[OFFSET_CATALOG_ENTRY + 48 : OFFSET_CATALOG_ENTRY + 56] = struct.pack("<Q", VA_ID_REPORT_ISSUE)
    data[OFFSET_CATALOG_ENTRY + 56 : OFFSET_CATALOG_ENTRY + 64] = struct.pack("<Q", 16)

    try:
        with open(exe_path, "wb") as f:
            f.write(data)
        return True, "PhotoCraft binary successfully patched!"
    except PermissionError:
        return False, "Permission denied. Ensure PhotoCraft is closed and run as administrator if needed."
    except Exception as e:
        return False, f"Failed writing patched binary: {e}"

def restore_photocraft_exe(exe_path):
    """Restores the original untouched photocraft.exe from backup."""
    orig_backup = exe_path + ".original"
    bak_backup = exe_path + ".bak"

    target_backup = orig_backup if os.path.exists(orig_backup) else (bak_backup if os.path.exists(bak_backup) else None)
    if not target_backup:
        return False, "No backup file (.original or .bak) found to restore."

    try:
        shutil.copyfile(target_backup, exe_path)
        return True, "Original PhotoCraft binary successfully restored!"
    except Exception as e:
        return False, f"Failed restoring binary: {e}"
