"""Configuration settings and constants for Click-to-Paste and Auto-Clicker."""

from dataclasses import dataclass, field
from typing import List

# Post-paste keyboard actions
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

# Auto-Click point actions
POINT_ACTION_PASTE = "Click & Paste Item"
POINT_ACTION_CLICK = "Just Click"
POINT_ACTION_DOUBLE_CLICK = "Double Click"

POINT_ACTIONS = [
    POINT_ACTION_PASTE,
    POINT_ACTION_CLICK,
    POINT_ACTION_DOUBLE_CLICK,
]


@dataclass
class ClickPoint:
    x: int
    y: int
    action: str = POINT_ACTION_PASTE
    delay_after_ms: int = 200


@dataclass
class AppConfig:
    # Operating mode: "manual" or "auto"
    mode: str = "manual"

    # Manual mode settings
    focus_delay_ms: int = 80
    post_paste_action: str = POST_ACTION_NONE
    sound_feedback: bool = True
    always_on_top: bool = True
    hotkey_toggle: str = "F8"
    hotkey_stop: str = "Esc"
    hotkey_capture: str = "F7"
    default_pattern: str = "P, S"

    # Auto-clicker mode settings
    auto_item_delay_sec: float = 1.0
    auto_points: List[ClickPoint] = field(default_factory=list)
