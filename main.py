"""Main entry point for Click-to-Paste Automation GUI."""

import ctypes
import os
import sys

# Ensure DPI awareness on Windows for crisp high-resolution UI
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from src.config import AppConfig
from src.gui import ClickPasteApp
from src.pattern_engine import PatternEngine
from src.queue_manager import QueueManager

# Close bootloader splash if present
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass


def main():
    config = AppConfig()
    queue_mgr = QueueManager()
    pattern_eng = PatternEngine(config.default_pattern)

    app = ClickPasteApp(queue_mgr=queue_mgr, pattern_eng=pattern_eng, config=config)
    app.mainloop()


if __name__ == "__main__":
    main()
