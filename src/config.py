"""Configuration settings and constants for Click-to-Paste."""

from dataclasses import dataclass
from typing import Literal

POST_ACTION_NONE = "None (Just Paste)"
POST_ACTION_TAB = "Press Tab"
POST_ACTION_ENTER = "Press Enter"
POST_ACTION_DOWN = "Press Down Arrow"

POST_ACTIONS = [
    POST_ACTION_NONE,
    POST_ACTION_TAB,
    POST_ACTION_ENTER,
    POST_ACTION_DOWN,
]

@dataclass
class AppConfig:
    focus_delay_ms: int = 80
    post_paste_action: str = POST_ACTION_NONE
    sound_feedback: bool = True
    always_on_top: bool = True
    hotkey_toggle: str = "F8"
    hotkey_stop: str = "Esc"
    default_pattern: str = "P, S"
