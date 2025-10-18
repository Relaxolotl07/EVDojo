from __future__ import annotations

import re
from typing import Tuple
from .config import config


def is_goal_allowed(goal: str) -> Tuple[bool, str | None]:
    low = goal.lower()
    for kw in config.blocked_goal_keywords:
        if kw in low:
            return False, f"Blocked by keyword: {kw}"
    return True, None


def sanitize_for_judging(text: str) -> str:
    # simple redactions are handled by adapter; keep as placeholder
    # Remove excessive whitespace
    return re.sub(r"\s+", " ", text).strip()

