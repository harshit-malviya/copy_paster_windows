"""Global mouse and keyboard listener for handling Click-to-Paste automation."""

import ctypes
import os
import sys
import threading
import time
from typing import Callable, Optional

from pynput import keyboard, mouse
import pyperclip

from src.config import (
    POST_ACTION_DOWN,
    POST_ACTION_ENTER,
    POST_ACTION_NONE,
    POST_ACTION_TAB,
    AppConfig,
)
from src.pattern_engine import PatternEngine
from src.queue_manager import QueueManager

# Windows API for window and point detection
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def is_point_in_rect(x: int, y: int, rect: tuple) -> bool:
    """Checks if point (x, y) is inside (left, top, right, bottom)."""
    left, top, right, bottom = rect
    return left <= x <= right and top <= y <= bottom


class ClickPasteController:
    """Controls the global mouse/keyboard listeners, state, and paste execution."""

    def __init__(
        self,
        queue_mgr: QueueManager,
        pattern_eng: PatternEngine,
        config: AppConfig,
        on_state_change: Optional[Callable[[bool], None]] = None,
        on_item_pasted: Optional[Callable[[str, int, int], None]] = None,
        on_step_updated: Optional[Callable[[], None]] = None,
        on_queue_finished: Optional[Callable[[], None]] = None,
    ):
        self.queue_mgr = queue_mgr
        self.pattern_eng = pattern_eng
        self.config = config

        self.on_state_change = on_state_change
        self.on_item_pasted = on_item_pasted
        self.on_step_updated = on_step_updated
        self.on_queue_finished = on_queue_finished

        self.is_active: bool = False
        self._app_window_hwnd: Optional[int] = None
        self._app_window_bbox_fn: Optional[Callable[[], Optional[tuple]]] = None

        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._kb_controller = keyboard.Controller()
        self._lock = threading.Lock()
        self._pasting = False

    def set_app_window_getter(self, bbox_fn: Callable[[], Optional[tuple]], hwnd: Optional[int] = None):
        """Register the GUI window coordinates & handle to avoid clicking inside app."""
        self._app_window_bbox_fn = bbox_fn
        self._app_window_hwnd = hwnd

    def start_listeners(self):
        """Starts background mouse and keyboard listeners."""
        self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

        self._keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

    def stop_listeners(self):
        """Stops background listeners."""
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()

    def set_active(self, active: bool):
        """Toggles active state."""
        with self._lock:
            self.is_active = active
        if self.on_state_change:
            self.on_state_change(self.is_active)
        self._play_sound(800 if active else 400, 50)

    def toggle_active(self):
        self.set_active(not self.is_active)

    def _play_sound(self, frequency: int, duration_ms: int):
        if not self.config.sound_feedback or sys.platform != "win32":
            return
        def _beep():
            try:
                import winsound
                winsound.Beep(frequency, duration_ms)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

    def _on_key_press(self, key):
        """Handles hotkey triggers (F8: toggle, Esc: stop)."""
        try:
            if key == keyboard.Key.f8:
                self.toggle_active()
            elif key == keyboard.Key.esc:
                if self.is_active:
                    self.set_active(False)
        except Exception:
            pass

    def _is_click_inside_app(self, x: int, y: int) -> bool:
        """Determines if the click occurred inside the application window."""
        try:
            # 1. Check Tkinter bounding box if provided
            if self._app_window_bbox_fn:
                bbox = self._app_window_bbox_fn()
                if bbox and is_point_in_rect(x, y, bbox):
                    return True

            # 2. Check Windows HWND under cursor
            if sys.platform == "win32" and self._app_window_hwnd:
                pt = POINT(int(x), int(y))
                hwnd_under_cursor = ctypes.windll.user32.WindowFromPoint(pt)
                # Check root owner/parent of the window under cursor
                curr = hwnd_under_cursor
                while curr:
                    if curr == self._app_window_hwnd:
                        return True
                    parent = ctypes.windll.user32.GetParent(curr)
                    if not parent or parent == curr:
                        break
                    curr = parent
        except Exception:
            pass
        return False

    def _on_mouse_click(self, x, y, button, pressed):
        """Called by pynput on any mouse button event."""
        # We only care when left button is RELEASED or PRESSED.
        # Pressed is best to initiate paste immediately after focus delay.
        if not pressed or button != mouse.Button.left:
            return

        if not self.is_active:
            return

        # Check if click is inside our own window
        if self._is_click_inside_app(x, y):
            return

        # Avoid re-entrancy
        if self._pasting:
            return

        # Run paste or skip in background thread so mouse hook isn't blocked
        threading.Thread(target=self._process_click_action, daemon=True).start()

    def _process_click_action(self):
        with self._lock:
            if not self.is_active or self._pasting:
                return
            self._pasting = True

        try:
            action = self.pattern_eng.get_current_action()

            if action == "S":
                # Skip step
                self.pattern_eng.advance()
                self._play_sound(600, 30)
                if self.on_step_updated:
                    self.on_step_updated()
                return

            # Action is 'P' (Paste)
            if not self.queue_mgr.has_next():
                self.set_active(False)
                if self.on_queue_finished:
                    self.on_queue_finished()
                return

            item_to_paste = self.queue_mgr.get_current_item()
            if item_to_paste is None:
                self.set_active(False)
                return

            # Allow target window time to focus after the mouse click
            delay_sec = max(0.01, self.config.focus_delay_ms / 1000.0)
            time.sleep(delay_sec)

            # Copy to clipboard and simulate Ctrl+V
            pyperclip.copy(item_to_paste)

            with self._kb_controller.pressed(keyboard.Key.ctrl):
                self._kb_controller.press('v')
                self._kb_controller.release('v')

            time.sleep(0.04)

            # Handle post-paste action
            post_act = self.config.post_paste_action
            if post_act == POST_ACTION_TAB:
                self._kb_controller.press(keyboard.Key.tab)
                self._kb_controller.release(keyboard.Key.tab)
            elif post_act == POST_ACTION_ENTER:
                self._kb_controller.press(keyboard.Key.enter)
                self._kb_controller.release(keyboard.Key.enter)
            elif post_act == POST_ACTION_DOWN:
                self._kb_controller.press(keyboard.Key.down)
                self._kb_controller.release(keyboard.Key.down)

            # Play high pitch confirmation beep for paste
            self._play_sound(1200, 35)

            # Advance queue and pattern
            consumed = self.queue_mgr.advance()
            self.pattern_eng.advance()

            if self.on_item_pasted and consumed is not None:
                self.on_item_pasted(consumed, self.queue_mgr.completed, self.queue_mgr.total)

            if self.on_step_updated:
                self.on_step_updated()

            # Check if queue finished
            if not self.queue_mgr.has_next():
                self.set_active(False)
                if self.on_queue_finished:
                    self.on_queue_finished()

        finally:
            self._pasting = False
