"""Pattern sequence engine for handling Click-to-Paste skip behaviors."""

from typing import List, Tuple


class PatternEngine:
    """Manages custom click patterns such as 'P, S' (Paste, Skip)."""

    def __init__(self, pattern_str: str = "P, S"):
        self.raw_pattern: str = ""
        self.steps: List[str] = []
        self.current_step_index: int = 0
        self.set_pattern(pattern_str)

    def set_pattern(self, pattern_str: str) -> bool:
        """Parses and validates a pattern string (e.g. 'P, S', 'P, S, S', 'P').

        Returns True if valid, False otherwise.
        """
        cleaned = pattern_str.upper().replace(" ", "").replace(";", ",").replace("-", ",")
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]

        valid_steps = []
        for part in parts:
            if part in ("P", "PASTE"):
                valid_steps.append("P")
            elif part in ("S", "SKIP"):
                valid_steps.append("S")
            else:
                # If characters are concatenated like "PSPS"
                for ch in part:
                    if ch == "P":
                        valid_steps.append("P")
                    elif ch == "S":
                        valid_steps.append("S")
                    else:
                        return False

        if not valid_steps:
            return False

        # Pattern must contain at least one Paste action
        if "P" not in valid_steps:
            return False

        self.raw_pattern = pattern_str
        self.steps = valid_steps
        self.current_step_index = 0
        return True

    def get_current_action(self) -> str:
        """Returns 'P' (Paste) or 'S' (Skip) for current step."""
        if not self.steps:
            return "P"
        return self.steps[self.current_step_index % len(self.steps)]

    def advance(self) -> str:
        """Advances to next step and returns the action that was just taken."""
        if not self.steps:
            return "P"
        action = self.get_current_action()
        self.current_step_index = (self.current_step_index + 1) % len(self.steps)
        return action

    def reset(self) -> None:
        """Resets pattern index to beginning."""
        self.current_step_index = 0

    def get_status_summary(self) -> Tuple[int, int, str]:
        """Returns (current_step_1_based, total_steps, current_action_name)."""
        if not self.steps:
            return 1, 1, "Paste"
        total = len(self.steps)
        curr = (self.current_step_index % total) + 1
        action = "PASTE" if self.get_current_action() == "P" else "SKIP"
        return curr, total, action
