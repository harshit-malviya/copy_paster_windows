"""CustomTkinter Graphical User Interface for Click-to-Paste."""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from src.click_listener import ClickPasteController
from src.config import (
    POST_ACTIONS,
    AppConfig,
)
from src.pattern_engine import PatternEngine
from src.queue_manager import QueueManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class ClickPasteApp(ctk.CTk):
    """Main Application Window."""

    def __init__(self, queue_mgr: QueueManager, pattern_eng: PatternEngine, config: AppConfig):
        super().__init__()

        self.queue_mgr = queue_mgr
        self.pattern_eng = pattern_eng
        self.config = config

        self.title("⚡ Click-to-Paste Automation")
        self.geometry("980x680")
        self.minsize(860, 580)

        # Set always on top from config
        self.attributes("-topmost", self.config.always_on_top)

        # Controller initialized
        self.controller = ClickPasteController(
            queue_mgr=self.queue_mgr,
            pattern_eng=self.pattern_eng,
            config=self.config,
            on_state_change=self._on_state_changed,
            on_item_pasted=self._on_item_pasted,
            on_step_updated=self._on_step_updated,
            on_queue_finished=self._on_queue_finished,
        )

        # Provide window coordinate getter to controller to ignore clicks inside app
        self.controller.set_app_window_getter(
            bbox_fn=self._get_window_bbox,
            hwnd=self._get_window_hwnd(),
        )

        self._build_ui()
        self.controller.start_listeners()

        # Handle window close cleanup
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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

    def _build_ui(self):
        # Grid layout (Header, Main Body, Footer)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Frame
        header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=("#1e293b", "#0f172a"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text="⚡ Click-to-Paste Automation",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8",
        )
        title_label.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        # Global Hotkey Guide
        hotkey_lbl = ctk.CTkLabel(
            header,
            text="Toggle: [ F8 ]   |   Stop: [ Esc ]",
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
        body.grid_columnconfigure(0, weight=6)  # Left panel (Queue)
        body.grid_columnconfigure(1, weight=4)  # Right panel (Settings & Controls)
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

        # Big Main Trigger Button
        self.toggle_btn = ctk.CTkButton(
            right,
            text="▶ START AUTOMATION (F8)",
            command=self.controller.toggle_active,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=54,
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=8,
        )
        self.toggle_btn.grid(row=0, column=0, sticky="ew", padx=16, pady=16)

        # Spotlight Box (Current Item to be pasted)
        spotlight = ctk.CTkFrame(right, fg_color=("#1e293b", "#0f172a"), corner_radius=8)
        spotlight.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

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

        # Pattern Sequence Config Section
        pat_frame = ctk.CTkFrame(right, corner_radius=8)
        pat_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        pat_frame.grid_columnconfigure(1, weight=1)

        pat_title = ctk.CTkLabel(
            pat_frame,
            text="🎯 Click Pattern Sequence",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
        )
        pat_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))

        # Pattern entry
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

        # Additional Options Frame
        opt_frame = ctk.CTkFrame(right, corner_radius=8)
        opt_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        opt_frame.grid_columnconfigure(1, weight=1)

        opt_title = ctk.CTkLabel(
            opt_frame,
            text="⚙ Options & Timing",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        opt_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 6))

        # Focus delay slider
        delay_lbl = ctk.CTkLabel(opt_frame, text="Focus Delay (ms):", font=ctk.CTkFont(size=11))
        delay_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=4)

        self.delay_val_lbl = ctk.CTkLabel(
            opt_frame,
            text=f"{self.config.focus_delay_ms} ms",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8",
        )
        self.delay_val_lbl.grid(row=1, column=1, sticky="e", padx=12, pady=4)

        self.delay_slider = ctk.CTkSlider(
            opt_frame,
            from_=20,
            to=400,
            number_of_steps=38,
            command=self._on_delay_change,
        )
        self.delay_slider.set(self.config.focus_delay_ms)
        self.delay_slider.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))

        # Post Paste Action
        post_lbl = ctk.CTkLabel(opt_frame, text="Post-Paste Key:", font=ctk.CTkFont(size=11))
        post_lbl.grid(row=3, column=0, sticky="w", padx=12, pady=4)

        self.post_combo = ctk.CTkComboBox(
            opt_frame,
            values=POST_ACTIONS,
            command=self._on_post_action_change,
            height=28,
            font=ctk.CTkFont(size=11),
        )
        self.post_combo.set(self.config.post_paste_action)
        self.post_combo.grid(row=3, column=1, sticky="ew", padx=12, pady=4)

        # Sound switch
        self.sound_switch = ctk.CTkSwitch(
            opt_frame,
            text="Sound Feedback (Beeps)",
            command=self._toggle_sound,
            font=ctk.CTkFont(size=11),
        )
        if self.config.sound_feedback:
            self.sound_switch.select()
        self.sound_switch.grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 12))

    # Event Handlers & Helpers
    def _toggle_always_on_top(self):
        self.config.always_on_top = bool(self.top_switch.get())
        self.attributes("-topmost", self.config.always_on_top)

    def _toggle_sound(self):
        self.config.sound_feedback = bool(self.sound_switch.get())

    def _on_delay_change(self, value):
        delay = int(value)
        self.config.focus_delay_ms = delay
        self.delay_val_lbl.configure(text=f"{delay} ms")

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

        # Checkbox for skip header
        skip_header_var = tk.BooleanVar(value=True)
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

        # Scroll to current index line
        if items:
            frac = curr_idx / max(1, len(items))
            self.queue_box.yview_moveto(max(0.0, frac - 0.1))

        # Update stats
        total = self.queue_mgr.total
        completed = self.queue_mgr.completed
        rem = self.queue_mgr.remaining

        self.stats_lbl.configure(
            text=f"Queue: {total} items | Completed: {completed} | Remaining: {rem}"
        )
        progress = completed / total if total > 0 else 0.0
        self.progress_bar.set(progress)

        # Update spotlight
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
    def _on_state_changed(self, is_active: bool):
        def _update():
            if is_active:
                self.toggle_btn.configure(
                    text="⏸ PAUSE AUTOMATION (F8)",
                    fg_color="#ef4444",
                    hover_color="#dc2626",
                )
                self._update_status("● ARMED & ACTIVE: Left-clicking external target will paste according to pattern.")
            else:
                self.toggle_btn.configure(
                    text="▶ START AUTOMATION (F8)",
                    fg_color="#10b981",
                    hover_color="#059669",
                )
                self._update_status("Paused. Press F8 or click Start to resume.")
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
            self._update_status("Queue finished! All items have been pasted.")
            messagebox.showinfo("Done", "All items in the queue have been successfully pasted!")
        self.after(0, _update)

    def _on_close(self):
        self.controller.stop_listeners()
        self.destroy()
