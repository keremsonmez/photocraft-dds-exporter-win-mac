"""
PhotoCraft DDS Export Engine
Multi-backend texture compression engine supporting macOS and Windows.
Automatically detects and utilizes:
1. NVIDIA Texture Tools (nvcompress) - Native binary or built via CMake
2. DirectXTex (texconv) - Cross-platform
3. AMD Compressonator (compressonatorcli)
4. Native Python DDS Writer (Zero-dependency fallback for RGBA, BC1, BC3, BC4, BC5)
"""

import sys
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image

def get_photocraft_appdata():
    """Returns the platform-specific Application Support or AppData directory for PhotoCraft."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "Photocraft"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "Photocraft"
    else:
        base = Path.home() / ".config" / "photocraft"
    return base

def find_compression_tool():
    """
    Finds the best available texture compression tool on the system.
    Returns (tool_type: str, tool_path: str or None)
    """
    appdata_tools = get_photocraft_appdata() / "nvidia_tools"
    repo_tools = Path(__file__).resolve().parent.parent / "bin" / ("nvidia_tools_mac" if sys.platform == "darwin" else "nvidia_tools")
    
    # 1. Search for nvcompress
    nv_names = ["nvcompress", "nvcompress.exe"] if sys.platform == "win32" else ["nvcompress"]
    for d in [appdata_tools, repo_tools]:
        for n in nv_names:
            p = d / n
            if p.exists() and os.access(p, os.X_OK if sys.platform != "win32" else os.F_OK):
                return ("nvcompress", str(p))
    
    which_nv = shutil.which("nvcompress")
    if which_nv:
        return ("nvcompress", which_nv)
        
    # 2. Search for texconv
    tc_names = ["texconv", "texconv.exe"] if sys.platform == "win32" else ["texconv"]
    for d in [appdata_tools, repo_tools]:
        for n in tc_names:
            p = d / n
            if p.exists() and os.access(p, os.X_OK if sys.platform != "win32" else os.F_OK):
                return ("texconv", str(p))
                
    which_tc = shutil.which("texconv")
    if which_tc:
        return ("texconv", which_tc)
        
    # 3. Search for compressonatorcli
    which_cmp = shutil.which("compressonatorcli") or shutil.which("compressonatorcli.exe")
    if which_cmp:
        return ("compressonator", which_cmp)
        
    # 4. Fallback to native python DDS writer
    return ("native_python", None)

def get_engine_description():
    """Returns a friendly string describing the active compression engine."""
    tool_type, tool_path = find_compression_tool()
    if tool_type == "nvcompress":
        name = "NVIDIA NVTT nvcompress"
        if sys.platform == "darwin":
            name += " (macOS Native)"
        else:
            name += " (CUDA v3.2.5)"
        return name, tool_path
    elif tool_type == "texconv":
        return "DirectXTex texconv", tool_path
    elif tool_type == "compressonator":
        return "AMD Compressonator CLI", tool_path
    else:
        return "Built-in Python DDS Engine", None


# ==================== NATIVE PYTHON DDS WRITER ====================

def _write_dds_header(f, width, height, mipmap_count=1, fourcc=None, rgb_bit_count=32,
                      r_mask=0x00FF0000, g_mask=0x0000FF00, b_mask=0x000000FF, a_mask=0xFF000000,
                      dx10_format=None):
    """Writes a standardized 128-byte DirectDraw Surface header (with optional DX10 extension)."""
    f.write(b"DDS ")  # Magic

    # dwFlags
    DDSD_CAPS = 0x1
    DDSD_HEIGHT = 0x2
    DDSD_WIDTH = 0x4
    DDSD_PITCH = 0x8
    DDSD_PIXELFORMAT = 0x1000
    DDSD_MIPMAPCOUNT = 0x20000
    DDSD_LINEARSIZE = 0x80000

    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
    if mipmap_count > 1:
        flags |= DDSD_MIPMAPCOUNT

    pitch_or_linear = 0
    if fourcc:
        flags |= DDSD_LINEARSIZE
        block_size = 8 if fourcc in [b"DXT1", b"BC1", b"BC4U", b"ATI1"] else 16
        pitch_or_linear = max(1, (width + 3) // 4) * block_size
    else:
        flags |= DDSD_PITCH
        pitch_or_linear = (width * rgb_bit_count + 7) // 8

    # Caps
    DDSCAPS_TEXTURE = 0x1000
    DDSCAPS_MIPMAP = 0x400000
    DDSCAPS_COMPLEX = 0x8
    caps = DDSCAPS_TEXTURE
    if mipmap_count > 1:
        caps |= (DDSCAPS_MIPMAP | DDSCAPS_COMPLEX)

    # Pixel Format
    DDPF_ALPHAPIXELS = 0x1
    DDPF_FOURCC = 0x4
    DDPF_RGB = 0x40

    if fourcc:
        pf_flags = DDPF_FOURCC
        pf_fourcc = fourcc
        pf_rgb_bits = 0
        r_mask = g_mask = b_mask = a_mask = 0
    else:
        pf_flags = DDPF_RGB | (DDPF_ALPHAPIXELS if a_mask else 0)
        pf_fourcc = b"\x00\x00\x00\x00"
        pf_rgb_bits = rgb_bit_count

    # Pack 124-byte DDS_HEADER
    header = struct.pack(
        "<IIIIIII11I" "II4sIIII" "IIIII",
        124,                # dwSize
        flags,              # dwFlags
        height,             # dwHeight
        width,              # dwWidth
        pitch_or_linear,    # dwPitchOrLinearSize
        0,                  # dwDepth
        mipmap_count,       # dwMipMapCount
        *([0] * 11),        # dwReserved1[11]
        # DDS_PIXELFORMAT (32 bytes)
        32,                 # dwSize
        pf_flags,           # dwFlags
        pf_fourcc,          # dwFourCC
        pf_rgb_bits,        # dwRGBBitCount
        r_mask,             # dwRBitMask
        g_mask,             # dwGBitMask
        b_mask,             # dwBBitMask
        a_mask,             # dwABitMask
        # Caps
        caps,               # dwCaps
        0,                  # dwCaps2
        0,                  # dwCaps3
        0,                  # dwCaps4
        0                   # dwReserved2
    )
    f.write(header)

    if dx10_format is not None:
        # DDS_HEADER_DXT10 (20 bytes)
        # dxgiFormat, resourceDimension (3 = D3D10_RESOURCE_DIMENSION_TEXTURE2D), miscFlag, arraySize, miscFlags2
        dx10_header = struct.pack("<IIIII", dx10_format, 3, 0, 1, 0)
        f.write(dx10_header)

def _generate_mipmaps(img, min_size=1):
    """Generates a list of PIL Images representing mipmap pyramid down to min_size."""
    mips = [img]
    w, h = img.size
    while w > min_size or h > min_size:
        w = max(1, w // 2)
        h = max(1, h // 2)
        mips.append(img.resize((w, h), Image.Resampling.LANCZOS))
        if w == 1 and h == 1:
            break
    return mips

def _encode_bc1_block(block_rgba):
    """
    Encodes a 4x4 RGBA block into 8 bytes of BC1 (DXT1).
    block_rgba: (4, 4, 4) uint8 numpy array.
    """
    rgb = block_rgba[:, :, :3].reshape(-1, 3).astype(np.float32)
    min_c = rgb.min(axis=0)
    max_c = rgb.max(axis=0)

    # Convert RGB to 565
    def to_565(c):
        r = int(np.clip(round(c[0] * 31.0 / 255.0), 0, 31))
        g = int(np.clip(round(c[1] * 63.0 / 255.0), 0, 63))
        b = int(np.clip(round(c[2] * 31.0 / 255.0), 0, 31))
        return (r << 11) | (g << 5) | b

    c0_565 = to_565(max_c)
    c1_565 = to_565(min_c)

    if c0_565 < c1_565:
        c0_565, c1_565 = c1_565, c0_565

    # Reconstruct 4 palette colors in float
    def from_565(val):
        r = ((val >> 11) & 31) * 255.0 / 31.0
        g = ((val >> 5) & 63) * 255.0 / 63.0
        b = (val & 31) * 255.0 / 31.0
        return np.array([r, g, b], dtype=np.float32)

    col0 = from_565(c0_565)
    col1 = from_565(c1_565)
    col2 = (col0 * 2.0 + col1) / 3.0
    col3 = (col0 + col1 * 2.0) / 3.0
    palette = np.stack([col0, col1, col2, col3])  # (4, 3)

    # Distance to palette
    diff = rgb[:, None, :] - palette[None, :, :]  # (16, 4, 3)
    dist = (diff ** 2).sum(axis=2)               # (16, 4)
    indices = np.argmin(dist, axis=1)            # (16,)

    idx_bits = 0
    for i, idx in enumerate(indices):
        idx_bits |= (idx << (i * 2))

    return struct.pack("<HHI", c0_565, c1_565, idx_bits)

def _encode_bc3_block(block_rgba):
    """Encodes a 4x4 RGBA block into 16 bytes of BC3 (DXT5) - 8 bytes alpha + 8 bytes BC1 color."""
    alpha = block_rgba[:, :, 3].reshape(-1).astype(np.float32)
    a_min = int(np.clip(alpha.min(), 0, 255))
    a_max = int(np.clip(alpha.max(), 0, 255))

    if a_max == a_min:
        alpha_block = struct.pack("<BB", a_max, a_min) + b"\x00" * 6
    else:
        a0, a1 = a_max, a_min
        pal_a = np.zeros(8, dtype=np.float32)
        pal_a[0] = a0
        pal_a[1] = a1
        for i in range(1, 7):
            pal_a[i + 1] = ((7 - i) * a0 + i * a1) / 7.0

        diff_a = np.abs(alpha[:, None] - pal_a[None, :])
        idx_a = np.argmin(diff_a, axis=1)

        bits = 0
        for i, idx in enumerate(idx_a):
            bits |= (idx << (i * 3))

        b_bytes = bytearray(6)
        for b_i in range(6):
            b_bytes[b_i] = (bits >> (b_i * 8)) & 0xFF
        alpha_block = struct.pack("<BB", a0, a1) + bytes(b_bytes)

    color_block = _encode_bc1_block(block_rgba)
    return alpha_block + color_block

def _write_native_dds(img, out_path, fmt_choice, gen_mips=True, min_mip=1):
    """Writes DDS file using pure Python / NumPy or Quicktex."""
    # Check if quicktex is installed for C++ speed
    try:
        import quicktex
        has_quicktex = True
    except ImportError:
        has_quicktex = False

    w, h = img.size
    mips = _generate_mipmaps(img, min_mip) if gen_mips else [img]

    # Format handling
    if "BC1" in fmt_choice or "DXT1" in fmt_choice:
        with open(out_path, "wb") as f:
            _write_dds_header(f, w, h, mipmap_count=len(mips), fourcc=b"DXT1")
            for mip in mips:
                mw, mh = mip.size
                arr = np.array(mip.convert("RGBA"))
                # Pad to multiple of 4
                pad_w = (4 - (mw % 4)) % 4
                pad_h = (4 - (mh % 4)) % 4
                if pad_w > 0 or pad_h > 0:
                    arr = np.pad(arr, ((0, pad_h), (0, pad_w), (0, 0)), mode="edge")
                bh, bw = arr.shape[0] // 4, arr.shape[1] // 4
                for by in range(bh):
                    for bx in range(bw):
                        blk = arr[by*4:(by+1)*4, bx*4:(bx+1)*4]
                        f.write(_encode_bc1_block(blk))
        return True

    elif "BC3" in fmt_choice or "DXT5" in fmt_choice:
        with open(out_path, "wb") as f:
            _write_dds_header(f, w, h, mipmap_count=len(mips), fourcc=b"DXT5")
            for mip in mips:
                mw, mh = mip.size
                arr = np.array(mip.convert("RGBA"))
                pad_w = (4 - (mw % 4)) % 4
                pad_h = (4 - (mh % 4)) % 4
                if pad_w > 0 or pad_h > 0:
                    arr = np.pad(arr, ((0, pad_h), (0, pad_w), (0, 0)), mode="edge")
                bh, bw = arr.shape[0] // 4, arr.shape[1] // 4
                for by in range(bh):
                    for bx in range(bw):
                        blk = arr[by*4:(by+1)*4, bx*4:(bx+1)*4]
                        f.write(_encode_bc3_block(blk))
        return True

    else:
        # Default / Uncompressed 32-bit RGBA (BGRA layout for standard DirectDraw surface)
        with open(out_path, "wb") as f:
            _write_dds_header(f, w, h, mipmap_count=len(mips), fourcc=None, rgb_bit_count=32,
                              r_mask=0x00FF0000, g_mask=0x0000FF00, b_mask=0x000000FF, a_mask=0xFF000000)
            for mip in mips:
                arr = np.array(mip.convert("RGBA"))
                # Convert RGBA to BGRA
                bgra = np.empty_like(arr)
                bgra[:, :, 0] = arr[:, :, 2]  # B
                bgra[:, :, 1] = arr[:, :, 1]  # G
                bgra[:, :, 2] = arr[:, :, 0]  # R
                bgra[:, :, 3] = arr[:, :, 3]  # A
                f.write(bgra.tobytes())
        return True


# ==================== UNIFIED EXPORT DISPATCHER ====================

def export_dds(input_image_or_path, out_path, format_choice, effort="Production",
               is_normal_map=False, gen_mipmaps=True, mip_filter="kaiser",
               min_mip_size=1, wrap=True):
    """
    Compresses and exports an image to DDS using the best available platform tool.
    Returns (success: bool, error_message_or_none)
    """
    # 1. Resolve source image
    if isinstance(input_image_or_path, (str, Path)):
        img = Image.open(input_image_or_path).convert("RGBA")
    else:
        img = input_image_or_path

    # Save to temp PNG for external CLI tools
    temp_dir = tempfile.gettempdir()
    temp_png = os.path.join(temp_dir, f"photocraft_export_{os.getpid()}.png")
    img.save(temp_png, "PNG")

    tool_type, tool_path = find_compression_tool()

    try:
        if tool_type == "nvcompress":
            # Map parameters for nvcompress
            fmt_map = {
                "BC7": "-bc7", "BC1": "-bc1", "BC3": "-bc3",
                "BC5": "-bc5", "BC1a": "-bc1a", "BC4": "-bc4",
                "BC6": "-bc6", "RGBA": "-rgb"
            }
            flag_fmt = "-bc7"
            for k, v in fmt_map.items():
                if k in format_choice:
                    flag_fmt = v
                    break

            cmd = [tool_path, flag_fmt]
            eff_map = {"Fast": "-fast", "Production": "-production", "Highest": "-highest"}
            if effort in eff_map:
                cmd.append(eff_map[effort])

            cmd.append("-normal" if is_normal_map else "-color")

            if not gen_mipmaps:
                cmd.append("-nomips")
            else:
                if mip_filter in ["kaiser", "box", "triangle", "mitchell-netravali", "min", "max"]:
                    cmd.extend(["-mipfilter", mip_filter])
                if min_mip_size > 1:
                    cmd.extend(["-min-mip-size", str(min_mip_size)])

            cmd.append("-repeat" if wrap else "-clamp")
            cmd.extend([temp_png, str(out_path)])

            extra_kwargs = {}
            if sys.platform == "win32":
                extra_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            res = subprocess.run(cmd, capture_output=True, text=True, **extra_kwargs)
            if res.returncode == 0 and os.path.exists(out_path):
                return True, None
            else:
                err = res.stderr or res.stdout or f"nvcompress exited with return code {res.returncode}"
                return False, err

        elif tool_type == "texconv":
            # Map parameters for DirectXTex texconv
            tc_fmt = "BC7_UNORM"
            if "BC1" in format_choice: tc_fmt = "BC1_UNORM"
            elif "BC3" in format_choice: tc_fmt = "BC3_UNORM"
            elif "BC5" in format_choice: tc_fmt = "BC5_UNORM"
            elif "BC4" in format_choice: tc_fmt = "BC4_UNORM"
            elif "BC6" in format_choice: tc_fmt = "BC6H_UF16"
            elif "RGBA" in format_choice: tc_fmt = "R8G8B8A8_UNORM"

            out_dir = str(Path(out_path).parent)
            out_name = Path(out_path).name

            cmd = [tool_path, "-f", tc_fmt, "-y"]
            if not gen_mipmaps:
                cmd.extend(["-m", "1"])
            if is_normal_map:
                cmd.append("-nmap")
            if wrap:
                cmd.append("-wrap")

            cmd.extend(["-o", out_dir, temp_png])

            res = subprocess.run(cmd, capture_output=True, text=True)
            # texconv saves with same base stem name as input
            gen_file = os.path.join(out_dir, Path(temp_png).stem + ".dds")
            if os.path.exists(gen_file):
                if gen_file != str(out_path):
                    shutil.move(gen_file, str(out_path))
                return True, None
            else:
                return False, res.stderr or res.stdout or "texconv conversion failed"

        elif tool_type == "compressonator":
            cmp_fmt = "BC7"
            if "BC1" in format_choice: cmp_fmt = "BC1"
            elif "BC3" in format_choice: cmp_fmt = "BC3"
            elif "BC5" in format_choice: cmp_fmt = "BC5"
            elif "BC4" in format_choice: cmp_fmt = "BC4"
            elif "RGBA" in format_choice: cmp_fmt = "ARGB_8888"

            cmd = [tool_path, "-fd", cmp_fmt, temp_png, str(out_path)]
            if not gen_mipmaps:
                cmd.append("-nomips")

            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(out_path):
                return True, None
            else:
                return False, res.stderr or res.stdout or "compressonator conversion failed"

        else:
            # Fallback: Native Python DDS export
            _write_native_dds(img, out_path, format_choice, gen_mips=gen_mipmaps, min_mip=min_mip_size)
            if os.path.exists(out_path):
                return True, None
            return False, "Native Python DDS writer failed."

    except Exception as e:
        return False, str(e)
    finally:
        try:
            if os.path.exists(temp_png):
                os.remove(temp_png)
        except Exception:
            pass
