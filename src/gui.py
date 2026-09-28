"""CustomTkinter Graphical User Interface for Click-to-Paste and Auto-Clicker."""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk
from PIL import Image

from src.auto_clicker import AutoClicker
from src.click_listener import ClickPasteController
from src.config import (
    ASSIGN_OPTIONS,
    PASS_OPTIONS,
    POINT_ACTION_CLICK,
    POINT_ACTION_DOUBLE_CLICK,
    POINT_ACTION_PASTE,
    POINT_ACTIONS,
    POST_ACTIONS,
    AppConfig,
    ClickPoint,
)
from src.pattern_engine import PatternEngine
from src.queue_manager import QueueManager
from src.splash import SplashScreen

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_position() -> tuple:
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return int(pt.x), int(pt.y)

def get_asset_path(filename: str) -> str:
    """Returns absolute path to asset file, compatible with PyInstaller bundles."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", filename)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ClickPasteApp(ctk.CTk):
    """Main Application Window."""

    def __init__(self, queue_mgr: QueueManager, pattern_eng: PatternEngine, config: AppConfig):
        super().__init__()

        self.queue_mgr = queue_mgr
        self.pattern_eng = pattern_eng
        self.config = config

        self.title("Click-to-Paste & Auto-Clicker")
        self.geometry("1040x720")
        self.minsize(920, 620)

        # Set window icon (.ico)
        ico_file = get_asset_path("icon.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        # Load Logo image for header
        self.logo_img = None
        logo_file = get_asset_path("logo.png")
        if os.path.exists(logo_file):
            try:
                pil_logo = Image.open(logo_file)
                self.logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(36, 36))
            except Exception:
                pass

        # Set always on top from config
        self.attributes("-topmost", self.config.always_on_top)

        # Controllers
        self.controller = ClickPasteController(
            queue_mgr=self.queue_mgr,
            pattern_eng=self.pattern_eng,
            config=self.config,
            on_state_change=self._on_manual_state_changed,
            on_item_pasted=self._on_item_pasted,
            on_step_updated=self._on_step_updated,
            on_queue_finished=self._on_queue_finished,
            on_capture_hotkey=self._on_capture_hotkey,
            on_toggle_hotkey=self._on_toggle_hotkey,
            on_stop_hotkey=self._on_stop_hotkey,
        )

        self.auto_clicker = AutoClicker(
            queue_mgr=self.queue_mgr,
            config=self.config,
            on_state_change=self._on_auto_state_changed,
            on_item_processed=self._on_item_pasted,
            on_finished=self._on_queue_finished,
        )

        # Window coordinate getter to ignore clicks inside app in manual mode
        self.controller.set_app_window_getter(
            bbox_fn=self._get_window_bbox,
            hwnd=self._get_window_hwnd(),
        )

        # Initially withdraw (hide) main window while splash screen runs
        self.withdraw()

        self._build_ui()
        self.controller.start_listeners()
        self._poll_mouse_coords()

        # Display splash screen before revealing main window
        self.splash = SplashScreen(self, on_complete=self._on_splash_done, duration_ms=1200)

        # Handle window close cleanup
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_splash_done(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _get_window_hwnd(self) -> Optional[int]:
        try:
            return self.winfo_id()
        except Exception:
            return None

    def _get_window_bbox(self) -> Optional[tuple]:
        """Returns (left, top, right, bottom) in screen coordinates."""
        try:
            if not self.winfo_exists():
                return None
            x = self.winfo_rootx()
            y = self.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
            return (x, y, x + w, y + h)
        except Exception:
            return None

    def _poll_mouse_coords(self):
        """Continuously updates the current cursor coordinate preview label."""
        try:
            if hasattr(self, "mouse_pos_lbl") and self.winfo_exists():
                x, y = get_mouse_position()
                self.mouse_pos_lbl.configure(text=f"Mouse Hover: X={x}, Y={y}")
        except Exception:
            pass
        self.after(100, self._poll_mouse_coords)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Frame
        header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=("#1e293b", "#0f172a"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Title Container with Logo
        title_container = ctk.CTkFrame(header, fg_color="transparent")
        title_container.grid(row=0, column=0, padx=18, pady=10, sticky="w")

        if self.logo_img:
            logo_label = ctk.CTkLabel(title_container, image=self.logo_img, text="")
            logo_label.pack(side="left", padx=(0, 10))

        title_label = ctk.CTkLabel(
            title_container,
            text="Click-to-Paste & Auto-Clicker",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8",
        )
        title_label.pack(side="left")

        # Global Hotkey Guide
        hotkey_lbl = ctk.CTkLabel(
            header,
            text="Toggle: [ F8 ]  |  Stop: [ Esc ]  |  Capture: [ F7 ]",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8",
        )
        hotkey_lbl.grid(row=0, column=1, padx=10, pady=12, sticky="e")

        # Always on Top Switch
        self.top_switch = ctk.CTkSwitch(
            header,
            text="Always on Top",
            command=self._toggle_always_on_top,
            font=ctk.CTkFont(size=12),
        )
        if self.config.always_on_top:
            self.top_switch.select()
        self.top_switch.grid(row=0, column=2, padx=20, pady=12, sticky="e")

        # Main Body - Two Columns
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        body.grid_columnconfigure(0, weight=5)  # Left panel (Queue)
        body.grid_columnconfigure(1, weight=5)  # Right panel (Settings & Controls)
        body.grid_rowconfigure(0, weight=1)

        self._build_left_panel(body)
        self._build_right_panel(body)

        # Footer Frame
        footer = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color=("#0f172a", "#020617"))
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        self.footer_lbl = ctk.CTkLabel(
            footer,
            text="Ready. Load your data and press Start or F8.",
            font=ctk.CTkFont(size=12),
            text_color="#64748b",
        )
        self.footer_lbl.grid(row=0, column=0, padx=20, pady=6, sticky="w")

    def _build_left_panel(self, parent):
        left = ctk.CTkFrame(parent, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        # Top Buttons (Data Import)
        btn_bar = ctk.CTkFrame(left, fg_color="transparent")
        btn_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))

        import_btn = ctk.CTkButton(
            btn_bar,
            text="📁 Import File...",
            command=self._import_file_dialog,
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        import_btn.pack(side="left", padx=(0, 6))

        paste_text_btn = ctk.CTkButton(
            btn_bar,
            text="📋 Paste Text / Queue",
            command=self._open_text_input_dialog,
            fg_color="#334155",
            hover_color="#475569",
            height=32,
            font=ctk.CTkFont(size=12),
        )
        paste_text_btn.pack(side="left", padx=6)

        clear_btn = ctk.CTkButton(
            btn_bar,
            text="Clear",
            command=self._clear_queue,
            fg_color="#ef4444",
            hover_color="#dc2626",
            width=60,
            height=32,
            font=ctk.CTkFont(size=12),
        )
        clear_btn.pack(side="right")

        # Stats & Progress
        stats_frame = ctk.CTkFrame(left, fg_color=("#1e293b", "#1e293b"), corner_radius=8)
        stats_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        stats_frame.grid_columnconfigure(0, weight=1)

        self.stats_lbl = ctk.CTkLabel(
            stats_frame,
            text="Queue: 0 items | Completed: 0 | Remaining: 0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#e2e8f0",
        )
        self.stats_lbl.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(stats_frame, height=8, progress_color="#38bdf8")
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

        # Live Queue List View
        self.queue_box = ctk.CTkTextbox(
            left,
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=8,
            state="disabled",
            wrap="none",
        )
        self.queue_box.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))

        # Bottom Queue Actions
        q_actions = ctk.CTkFrame(left, fg_color="transparent")
        q_actions.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))

        reset_btn = ctk.CTkButton(
            q_actions,
            text="↺ Reset to Beginning",
            command=self._reset_queue_index,
            fg_color="#475569",
            hover_color="#64748b",
            height=28,
            font=ctk.CTkFont(size=12),
        )
        reset_btn.pack(side="left")

    def _build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        # Mode Selector Tabs
        self.mode_seg = ctk.CTkSegmentedButton(
            right,
            values=["🖱 Manual Click Mode", "🤖 Auto-Clicker Mode"],
            command=self._on_mode_change,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.mode_seg.set("🖱 Manual Click Mode")
        self.mode_seg.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        # Spotlight Box (Always Visible)
        spotlight = ctk.CTkFrame(right, fg_color=("#1e293b", "#0f172a"), corner_radius=8)
        spotlight.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        spotlight_hdr = ctk.CTkLabel(
            spotlight,
            text="NEXT ITEM TO PASTE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
        )
        spotlight_hdr.pack(anchor="w", padx=14, pady=(8, 2))

        self.spotlight_val = ctk.CTkLabel(
            spotlight,
            text="[ No data loaded ]",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#38bdf8",
        )
        self.spotlight_val.pack(anchor="w", padx=14, pady=(0, 8))

        # Container for Switching Content between Manual and Auto
        self.mode_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.mode_container.grid(row=2, column=0, sticky="nsew", padx=12, pady=0)
        self.mode_container.grid_columnconfigure(0, weight=1)

        # Build Sub-Frames
        self._build_manual_mode_view()
        self._build_auto_mode_view()

        # Default display manual mode
        self._show_manual_view()

    def _build_manual_mode_view(self):
        self.manual_frame = ctk.CTkFrame(self.mode_container, fg_color="transparent")
        self.manual_frame.grid_columnconfigure(0, weight=1)

        # Manual Trigger Button
        self.manual_toggle_btn = ctk.CTkButton(
            self.manual_frame,
            text="▶ START AUTOMATION (F8)",
            command=self.controller.toggle_active,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=8,
        )
        self.manual_toggle_btn.pack(fill="x", pady=(4, 12))

        # Pattern Sequence Config Section
        pat_frame = ctk.CTkFrame(self.manual_frame, corner_radius=8)
        pat_frame.pack(fill="x", pady=(0, 12))
        pat_frame.grid_columnconfigure(1, weight=1)

        pat_title = ctk.CTkLabel(
            pat_frame,
            text="🎯 Click Pattern Sequence",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
        )
        pat_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))

        pat_entry_lbl = ctk.CTkLabel(pat_frame, text="Sequence (P=Paste, S=Skip):", font=ctk.CTkFont(size=11))
        pat_entry_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=2)

        self.pattern_entry = ctk.CTkEntry(
            pat_frame,
            placeholder_text="e.g. P, S",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
        )
        self.pattern_entry.insert(0, self.config.default_pattern)
        self.pattern_entry.grid(row=1, column=1, sticky="ew", padx=(4, 12), pady=2)
        self.pattern_entry.bind("<KeyRelease>", self._on_pattern_text_change)

        # Quick preset buttons
        preset_bar = ctk.CTkFrame(pat_frame, fg_color="transparent")
        preset_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 8))

        p1_btn = ctk.CTkButton(
            preset_bar,
            text="P (All)",
            command=lambda: self._set_preset_pattern("P"),
            width=65,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
        )
        p1_btn.pack(side="left", padx=(0, 4))

        p2_btn = ctk.CTkButton(
            preset_bar,
            text="P, S (Alternate)",
            command=lambda: self._set_preset_pattern("P, S"),
            width=95,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
        )
        p2_btn.pack(side="left", padx=4)

        p3_btn = ctk.CTkButton(
            preset_bar,
            text="P, S, S (1 in 3)",
            command=lambda: self._set_preset_pattern("P, S, S"),
            width=90,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
        )
        p3_btn.pack(side="left", padx=4)

        # Live Pattern Step Indicator
        self.step_tracker_lbl = ctk.CTkLabel(
            pat_frame,
            text="Current Step: [ 1 / 2 ] ➔ PASTE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10b981",
        )
        self.step_tracker_lbl.grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(4, 10))

        # Shared Options Frame
        self._build_options_section(self.manual_frame)

    def _build_auto_mode_view(self):
        self.auto_frame = ctk.CTkFrame(self.mode_container, fg_color="transparent")
        self.auto_frame.grid_columnconfigure(0, weight=1)

        # Auto Trigger Button
        self.auto_toggle_btn = ctk.CTkButton(
            self.auto_frame,
            text="▶ START AUTO-CLICKER (F8)",
            command=self._toggle_auto_clicker,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=8,
        )
        self.auto_toggle_btn.pack(fill="x", pady=(4, 10))

        # Points Manager Section
        pts_frame = ctk.CTkFrame(self.auto_frame, corner_radius=8)
        pts_frame.pack(fill="x", pady=(0, 10))
        pts_frame.grid_columnconfigure(0, weight=1)

        pts_hdr_row = ctk.CTkFrame(pts_frame, fg_color="transparent")
        pts_hdr_row.pack(fill="x", padx=12, pady=(10, 4))

        pts_title = ctk.CTkLabel(
            pts_hdr_row,
            text="🎯 Click Sequence Points",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
        )
        pts_title.pack(side="left")

        # Live Hover Coordinate Label
        self.mouse_pos_lbl = ctk.CTkLabel(
            pts_hdr_row,
            text="Mouse Hover: X=0, Y=0",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#38bdf8",
        )
        self.mouse_pos_lbl.pack(side="right")

        # Container for point cards
        self.points_list_container = ctk.CTkFrame(pts_frame, fg_color="transparent")
        self.points_list_container.pack(fill="x", padx=12, pady=4)

        # Buttons to add points
        add_btn_row = ctk.CTkFrame(pts_frame, fg_color="transparent")
        add_btn_row.pack(fill="x", padx=12, pady=(6, 10))

        capture_btn = ctk.CTkButton(
            add_btn_row,
            text="🎯 Capture Point (F7)",
            command=self._capture_current_mouse_point,
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        capture_btn.pack(side="left", padx=(0, 6))

        manual_pt_btn = ctk.CTkButton(
            add_btn_row,
            text="➕ Add Custom (X, Y)",
            command=self._add_custom_point_dialog,
            fg_color="#334155",
            hover_color="#475569",
            height=28,
            font=ctk.CTkFont(size=11),
        )
        manual_pt_btn.pack(side="left", padx=6)

        clear_pts_btn = ctk.CTkButton(
            add_btn_row,
            text="Clear Points",
            command=self._clear_auto_points,
            fg_color="#ef4444",
            hover_color="#dc2626",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
        )
        clear_pts_btn.pack(side="right")

        # Distribution & Run Mode Section
        mode_cfg_frame = ctk.CTkFrame(self.auto_frame, corner_radius=8)
        mode_cfg_frame.pack(fill="x", pady=(0, 10))
        mode_cfg_frame.grid_columnconfigure(1, weight=1)

        mode_cfg_title = ctk.CTkLabel(
            mode_cfg_frame,
            text="📋 Distribution & Pass Mode",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
        )
        mode_cfg_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))

        # Item assignment dropdown
        assign_lbl = ctk.CTkLabel(mode_cfg_frame, text="Item Assignment:", font=ctk.CTkFont(size=11))
        assign_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=4)

        self.assign_combo = ctk.CTkComboBox(
            mode_cfg_frame,
            values=ASSIGN_OPTIONS,
            command=self._on_assign_mode_change,
            height=28,
            font=ctk.CTkFont(size=11),
        )
        self.assign_combo.set(self.config.auto_item_assignment)
        self.assign_combo.grid(row=1, column=1, sticky="ew", padx=12, pady=4)

        # Pass execution mode dropdown
        pass_lbl = ctk.CTkLabel(mode_cfg_frame, text="Execution Pass:", font=ctk.CTkFont(size=11))
        pass_lbl.grid(row=2, column=0, sticky="w", padx=12, pady=4)

        self.pass_combo = ctk.CTkComboBox(
            mode_cfg_frame,
            values=PASS_OPTIONS,
            command=self._on_pass_mode_change,
            height=28,
            font=ctk.CTkFont(size=11),
        )
        self.pass_combo.set(self.config.auto_pass_mode)
        self.pass_combo.grid(row=2, column=1, sticky="ew", padx=12, pady=(4, 10))

        # Auto Pacing Interval
        pacing_frame = ctk.CTkFrame(self.auto_frame, corner_radius=8)
        pacing_frame.pack(fill="x", pady=(0, 10))
        pacing_frame.grid_columnconfigure(1, weight=1)

        pacing_hdr = ctk.CTkLabel(
            pacing_frame,
            text="⏱ Interval Between Passes:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        pacing_hdr.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        self.pacing_val_lbl = ctk.CTkLabel(
            pacing_frame,
            text=f"{self.config.auto_item_delay_sec:.1f} s",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8",
        )
        self.pacing_val_lbl.grid(row=0, column=1, sticky="e", padx=12, pady=(10, 4))

        self.pacing_slider = ctk.CTkSlider(
            pacing_frame,
            from_=0.2,
            to=5.0,
            number_of_steps=48,
            command=self._on_pacing_change,
        )
        self.pacing_slider.set(self.config.auto_item_delay_sec)
        self.pacing_slider.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))

        # Shared Options in Auto Frame
        self._build_options_section(self.auto_frame)

    def _build_options_section(self, parent):
        opt_frame = ctk.CTkFrame(parent, corner_radius=8)
        opt_frame.pack(fill="x", pady=(0, 12))
        opt_frame.grid_columnconfigure(1, weight=1)

        opt_title = ctk.CTkLabel(
            opt_frame,
            text="⚙ Timing & Key Actions",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        opt_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))

        # Focus delay slider
        delay_lbl = ctk.CTkLabel(opt_frame, text="Focus Delay (ms):", font=ctk.CTkFont(size=11))
        delay_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=4)

        delay_val_lbl = ctk.CTkLabel(
            opt_frame,
            text=f"{self.config.focus_delay_ms} ms",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8",
        )
        delay_val_lbl.grid(row=1, column=1, sticky="e", padx=12, pady=4)

        delay_slider = ctk.CTkSlider(
            opt_frame,
            from_=20,
            to=400,
            number_of_steps=38,
            command=lambda val, lbl=delay_val_lbl: self._on_delay_change(val, lbl),
        )
        delay_slider.set(self.config.focus_delay_ms)
        delay_slider.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))

        # Post Paste Action
        post_lbl = ctk.CTkLabel(opt_frame, text="Post-Paste Key:", font=ctk.CTkFont(size=11))
        post_lbl.grid(row=3, column=0, sticky="w", padx=12, pady=4)

        post_combo = ctk.CTkComboBox(
            opt_frame,
            values=POST_ACTIONS,
            command=self._on_post_action_change,
            height=28,
            font=ctk.CTkFont(size=11),
        )
        post_combo.set(self.config.post_paste_action)
        post_combo.grid(row=3, column=1, sticky="ew", padx=12, pady=4)

        # Sound switch
        sound_switch = ctk.CTkSwitch(
            opt_frame,
            text="Sound Feedback (Beeps)",
            command=lambda: self._toggle_sound(sound_switch),
            font=ctk.CTkFont(size=11),
        )
        if self.config.sound_feedback:
            sound_switch.select()
        sound_switch.grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 12))

    def _on_mode_change(self, selected_mode: str):
        if "Auto" in selected_mode:
            self.config.mode = "auto"
            self._show_auto_view()
            self._update_status("Auto-Clicker Mode selected. Add target points using F7, then press F8 to run.")
        else:
            self.config.mode = "manual"
            self._show_manual_view()
            self._update_status("Manual Click Mode selected. Press F8 or click Start to arm.")

    def _show_manual_view(self):
        self.auto_frame.pack_forget()
        self.manual_frame.pack(fill="both", expand=True)

    def _show_auto_view(self):
        self.manual_frame.pack_forget()
        self.auto_frame.pack(fill="both", expand=True)
        self._refresh_points_ui()

    # Auto-Clicker Point Management
    def _capture_current_mouse_point(self):
        x, y = get_mouse_position()
        self._add_point_coord(x, y)

    def _on_capture_hotkey(self, x: int, y: int):
        self.after(0, lambda: self._add_point_coord(x, y))

    def _add_point_coord(self, x: int, y: int):
        # Default action: first point pastes, subsequent points just click
        default_act = POINT_ACTION_PASTE if len(self.config.auto_points) == 0 else POINT_ACTION_CLICK
        new_pt = ClickPoint(x=x, y=y, action=default_act)
        self.config.auto_points.append(new_pt)
        self._refresh_points_ui()
        self._update_status(f"Recorded Point #{len(self.config.auto_points)} at (X={x}, Y={y})")

    def _add_custom_point_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Point")
        dialog.geometry("320x220")
        dialog.attributes("-topmost", True)

        x_entry = ctk.CTkEntry(dialog, placeholder_text="X (pixels)")
        x_entry.pack(padx=20, pady=(20, 8), fill="x")

        y_entry = ctk.CTkEntry(dialog, placeholder_text="Y (pixels)")
        y_entry.pack(padx=20, pady=8, fill="x")

        def _save():
            try:
                x = int(x_entry.get().strip())
                y = int(y_entry.get().strip())
                self._add_point_coord(x, y)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid integers for X and Y coordinates.")

        btn = ctk.CTkButton(dialog, text="Add Point", command=_save, fg_color="#0284c7")
        btn.pack(padx=20, pady=16, fill="x")

    def _clear_auto_points(self):
        self.config.auto_points.clear()
        self._refresh_points_ui()
        self._update_status("All auto-click points cleared.")

    def _refresh_points_ui(self):
        for widget in self.points_list_container.winfo_children():
            widget.destroy()

        if not self.config.auto_points:
            empty_lbl = ctk.CTkLabel(
                self.points_list_container,
                text="No target points set.\nHover mouse over target and press F7 to record.",
                font=ctk.CTkFont(size=12),
                text_color="#64748b",
            )
            empty_lbl.pack(pady=12)
            return

        for idx, pt in enumerate(self.config.auto_points):
            row = ctk.CTkFrame(self.points_list_container, fg_color=("#1e293b", "#0f172a"), corner_radius=6)
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(1, weight=1)

            lbl = ctk.CTkLabel(
                row,
                text=f"#{idx+1}  ({pt.x}, {pt.y})",
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                text_color="#38bdf8",
            )
            lbl.grid(row=0, column=0, padx=(10, 8), pady=6, sticky="w")

            combo = ctk.CTkComboBox(
                row,
                values=POINT_ACTIONS,
                command=lambda val, p=pt: self._on_point_action_change(p, val),
                height=26,
                font=ctk.CTkFont(size=11),
                width=160,
            )
            combo.set(pt.action)
            combo.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

            del_btn = ctk.CTkButton(
                row,
                text="✕",
                command=lambda i=idx: self._delete_point(i),
                width=28,
                height=26,
                fg_color="#ef4444",
                hover_color="#dc2626",
                font=ctk.CTkFont(size=11, weight="bold"),
            )
            del_btn.grid(row=0, column=2, padx=(6, 10), pady=6)

    def _on_point_action_change(self, pt: ClickPoint, action: str):
        pt.action = action

    def _delete_point(self, index: int):
        if 0 <= index < len(self.config.auto_points):
            self.config.auto_points.pop(index)
            self._refresh_points_ui()

    def _toggle_auto_clicker(self):
        if not self.config.auto_points:
            messagebox.showwarning("No Points", "Please define at least one target screen point before starting.\n(Hover mouse and press F7)")
            return
        if not self.queue_mgr.has_next():
            messagebox.showwarning("Queue Empty", "Please load items into the queue first.")
            return

        self.auto_clicker.toggle()

    def _on_assign_mode_change(self, value: str):
        self.config.auto_item_assignment = value

    def _on_pass_mode_change(self, value: str):
        self.config.auto_pass_mode = value

    def _on_pacing_change(self, val):
        self.config.auto_item_delay_sec = float(val)
        self.pacing_val_lbl.configure(text=f"{self.config.auto_item_delay_sec:.1f} s")

    # Global Hotkey Handlers
    def _on_toggle_hotkey(self):
        if self.config.mode == "auto":
            self.after(0, self._toggle_auto_clicker)
        else:
            self.controller.toggle_active()

    def _on_stop_hotkey(self):
        self.auto_clicker.stop()
        if self.controller.is_active:
            self.controller.set_active(False)

    # General Event Handlers
    def _toggle_always_on_top(self):
        self.config.always_on_top = bool(self.top_switch.get())
        self.attributes("-topmost", self.config.always_on_top)

    def _toggle_sound(self, switch_widget):
        self.config.sound_feedback = bool(switch_widget.get())

    def _on_delay_change(self, value, lbl):
        delay = int(value)
        self.config.focus_delay_ms = delay
        lbl.configure(text=f"{delay} ms")

    def _on_post_action_change(self, value):
        self.config.post_paste_action = value

    def _set_preset_pattern(self, pattern: str):
        self.pattern_entry.delete(0, "end")
        self.pattern_entry.insert(0, pattern)
        self._on_pattern_text_change()

    def _on_pattern_text_change(self, event=None):
        text = self.pattern_entry.get()
        if self.pattern_eng.set_pattern(text):
            self.pattern_entry.configure(border_color=["#979da2", "#565b5e"])
            self._update_step_tracker()
        else:
            self.pattern_entry.configure(border_color="#ef4444")

    def _update_step_tracker(self):
        curr, total, action = self.pattern_eng.get_status_summary()
        color = "#10b981" if action == "PASTE" else "#f59e0b"
        self.step_tracker_lbl.configure(
            text=f"Current Step: [ {curr} / {total} ] ➔ {action}",
            text_color=color,
        )

    def _import_file_dialog(self):
        filetypes = [
            ("All Supported Files", "*.txt;*.csv;*.xlsx;*.xlsm"),
            ("Text Files (*.txt)", "*.txt"),
            ("CSV Files (*.csv)", "*.csv"),
            ("Excel Files (*.xlsx)", "*.xlsx"),
            ("All Files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select Data File", filetypes=filetypes)
        if path:
            try:
                count = self.queue_mgr.load_from_file(path)
                self._refresh_queue_view()
                self._update_status(f"Imported {count} items from {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to load file:\n{str(e)}")

    def _open_text_input_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Paste Custom Data")
        dialog.geometry("480x420")
        dialog.attributes("-topmost", True)

        lbl = ctk.CTkLabel(dialog, text="Paste text below (one entry per line):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl.pack(padx=16, pady=(16, 8), anchor="w")

        txt_box = ctk.CTkTextbox(dialog, font=ctk.CTkFont(family="Consolas", size=12))
        txt_box.pack(fill="both", expand=True, padx=16, pady=8)

        skip_header_var = tk.BooleanVar(value=False)
        cb = ctk.CTkCheckBox(dialog, text="Skip first line (Header)", variable=skip_header_var)
        cb.pack(padx=16, pady=4, anchor="w")

        def _apply():
            content = txt_box.get("1.0", "end")
            count = self.queue_mgr.load_from_text(content, skip_header=skip_header_var.get())
            dialog.destroy()
            self._refresh_queue_view()
            self._update_status(f"Loaded {count} items from custom text input.")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=12)

        ok_btn = ctk.CTkButton(btn_row, text="Load Data", command=_apply, fg_color="#0284c7")
        ok_btn.pack(side="right", padx=(8, 0))

        cancel_btn = ctk.CTkButton(btn_row, text="Cancel", command=dialog.destroy, fg_color="#475569")
        cancel_btn.pack(side="right")

    def _clear_queue(self):
        self.queue_mgr.clear()
        self._refresh_queue_view()
        self._update_status("Queue cleared.")

    def _reset_queue_index(self):
        self.queue_mgr.reset()
        self.pattern_eng.reset()
        self._refresh_queue_view()
        self._update_step_tracker()
        self._update_status("Queue reset to first item.")

    def _refresh_queue_view(self):
        self.queue_box.configure(state="normal")
        self.queue_box.delete("1.0", "end")

        items = self.queue_mgr.items
        curr_idx = self.queue_mgr.current_index

        for idx, item in enumerate(items):
            if idx < curr_idx:
                prefix = "  [✓] "
                line = f"{prefix}{idx+1:03d}: {item}\n"
            elif idx == curr_idx:
                prefix = "➔ [NEXT] "
                line = f"{prefix}{idx+1:03d}: {item}\n"
            else:
                prefix = "  [ ] "
                line = f"{prefix}{idx+1:03d}: {item}\n"
            self.queue_box.insert("end", line)

        self.queue_box.configure(state="disabled")

        if items:
            frac = curr_idx / max(1, len(items))
            self.queue_box.yview_moveto(max(0.0, frac - 0.1))

        total = self.queue_mgr.total
        completed = self.queue_mgr.completed
        rem = self.queue_mgr.remaining

        self.stats_lbl.configure(
            text=f"Queue: {total} items | Completed: {completed} | Remaining: {rem}"
        )
        progress = completed / total if total > 0 else 0.0
        self.progress_bar.set(progress)

        curr_item = self.queue_mgr.get_current_item()
        if curr_item:
            self.spotlight_val.configure(text=curr_item, text_color="#38bdf8")
        elif total > 0 and rem == 0:
            self.spotlight_val.configure(text="[ ALL COMPLETED ]", text_color="#10b981")
        else:
            self.spotlight_val.configure(text="[ No data loaded ]", text_color="#94a3b8")

    def _update_status(self, text: str):
        self.footer_lbl.configure(text=text)

    # Controller Callbacks
    def _on_manual_state_changed(self, is_active: bool):
        def _update():
            if is_active:
                self.manual_toggle_btn.configure(
                    text="⏸ PAUSE AUTOMATION (F8)",
                    fg_color="#ef4444",
                    hover_color="#dc2626",
                )
                self._update_status("● ARMED & ACTIVE: Left-clicking external target will paste according to pattern.")
            else:
                self.manual_toggle_btn.configure(
                    text="▶ START AUTOMATION (F8)",
                    fg_color="#10b981",
                    hover_color="#059669",
                )
                self._update_status("Paused. Press F8 or click Start to resume.")
        self.after(0, _update)

    def _on_auto_state_changed(self, is_running: bool):
        def _update():
            if is_running:
                self.auto_toggle_btn.configure(
                    text="⏸ PAUSE AUTO-CLICKER (F8)",
                    fg_color="#ef4444",
                    hover_color="#dc2626",
                )
                self._update_status("● AUTO-CLICKER RUNNING: Automated clicking & pasting in progress. Press Esc to stop.")
            else:
                self.auto_toggle_btn.configure(
                    text="▶ START AUTO-CLICKER (F8)",
                    fg_color="#10b981",
                    hover_color="#059669",
                )
                self._update_status("Auto-Clicker paused. Press F8 to resume.")
        self.after(0, _update)

    def _on_item_pasted(self, item: str, completed: int, total: int):
        def _update():
            self._refresh_queue_view()
            self._update_status(f"Pasted: '{item}' ({completed}/{total})")
        self.after(0, _update)

    def _on_step_updated(self):
        self.after(0, self._update_step_tracker)

    def _on_queue_finished(self):
        def _update():
            self._refresh_queue_view()
            self._update_status("Queue finished! All items have been processed.")
            messagebox.showinfo("Done", "All items in the queue have been successfully processed!")
        self.after(0, _update)

    def _on_close(self):
        self.auto_clicker.stop()
        self.controller.stop_listeners()
        self.destroy()
