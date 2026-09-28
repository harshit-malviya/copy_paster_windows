"""Queue Manager for holding and iterating over data to be pasted."""

import csv
import os
from typing import List, Optional, Tuple


class QueueManager:
    """Manages the list of items to paste and track progress."""

    def __init__(self):
        self.items: List[str] = []
        self.current_index: int = 0

    def load_from_text(self, text: str, skip_header: bool = False) -> int:
        """Loads items from a multiline string. Returns count of loaded items."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if skip_header and lines:
            lines = lines[1:]
        self.items = lines
        self.current_index = 0
        return len(self.items)

    def load_from_file(self, filepath: str) -> int:
        """Loads items from .txt, .csv, or .xlsx file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        loaded_items: List[str] = []

        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                loaded_items = [line.strip() for line in f if line.strip()]

        elif ext == ".csv":
            with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        val = row[0].strip()
                        if val:
                            loaded_items.append(val)

        elif ext in (".xlsx", ".xlsm"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
                sheet = wb.active
                for row in sheet.iter_rows(values_only=True):
                    if row and row[0] is not None:
                        val = str(row[0]).strip()
                        if val:
                            loaded_items.append(val)
                wb.close()
            except ImportError:
                raise ImportError("openpyxl is required to load Excel files (.xlsx). Please install openpyxl.")

        else:
            # Fallback to plain text read
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                loaded_items = [line.strip() for line in f if line.strip()]

        self.items = loaded_items
        self.current_index = 0
        return len(self.items)

    def get_current_item(self) -> Optional[str]:
        """Returns the item currently pointed to, or None if queue is exhausted or empty."""
        if 0 <= self.current_index < len(self.items):
            return self.items[self.current_index]
        return None

    def advance(self) -> Optional[str]:
        """Advances pointer to next item and returns the item just consumed."""
        if 0 <= self.current_index < len(self.items):
            item = self.items[self.current_index]
            self.current_index += 1
            return item
        return None

    def reset(self) -> None:
        """Resets the queue pointer to 0."""
        self.current_index = 0

    def jump_to(self, index: int) -> bool:
        """Jumps to a specific 0-based index."""
        if 0 <= index <= len(self.items):
            self.current_index = index
            return True
        return False

    def clear(self) -> None:
        """Clears all items in the queue."""
        self.items.clear()
        self.current_index = 0

    def has_next(self) -> bool:
        """Checks if there are remaining items to paste."""
        return self.current_index < len(self.items)

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def remaining(self) -> int:
        return max(0, len(self.items) - self.current_index)

    @property
    def completed(self) -> int:
        return min(self.current_index, len(self.items))
