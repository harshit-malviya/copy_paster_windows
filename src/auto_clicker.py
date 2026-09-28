"""Auto-clicker engine for executing sequential clicks and pastes at defined screen coordinates."""

import sys
import threading
import time
from typing import Callable, Optional

from pynput import keyboard, mouse
import pyperclip

from src.config import (
    ASSIGN_SEQUENTIAL,
    PASS_SINGLE,
    POINT_ACTION_CLICK,
    POINT_ACTION_DOUBLE_CLICK,
    POINT_ACTION_PASTE,
    POST_ACTION_DOWN,
    POST_ACTION_ENTER,
    POST_ACTION_NONE,
    POST_ACTION_TAB,
    AppConfig,
)
from src.queue_manager import QueueManager


class AutoClicker:
    """Manages the automatic execution of click/paste sequences at defined coordinates."""

    def __init__(
        self,
        queue_mgr: QueueManager,
        config: AppConfig,
        on_state_change: Optional[Callable[[bool], None]] = None,
        on_item_processed: Optional[Callable[[str, int, int], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ):
        self.queue_mgr = queue_mgr
        self.config = config
        self.on_state_change = on_state_change
        self.on_item_processed = on_item_processed
        self.on_finished = on_finished

        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._mouse_ctl = mouse.Controller()
        self._kb_ctl = keyboard.Controller()

    def start(self) -> bool:
        """Starts the auto-clicking loop in a background thread."""
        if self.is_running:
            return True

        if not self.config.auto_points:
            return False

        if not self.queue_mgr.has_next():
            return False

        self._stop_event.clear()
        self.is_running = True

        if self.on_state_change:
            self.on_state_change(True)

        self._play_sound(1000, 60)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stops/pauses the auto-clicking loop immediately."""
        if not self.is_running:
            return

        self._stop_event.set()
        self.is_running = False

        if self.on_state_change:
            self.on_state_change(False)

        self._play_sound(500, 60)

    def toggle(self) -> bool:
        if self.is_running:
            self.stop()
            return False
        else:
            return self.start()

    def _sleep_interruptible(self, seconds: float) -> bool:
        """Sleeps in small chunks while checking for stop event. Returns False if interrupted."""
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self._stop_event.is_set():
                return False
            time.sleep(min(0.04, end_time - time.time()))
        return not self._stop_event.is_set()

    def _play_sound(self, freq: int, duration_ms: int):
        if not self.config.sound_feedback or sys.platform != "win32":
            return
        def _beep():
            try:
                import winsound
                winsound.Beep(freq, duration_ms)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

    def _run_loop(self):
        try:
            # Initial brief grace period (0.4s) to allow user to switch context if needed
            if not self._sleep_interruptible(0.4):
                return

            is_sequential = (self.config.auto_item_assignment == ASSIGN_SEQUENTIAL)
            is_single_pass = (self.config.auto_pass_mode == PASS_SINGLE)

            while not self._stop_event.is_set() and self.queue_mgr.has_next():
                # If repeat mode, take the item for this entire pass
                batch_item = None
                if not is_sequential:
                    batch_item = self.queue_mgr.get_current_item()
                    if batch_item is None:
                        break

                # Execute the point sequence for this pass
                for pt in self.config.auto_points:
                    if self._stop_event.is_set():
                        return

                    # 1. Move mouse to target coordinates
                    self._mouse_ctl.position = (int(pt.x), int(pt.y))
                    time.sleep(0.04)

                    # 2. Perform action
                    if pt.action == POINT_ACTION_PASTE:
                        if is_sequential:
                            if not self.queue_mgr.has_next():
                                # No more items to paste
                                return
                            item_to_paste = self.queue_mgr.get_current_item()
                        else:
                            item_to_paste = batch_item

                        if item_to_paste is None:
                            return

                        # Click to focus
                        self._mouse_ctl.click(mouse.Button.left, 1)

                        # Focus delay
                        delay_sec = max(0.02, self.config.focus_delay_ms / 1000.0)
                        if not self._sleep_interruptible(delay_sec):
                            return

                        # Copy to clipboard & paste
                        pyperclip.copy(item_to_paste)
                        with self._kb_ctl.pressed(keyboard.Key.ctrl):
                            self._kb_ctl.press('v')
                            self._kb_ctl.release('v')

                        time.sleep(0.03)

                        # Post-paste action
                        post_act = self.config.post_paste_action
                        if post_act == POST_ACTION_TAB:
                            self._kb_ctl.press(keyboard.Key.tab)
                            self._kb_ctl.release(keyboard.Key.tab)
                        elif post_act == POST_ACTION_ENTER:
                            self._kb_ctl.press(keyboard.Key.enter)
                            self._kb_ctl.release(keyboard.Key.enter)
                        elif post_act == POST_ACTION_DOWN:
                            self._kb_ctl.press(keyboard.Key.down)
                            self._kb_ctl.release(keyboard.Key.down)

                        self._play_sound(1300, 30)

                        if is_sequential:
                            consumed = self.queue_mgr.advance()
                            if self.on_item_processed and consumed is not None:
                                self.on_item_processed(consumed, self.queue_mgr.completed, self.queue_mgr.total)

                    elif pt.action == POINT_ACTION_CLICK:
                        self._mouse_ctl.click(mouse.Button.left, 1)
                        self._play_sound(900, 20)

                    elif pt.action == POINT_ACTION_DOUBLE_CLICK:
                        self._mouse_ctl.click(mouse.Button.left, 2)
                        self._play_sound(900, 20)

                    # Wait per-point delay
                    if pt.delay_after_ms > 0:
                        if not self._sleep_interruptible(pt.delay_after_ms / 1000.0):
                            return

                # If repeat mode, advance queue once at the end of the pass
                if not is_sequential and batch_item is not None:
                    consumed = self.queue_mgr.advance()
                    if self.on_item_processed and consumed is not None:
                        self.on_item_processed(consumed, self.queue_mgr.completed, self.queue_mgr.total)

                # If single pass, stop after one complete pass through all points!
                if is_single_pass:
                    break

                # If loop sequence and more items exist, wait interval delay before next pass
                if self.queue_mgr.has_next():
                    item_delay = max(0.1, self.config.auto_item_delay_sec)
                    if not self._sleep_interruptible(item_delay):
                        return

        finally:
            self.is_running = False
            if self.on_state_change:
                self.on_state_change(False)

            if not self._stop_event.is_set():
                if self.on_finished:
                    self.on_finished()
