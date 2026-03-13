"""
Proficiency-level detector for extracted skills.
Looks at contextual clues near a skill mention in the resume text.
"""
from __future__ import annotations

import re
from src.config.settings import PROFICIENCY_KEYWORDS


def _window(text: str, skill: str, radius: int = 120) -> str:
    """Return a text window around the first occurrence of *skill*."""
    idx = text.lower().find(skill.lower())
    if idx == -1:
        return ""
    start = max(0, idx - radius)
    end = min(len(text), idx + len(skill) + radius)
    return text[start:end].lower()


def detect_proficiency(text: str, skill: str) -> str:
    """
    Return ``"advanced"``, ``"intermediate"``, or ``"basic"``
    based on contextual keywords near *skill* in *text*.
    Default is ``"intermediate"``.
    """
    window = _window(text, skill)
    if not window:
        return "intermediate"

    for level in ("advanced", "basic", "intermediate"):
        for kw in PROFICIENCY_KEYWORDS[level]:
            if re.search(r"\b" + re.escape(kw) + r"\b", window):
                return level

    return "intermediate"
