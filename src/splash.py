"""Splash screen window displayed when application launches."""

import os
import sys
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image


def get_asset_path(filename: str) -> str:
    """Returns absolute path to asset file, handling PyInstaller bundles."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", filename)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


class SplashScreen(ctk.CTkToplevel):
    """Frameless modern splash screen with application branding."""

    def __init__(self, parent: ctk.CTk, on_complete: Callable[[], None], duration_ms: int = 1500):
        super().__init__(parent)

        self.parent = parent
        self.on_complete = on_complete
        self.duration_ms = duration_ms

        # Frameless and centered
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        width = 440
        height = 360

        # Center on screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        self.configure(fg_color="#0f172a")

        # Container Frame with border
        container = ctk.CTkFrame(
            self,
            fg_color="#0f172a",
            border_color="#38bdf8",
            border_width=2,
            corner_radius=12,
        )
        container.pack(fill="both", expand=True, padx=2, pady=2)

        # Load Logo
        logo_path = get_asset_path("logo.png")
        self.logo_img = None
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(130, 130))
            except Exception:
                pass

        if self.logo_img:
            logo_lbl = ctk.CTkLabel(container, image=self.logo_img, text="")
            logo_lbl.pack(pady=(28, 12))

        title_lbl = ctk.CTkLabel(
            container,
            text="Click-to-Paste & Auto-Clicker",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#f8fafc",
        )
        title_lbl.pack(pady=(0, 4))

        sub_lbl = ctk.CTkLabel(
            container,
            text="High Performance Windows Automation",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        sub_lbl.pack(pady=(0, 20))

        # Animated progress bar
        self.progress = ctk.CTkProgressBar(
            container,
            width=280,
            height=6,
            progress_color="#38bdf8",
            fg_color="#1e293b",
        )
        self.progress.pack(pady=(0, 12))
        self.progress.set(0.0)

        self._start_progress_animation()

    def _start_progress_animation(self):
        steps = 30
        step_interval = self.duration_ms // steps
        current_step = 0

        def _step():
            nonlocal current_step
            current_step += 1
            progress_val = min(1.0, current_step / steps)
            self.progress.set(progress_val)

            if current_step < steps:
                self.after(step_interval, _step)
            else:
                self._finish()

        self.after(50, _step)

    def _finish(self):
        self.destroy()
        self.on_complete()
