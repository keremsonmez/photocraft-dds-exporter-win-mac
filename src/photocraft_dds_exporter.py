"""
PhotoCraft - NVIDIA Texture Tools Exporter
A Photoshop-comparable DDS Texture Exporter powered by official NVIDIA NVTT 3.2.5 CUDA acceleration.
Provides the complete NVIDIA Texture Tools options: Image Type, Mipmap Options, Effects,
Compression Effort, and Height-to-Normal Map Generator.
"""

import sys
import os
import subprocess
import threading
from pathlib import Path
import numpy as np
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageOps
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Set CustomTkinter theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

TOOLS_DIR = Path(r"C:\Users\kerem\AppData\Roaming\Photocraft\nvidia_tools")
NVCOMPRESS = TOOLS_DIR / "nvcompress.exe"

FORMAT_MAP = {
    "BC7 (High Quality, Full Alpha)": "-bc7",
    "BC1 / DXT1 (Opaque, No Alpha)": "-bc1",
    "BC3 / DXT5 (Smooth Interpolated Alpha)": "-bc3",
    "BC5 (Normal Maps, 2-Channel RG)": "-bc5",
    "BC1a (1-bit Cutout Alpha)": "-bc1a",
    "BC4 (Grayscale / Height)": "-bc4",
    "BC6H (HDR / Floating Point)": "-bc6",
    "RGBA (32-bit Uncompressed)": "-rgb",
}

EFFORT_MAP = {
    "Default": "",
    "Fast": "-fast",
    "Production": "-production",
    "Highest": "-highest"
}

MIP_FILTERS = ["kaiser", "box", "triangle", "mitchell-netravali", "min", "max"]

class CollapsibleSection(ctk.CTkFrame):
    """Collapsible panel with chevron toggle."""
    def __init__(self, parent, title, is_open=True, on_toggle=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.is_open = is_open
        self.title_text = title
        self.on_toggle = on_toggle

        # Header button
        self.header_btn = ctk.CTkButton(
            self,
            text=f"{'▼' if is_open else '►'}  {title}",
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2b2d30",
            hover_color="#3c3f41",
            text_color="#e0e0e0",
            height=28,
            corner_radius=4,
            command=self.toggle
        )
        self.header_btn.pack(fill="x", padx=1, pady=(3, 1))

        # Content container
        self.content_frame = ctk.CTkFrame(self, fg_color="#1e1f22", corner_radius=4)
        if self.is_open:
            self.content_frame.pack(fill="x", expand=True, padx=2, pady=(1, 3))

    def toggle(self):
        self.is_open = not self.is_open
        self.header_btn.configure(text=f"{'▼' if self.is_open else '►'}  {self.title_text}")
        if self.is_open:
            self.content_frame.pack(fill="x", expand=True, padx=2, pady=(1, 3))
        else:
            self.content_frame.pack_forget()
        if self.on_toggle:
            self.on_toggle(self.is_open)

    def set_open(self, open_state):
        if self.is_open != open_state:
            self.toggle()


class PhotocraftDDSExporter(ctk.CTk):
    def __init__(self, initial_file=None):
        super().__init__()

        self.title("PhotoCraft — NVIDIA Texture Tools Exporter")
        self.geometry("1060x780")
        self.minsize(980, 700)

        # Windows dark title bar
        self.after(10, self._apply_dark_titlebar)

        self.input_file = None
        self.original_image = None   # Base loaded image
        self.processed_image = None  # After effect / normal map
        self.preview_image = None
        self.active_channel = "RGBA"

        self._build_ui()

        if initial_file and os.path.exists(initial_file):
            self.load_image(initial_file)

    def _apply_dark_titlebar(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctk.cast = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctk.cast), ctypes.sizeof(ctk.cast))
        except Exception:
            pass

    def _build_ui(self):
        # Grid layout: 2 columns (Left: Options Sidebar, Right: Preview & Save)
        self.grid_columnconfigure(0, weight=0, minsize=440)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ------------------- LEFT SIDEBAR -------------------
        self.sidebar = ctk.CTkScrollableFrame(self, width=430, corner_radius=0, fg_color="#18181b")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # App Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=10, pady=(10, 6))

        title_lbl = ctk.CTkLabel(
            brand_frame,
            text="NVIDIA Texture Tools",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#76b900"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            brand_frame,
            text="CUDA Accelerated DirectDraw Surface Exporter",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        sub_lbl.pack(anchor="w")

        # 1. IMAGE OPTIONS
        self.sec_image = CollapsibleSection(self.sidebar, "Image Options", is_open=True)
        self.sec_image.pack(fill="x", padx=6, pady=4)
        c_img = self.sec_image.content_frame

        # Image Type
        row_type = ctk.CTkFrame(c_img, fg_color="transparent")
        row_type.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row_type, text="Image Type", width=120, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
        self.image_type_var = ctk.StringVar(value="Color Map")
        self.image_type_menu = ctk.CTkOptionMenu(
            row_type,
            variable=self.image_type_var,
            values=["Color Map", "Grayscale", "Normal Map : Tangent Space", "Normal Map : Object Space"],
            button_color="#1976d2",
            button_hover_color="#1565c0",
            fg_color="#2b2d30",
            command=self._on_image_type_changed,
            width=230
        )
        self.image_type_menu.pack(side="right", fill="x", expand=True)

        # Extract From Atlas
        self.extract_atlas_var = ctk.BooleanVar(value=False)
        self.extract_atlas_chk = ctk.CTkCheckBox(
            c_img,
            text="Extract From Atlas",
            variable=self.extract_atlas_var,
            font=ctk.CTkFont(size=12),
            checkbox_width=18,
            checkbox_height=18
        )
        self.extract_atlas_chk.pack(anchor="w", padx=8, pady=3)

        # Generate Mipmaps
        self.gen_mipmaps_var = ctk.BooleanVar(value=True)
        self.gen_mipmaps_chk = ctk.CTkCheckBox(
            c_img,
            text="Generate Mipmaps",
            variable=self.gen_mipmaps_var,
            font=ctk.CTkFont(size=12),
            checkbox_width=18,
            checkbox_height=18,
            command=self._toggle_mip_options
        )
        self.gen_mipmaps_chk.pack(anchor="w", padx=8, pady=3)

        # Sub-collapsible: Mipmap Options
        self.sec_mipmaps = CollapsibleSection(c_img, "Mipmap Options", is_open=False)
        self.sec_mipmaps.pack(fill="x", padx=6, pady=4)
        c_mip = self.sec_mipmaps.content_frame

        row_mip_filt = ctk.CTkFrame(c_mip, fg_color="transparent")
        row_mip_filt.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(row_mip_filt, text="Filter Type", width=110, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left")
        self.mip_filter_var = ctk.StringVar(value="kaiser")
        self.mip_filter_menu = ctk.CTkOptionMenu(
            row_mip_filt,
            variable=self.mip_filter_var,
            values=MIP_FILTERS,
            button_color="#1976d2",
            button_hover_color="#1565c0",
            fg_color="#2b2d30",
            width=160
        )
        self.mip_filter_menu.pack(side="right", fill="x", expand=True)

        row_min_mip = ctk.CTkFrame(c_mip, fg_color="transparent")
        row_min_mip.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(row_min_mip, text="Minimum Mip Size", width=110, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left")
        self.min_mip_var = ctk.StringVar(value="1")
        self.min_mip_entry = ctk.CTkEntry(row_min_mip, textvariable=self.min_mip_var, width=60, font=ctk.CTkFont(size=11))
        self.min_mip_entry.pack(side="right")

        # 2. EFFECTS
        self.sec_effects = CollapsibleSection(self.sidebar, "Effects", is_open=True)
        self.sec_effects.pack(fill="x", padx=6, pady=4)
        c_eff = self.sec_effects.content_frame

        row_eff = ctk.CTkFrame(c_eff, fg_color="transparent")
        row_eff.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row_eff, text="Effect", width=120, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
        self.effect_var = ctk.StringVar(value="Select...")
        self.effect_menu = ctk.CTkOptionMenu(
            row_eff,
            variable=self.effect_var,
            values=[
                "Select...",
                "2D Convolution",
                "Negative",
                "Lighter",
                "Darker",
                "Contrast More",
                "Contrast Less",
                "Smooth",
                "Sharpen Soft",
                "Sharpen Medium"
            ],
            button_color="#1976d2",
            button_hover_color="#1565c0",
            fg_color="#2b2d30",
            command=self._on_setting_changed,
            width=230
        )
        self.effect_menu.pack(side="right", fill="x", expand=True)

        # 3. COMPRESSION & FORMAT
        self.sec_format = CollapsibleSection(self.sidebar, "Compression Options", is_open=True)
        self.sec_format.pack(fill="x", padx=6, pady=4)
        c_fmt = self.sec_format.content_frame

        row_fmt = ctk.CTkFrame(c_fmt, fg_color="transparent")
        row_fmt.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row_fmt, text="Format", width=120, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
        self.format_var = ctk.StringVar(value="BC7 (High Quality, Full Alpha)")
        self.format_menu = ctk.CTkOptionMenu(
            row_fmt,
            variable=self.format_var,
            values=list(FORMAT_MAP.keys()),
            button_color="#1976d2",
            button_hover_color="#1565c0",
            fg_color="#2b2d30",
            width=230
        )
        self.format_menu.pack(side="right", fill="x", expand=True)

        row_eff_opt = ctk.CTkFrame(c_fmt, fg_color="transparent")
        row_eff_opt.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row_eff_opt, text="Effort", width=120, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left")
        self.effort_var = ctk.StringVar(value="Production")
        self.effort_menu = ctk.CTkOptionMenu(
            row_eff_opt,
            variable=self.effort_var,
            values=list(EFFORT_MAP.keys()),
            button_color="#1976d2",
            button_hover_color="#1565c0",
            fg_color="#2b2d30",
            width=230
        )
        self.effort_menu.pack(side="right", fill="x", expand=True)

        # 4. NORMAL MAP SETTINGS
        self.sec_normal = CollapsibleSection(self.sidebar, "Normal Map Settings", is_open=False)
        self.sec_normal.pack(fill="x", padx=6, pady=4)
        c_norm = self.sec_normal.content_frame

        # Sub-section: Height Source
        self.sec_h_src = CollapsibleSection(c_norm, "Height Source", is_open=True)
        self.sec_h_src.pack(fill="x", padx=4, pady=3)
        c_h_src = self.sec_h_src.content_frame

        self.height_source_var = ctk.StringVar(value="Average RGB")
        sources = ["Alpha Channel", "Average RGB", "Max RGB", "Screen RGB", "Red", "Green", "Blue"]
        for src in sources:
            r = ctk.CTkRadioButton(
                c_h_src,
                text=src,
                variable=self.height_source_var,
                value=src,
                font=ctk.CTkFont(size=11),
                command=self._on_setting_changed
            )
            r.pack(anchor="w", padx=10, pady=2)

        # Sub-section: Height Generation
        self.sec_h_gen = CollapsibleSection(c_norm, "Height Generation", is_open=True)
        self.sec_h_gen.pack(fill="x", padx=4, pady=3)
        c_h_gen = self.sec_h_gen.content_frame

        # Grid for Filter Type (Left) and Wrap/Inverts (Right)
        split_frame = ctk.CTkFrame(c_h_gen, fg_color="transparent")
        split_frame.pack(fill="x", padx=6, pady=4)
        split_frame.columnconfigure(0, weight=1)
        split_frame.columnconfigure(1, weight=1)

        left_filter = ctk.CTkFrame(split_frame, fg_color="transparent")
        left_filter.grid(row=0, column=0, sticky="nw")
        ctk.CTkLabel(left_filter, text="Filter Type...", font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa").pack(anchor="w", pady=(0, 2))
        self.filter_type_var = ctk.StringVar(value="3x3")
        filters = ["4 Sample", "3x3", "5x5", "7x7", "9x9", "dUdV"]
        for flt in filters:
            ctk.CTkRadioButton(
                left_filter,
                text=flt,
                variable=self.filter_type_var,
                value=flt,
                font=ctk.CTkFont(size=11),
                command=self._on_setting_changed
            ).pack(anchor="w", pady=1)

        right_opts = ctk.CTkFrame(split_frame, fg_color="transparent")
        right_opts.grid(row=0, column=1, sticky="nw", padx=(10, 0))
        ctk.CTkLabel(right_opts, text="Options", font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa").pack(anchor="w", pady=(0, 2))

        self.wrap_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(right_opts, text="Wrap", variable=self.wrap_var, font=ctk.CTkFont(size=11), command=self._on_setting_changed).pack(anchor="w", pady=2)

        self.invert_x_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(right_opts, text="Invert X", variable=self.invert_x_var, font=ctk.CTkFont(size=11), command=self._on_setting_changed).pack(anchor="w", pady=2)

        self.invert_y_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(right_opts, text="Invert Y (DirectX)", variable=self.invert_y_var, font=ctk.CTkFont(size=11), command=self._on_setting_changed).pack(anchor="w", pady=2)

        # Min Z Slider
        row_minz = ctk.CTkFrame(c_h_gen, fg_color="transparent")
        row_minz.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(row_minz, text="Min Z", width=50, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left")
        self.min_z_val_lbl = ctk.CTkLabel(row_minz, text="0.000", width=45, font=ctk.CTkFont(size=11))
        self.min_z_val_lbl.pack(side="right")
        self.min_z_slider = ctk.CTkSlider(
            row_minz,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            command=self._on_min_z_slider
        )
        self.min_z_slider.set(0.0)
        self.min_z_slider.pack(side="right", fill="x", expand=True, padx=4)

        # Scale Slider
        row_scale = ctk.CTkFrame(c_h_gen, fg_color="transparent")
        row_scale.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(row_scale, text="Scale", width=50, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left")
        self.scale_val_lbl = ctk.CTkLabel(row_scale, text="1.000", width=45, font=ctk.CTkFont(size=11))
        self.scale_val_lbl.pack(side="right")
        self.scale_slider = ctk.CTkSlider(
            row_scale,
            from_=0.1,
            to=10.0,
            number_of_steps=99,
            command=self._on_scale_slider
        )
        self.scale_slider.set(1.0)
        self.scale_slider.pack(side="right", fill="x", expand=True, padx=4)

        # Sub-section: Alpha Field
        self.sec_alpha_field = CollapsibleSection(c_norm, "Alpha Field", is_open=False)
        self.sec_alpha_field.pack(fill="x", padx=4, pady=3)
        c_af = self.sec_alpha_field.content_frame
        self.alpha_mode_var = ctk.StringVar(value="Set to 1.0")
        for am in ["Set to 1.0", "Preserve Original", "Set to Height"]:
            ctk.CTkRadioButton(c_af, text=am, variable=self.alpha_mode_var, value=am, font=ctk.CTkFont(size=11), command=self._on_setting_changed).pack(anchor="w", padx=8, pady=2)

        # Normalize
        self.normalize_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            c_norm,
            text="Normalize Vectors",
            variable=self.normalize_var,
            font=ctk.CTkFont(size=12),
            command=self._on_setting_changed
        ).pack(anchor="w", padx=10, pady=6)

        # ------------------- RIGHT PANEL (PREVIEW & EXPORT) -------------------
        self.right_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(1, weight=1)

        # Top Bar: Channel filters & Quick actions
        top_ctrl = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        top_ctrl.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 8))

        ctk.CTkLabel(top_ctrl, text="Channels:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#aaaaaa").pack(side="left", padx=(0, 6))
        self.chan_btns = {}
        for ch in ["RGBA", "RGB", "Alpha", "Red", "Green", "Blue"]:
            b = ctk.CTkButton(
                top_ctrl,
                text=ch,
                width=45,
                height=24,
                font=ctk.CTkFont(size=11),
                fg_color="#3c3f41" if ch != "RGBA" else "#1976d2",
                hover_color="#1565c0",
                command=lambda c=ch: self._select_channel(c)
            )
            b.pack(side="left", padx=2)
            self.chan_btns[ch] = b

        open_btn = ctk.CTkButton(
            top_ctrl,
            text="Open Image...",
            width=110,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#2b2d30",
            hover_color="#3c3f41",
            command=self._browse_input
        )
        open_btn.pack(side="right", padx=2)

        # Center Preview Canvas
        self.preview_frame = ctk.CTkFrame(self.right_frame, fg_color="#121212", corner_radius=6)
        self.preview_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)

        self.preview_canvas = ctk.CTkLabel(
            self.preview_frame,
            text="No Image Loaded\nPress F10 in PhotoCraft or click 'Open Image...'",
            font=ctk.CTkFont(size=13),
            text_color="#666666"
        )
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")

        # Bottom Box: Info & Destination & Export
        bottom_box = ctk.CTkFrame(self.right_frame, fg_color="#252526", corner_radius=6)
        bottom_box.grid(row=2, column=0, sticky="ew", padx=8, pady=(8, 0))

        # File info
        self.info_label = ctk.CTkLabel(
            bottom_box,
            text="Ready.",
            font=ctk.CTkFont(size=11),
            text_color="#999999",
            justify="left"
        )
        self.info_label.pack(anchor="w", padx=10, pady=(6, 4))

        # Output path row
        out_row = ctk.CTkFrame(bottom_box, fg_color="transparent")
        out_row.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(out_row, text="Destination:", width=80, anchor="w", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.out_path_var = ctk.StringVar()
        self.out_entry = ctk.CTkEntry(out_row, textvariable=self.out_path_var, font=ctk.CTkFont(size=11))
        self.out_entry.pack(side="left", fill="x", expand=True, padx=6)
        browse_out_btn = ctk.CTkButton(out_row, text="Browse...", width=75, height=26, font=ctk.CTkFont(size=11), command=self._browse_output)
        browse_out_btn.pack(side="right")

        # Big NVIDIA Export Button
        self.export_btn = ctk.CTkButton(
            bottom_box,
            text="Save as DDS",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#76b900",
            hover_color="#5c9200",
            text_color="#000000",
            command=self.start_export
        )
        self.export_btn.pack(fill="x", padx=10, pady=(8, 10))

        # ------------------- STATUS BAR -------------------
        status_frame = ctk.CTkFrame(self, height=24, fg_color="#121212", corner_radius=0)
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_bar = ctk.CTkLabel(
            status_frame,
            text="NVIDIA CUDA Hardware Acceleration Enabled (nvcompress 3.2.5)",
            font=ctk.CTkFont(size=11),
            text_color="#76b900"
        )
        self.status_bar.pack(side="left", padx=10)

    # ------------------- EVENT HANDLERS -------------------

    def _toggle_mip_options(self):
        if not self.gen_mipmaps_var.get():
            self.sec_mipmaps.set_open(False)

    def _on_image_type_changed(self, choice):
        if "Normal Map" in choice:
            self.sec_normal.set_open(True)
            self.format_var.set("BC5 (Normal Maps, 2-Channel RG)")
        elif choice == "Grayscale":
            self.format_var.set("BC4 (Grayscale / Height)")
        else:
            if self.original_image and self.original_image.mode == "RGBA":
                self.format_var.set("BC7 (High Quality, Full Alpha)")
            else:
                self.format_var.set("BC1 / DXT1 (Opaque, No Alpha)")
        self._update_pipeline()

    def _on_min_z_slider(self, val):
        self.min_z_val_lbl.configure(text=f"{val:.3f}")
        self._update_pipeline()

    def _on_scale_slider(self, val):
        self.scale_val_lbl.configure(text=f"{val:.3f}")
        self._update_pipeline()

    def _on_setting_changed(self, *args):
        self._update_pipeline()

    def _select_channel(self, ch):
        self.active_channel = ch
        for name, btn in self.chan_btns.items():
            btn.configure(fg_color="#1976d2" if name == ch else "#3c3f41")
        self._render_preview()

    # ------------------- IMAGE PIPELINE -------------------

    def load_image(self, file_path):
        try:
            self.input_file = Path(file_path)
            self.original_image = Image.open(self.input_file).convert("RGBA")

            w, h = self.original_image.size
            mode = self.original_image.mode
            fsize_kb = os.path.getsize(self.input_file) / 1024.0

            # Update info
            self.info_label.configure(
                text=f"File: {self.input_file.name}  |  Dimensions: {w} × {h} px  |  Mode: {mode} ({fsize_kb:.1f} KB)"
            )

            # Auto suggest format
            lower = self.input_file.stem.lower()
            if any(k in lower for k in ["_n", "normal", "norm"]):
                self.image_type_var.set("Normal Map : Tangent Space")
                self.format_var.set("BC5 (Normal Maps, 2-Channel RG)")
                self.sec_normal.set_open(True)
            elif mode == "RGBA":
                self.format_var.set("BC7 (High Quality, Full Alpha)")
            else:
                self.format_var.set("BC1 / DXT1 (Opaque, No Alpha)")

            # Auto-set output file
            if "photocraft_active_texture" in self.input_file.name.lower():
                desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
                if not os.path.exists(desktop):
                    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                suggested_dds = os.path.join(desktop, "texture.dds")
            else:
                suggested_dds = self.input_file.with_suffix(".dds")
            self.out_path_var.set(str(suggested_dds))

            self._update_pipeline()
            self.status_bar.configure(text=f"Loaded {self.input_file.name}. Ready to export.", text_color="#aaaaaa")
        except Exception as e:
            messagebox.showerror("Error Opening Image", f"Failed to open image:\n{e}")

    def _update_pipeline(self):
        """Processes original_image through Effects and Normal Map settings."""
        if not self.original_image:
            return

        img = self.original_image.copy()

        # 1. Apply Effects
        eff = self.effect_var.get()
        if eff != "Select...":
            img = self._apply_effect(img, eff)

        # 2. Check Image Type or Normal Map
        itype = self.image_type_var.get()
        if itype == "Grayscale":
            gray = img.convert("L")
            img = Image.merge("RGBA", (gray, gray, gray, img.split()[3]))
        elif "Normal Map" in itype or (self.sec_normal.is_open and self.height_source_var.get()):
            img = self._generate_normal_map(img)

        self.processed_image = img
        self._render_preview()

    def _apply_effect(self, img, effect_name):
        if effect_name == "Negative":
            r, g, b, a = img.split()
            rgb = Image.merge("RGB", (r, g, b))
            inv = ImageOps.invert(rgb)
            ir, ig, ib = inv.split()
            return Image.merge("RGBA", (ir, ig, ib, a))
        elif effect_name == "Lighter":
            return ImageEnhance.Brightness(img).enhance(1.25)
        elif effect_name == "Darker":
            return ImageEnhance.Brightness(img).enhance(0.75)
        elif effect_name == "Contrast More":
            return ImageEnhance.Contrast(img).enhance(1.35)
        elif effect_name == "Contrast Less":
            return ImageEnhance.Contrast(img).enhance(0.65)
        elif effect_name == "Smooth":
            return img.filter(ImageFilter.SMOOTH_MORE)
        elif effect_name == "Sharpen Soft":
            return img.filter(ImageFilter.SHARPEN)
        elif effect_name == "Sharpen Medium":
            return ImageEnhance.Sharpness(img).enhance(2.2)
        elif effect_name == "2D Convolution":
            kernel = ImageFilter.Kernel((3, 3), [0, -1, 0, -1, 5, -1, 0, -1, 0])
            return img.filter(kernel)
        return img

    def _generate_normal_map(self, img):
        arr = np.array(img).astype(np.float32) / 255.0
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

        hsrc = self.height_source_var.get()
        if hsrc == "Alpha Channel":
            h = a
        elif hsrc == "Red":
            h = r
        elif hsrc == "Green":
            h = g
        elif hsrc == "Blue":
            h = b
        elif hsrc == "Max RGB":
            h = np.maximum(np.maximum(r, g), b)
        elif hsrc == "Screen RGB":
            h = 1.0 - (1.0 - r) * (1.0 - g) * (1.0 - b)
        else:  # Average RGB
            h = (r + g + b) / 3.0

        flt = self.filter_type_var.get()
        if flt == "4 Sample":
            gx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
            gy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
        elif flt == "5x5":
            gx = (np.roll(h, -2, axis=1) * -1 + np.roll(h, -1, axis=1) * -2 + np.roll(h, 1, axis=1) * 2 + np.roll(h, 2, axis=1) * 1) / 12.0
            gy = (np.roll(h, -2, axis=0) * -1 + np.roll(h, -1, axis=0) * -2 + np.roll(h, 1, axis=0) * 2 + np.roll(h, 2, axis=0) * 1) / 12.0
        elif flt == "dUdV":
            gx = np.gradient(h, axis=1)
            gy = np.gradient(h, axis=0)
        else:  # 3x3 Sobel default
            gx = (
                (np.roll(np.roll(h, -1, axis=0), -1, axis=1) + 2.0 * np.roll(h, -1, axis=1) + np.roll(np.roll(h, 1, axis=0), -1, axis=1)) -
                (np.roll(np.roll(h, -1, axis=0), 1, axis=1) + 2.0 * np.roll(h, 1, axis=1) + np.roll(np.roll(h, 1, axis=0), 1, axis=1))
            ) / 8.0
            gy = (
                (np.roll(np.roll(h, -1, axis=1), -1, axis=0) + 2.0 * np.roll(h, -1, axis=0) + np.roll(np.roll(h, 1, axis=1), -1, axis=0)) -
                (np.roll(np.roll(h, -1, axis=1), 1, axis=0) + 2.0 * np.roll(h, 1, axis=0) + np.roll(np.roll(h, 1, axis=1), 1, axis=0))
            ) / 8.0

        scale = float(self.scale_slider.get())
        nx = -gx * scale
        ny = -gy * scale
        nz = np.ones_like(nx)

        if self.invert_x_var.get():
            nx = -nx
        if self.invert_y_var.get():
            ny = -ny

        min_z = float(self.min_z_slider.get())
        if min_z > 0.0:
            nz = np.maximum(nz, min_z)

        if self.normalize_var.get():
            length = np.sqrt(nx * nx + ny * ny + nz * nz)
            length = np.maximum(length, 1e-6)
            nx /= length
            ny /= length
            nz /= length

        out_r = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
        out_g = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
        out_b = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)

        # Alpha handling
        amode = self.alpha_mode_var.get()
        if amode == "Set to 1.0":
            out_a = np.full_like(out_r, 255)
        elif amode == "Set to Height":
            out_a = np.clip(h * 255.0, 0, 255).astype(np.uint8)
        else:
            out_a = (a * 255.0).astype(np.uint8)

        return Image.fromarray(np.stack([out_r, out_g, out_b, out_a], axis=2), "RGBA")

    def _render_preview(self):
        img = self.processed_image or self.original_image
        if not img:
            return

        # Channel isolation
        ch = self.active_channel
        if ch == "RGB":
            r, g, b, a = img.split()
            display_img = Image.merge("RGB", (r, g, b))
        elif ch == "Alpha":
            a = img.split()[3]
            display_img = Image.merge("RGB", (a, a, a))
        elif ch == "Red":
            r = img.split()[0]
            display_img = Image.merge("RGB", (r, r, r))
        elif ch == "Green":
            g = img.split()[1]
            display_img = Image.merge("RGB", (g, g, g))
        elif ch == "Blue":
            b = img.split()[2]
            display_img = Image.merge("RGB", (b, b, b))
        else:
            display_img = img

        # Thumbnail fit to 380x380
        max_size = (380, 380)
        thumb = display_img.copy()
        thumb.thumbnail(max_size, Image.Resampling.BILINEAR)

        self.preview_image = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
        self.preview_canvas.configure(image=self.preview_image, text="")

    # ------------------- FILE DIALOGS -------------------

    def _browse_input(self):
        f = filedialog.askopenfilename(
            title="Open Image for DDS Export",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.tga;*.tif;*.tiff;*.bmp;*.psd;*.dds"), ("All Files", "*.*")]
        )
        if f:
            self.load_image(f)

    def _browse_output(self):
        initial = self.out_path_var.get()
        initial_dir = os.path.dirname(initial) if initial else os.path.expanduser("~")
        initial_file = os.path.basename(initial) if initial else "texture.dds"
        f = filedialog.asksaveasfilename(
            title="Save DDS File As",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".dds",
            filetypes=[("DirectDraw Surface", "*.dds"), ("All Files", "*.*")]
        )
        if f:
            self.out_path_var.set(f)
            return f
        return None

    # ------------------- EXPORT LOGIC -------------------

    def start_export(self):
        if not self.original_image:
            messagebox.showwarning("No File", "Please select or open an image first.")
            return

        out_path = self.out_path_var.get().strip()
        if not out_path:
            messagebox.showwarning("No Destination", "Please specify a destination DDS file path.")
            return

        if os.path.basename(out_path).lower() in ["texture.dds", "photocraft_active_texture.dds"]:
            chosen = self._browse_output()
            if not chosen:
                return
            out_path = chosen

        self.export_btn.configure(state="disabled", text="Compressing with CUDA...")
        self.status_bar.configure(text="Processing texture with NVIDIA CUDA...", text_color="#76b900")

        threading.Thread(target=self._execute_export, args=(out_path,), daemon=True).start()

    def _execute_export(self, out_path):
        try:
            # 1. Save processed image to temporary PNG
            temp_in = os.path.join(os.environ.get("TEMP", ""), "nvtt_export_in.png")
            img_to_export = self.processed_image or self.original_image
            img_to_export.save(temp_in, "PNG")

            # 2. Build nvcompress command
            fmt_flag = FORMAT_MAP.get(self.format_var.get(), "-bc7")
            effort_flag = EFFORT_MAP.get(self.effort_var.get(), "")

            cmd = [str(NVCOMPRESS), fmt_flag]
            if effort_flag:
                cmd.append(effort_flag)

            # Normal map flag
            itype = self.image_type_var.get()
            if "Normal Map" in itype or self.sec_normal.is_open:
                cmd.append("-normal")
            else:
                cmd.append("-color")

            # Mipmaps
            if not self.gen_mipmaps_var.get():
                cmd.append("-nomips")
            else:
                m_filter = self.mip_filter_var.get()
                if m_filter in MIP_FILTERS:
                    cmd.extend(["-mipfilter", m_filter])
                try:
                    min_sz = int(self.min_mip_var.get())
                    if min_sz > 1:
                        cmd.extend(["-min-mip-size", str(min_sz)])
                except Exception:
                    pass

            # Wrap
            if self.wrap_var.get():
                cmd.append("-repeat")
            else:
                cmd.append("-clamp")

            cmd.extend([temp_in, out_path])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            if result.returncode == 0 and os.path.exists(out_path):
                out_size = os.path.getsize(out_path) / 1024.0
                self.after(0, self._on_export_success, out_path, out_size)
            else:
                self.after(0, self._on_export_failure, result.stderr or result.stdout)
        except Exception as e:
            self.after(0, self._on_export_failure, str(e))

    def _on_export_success(self, out_path, out_size):
        self.export_btn.configure(state="normal", text="Save as DDS")
        msg = f"Successfully exported: {os.path.basename(out_path)} ({out_size:.1f} KB)"
        self.status_bar.configure(text=msg, text_color="#76b900")
        messagebox.showinfo(
            "Export Complete",
            f"Texture exported successfully!\n\nSaved to:\n{out_path}\nSize: {out_size:.1f} KB\nEngine: NVIDIA CUDA nvcompress 3.2.5"
        )

    def _on_export_failure(self, err_msg):
        self.export_btn.configure(state="normal", text="Save as DDS")
        self.status_bar.configure(text="Export failed. See error.", text_color="#ff5555")
        messagebox.showerror("Export Failed", f"nvcompress failed with error:\n{err_msg}")


if __name__ == "__main__":
    initial = sys.argv[1] if len(sys.argv) > 1 else None
    app = PhotocraftDDSExporter(initial)
    app.mainloop()
