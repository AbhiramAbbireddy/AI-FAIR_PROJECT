"""
Canonical skill extraction component for FAIR-PATH.

This module is the public entrypoint for Component 2. It wraps the
implementation inside ``src.skill_extraction`` and exposes a stable API
for the Streamlit app, FastAPI routes, and future evaluation scripts.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.models.schemas import ExtractedSkill
from src.skill_extraction.extractor import (
    extract_skill_names as _extract_skill_names,
    extract_skills as _extract_skills,
)


@dataclass(slots=True)
class SkillExtractionConfig:
    use_ner: bool = True
    fast_mode: bool = True


class SkillExtractor:
    """Canonical wrapper around the resume skill extraction pipeline."""

    def __init__(self, config: SkillExtractionConfig | None = None):
        self.config = config or SkillExtractionConfig()

    def extract(self, text: str) -> list[ExtractedSkill]:
        return _extract_skills(
            text,
            use_ner=self.config.use_ner,
            fast_mode=self.config.fast_mode,
        )

    def extract_names(self, text: str) -> list[str]:
        return _extract_skill_names(
            text,
            use_ner=self.config.use_ner,
            fast_mode=self.config.fast_mode,
        )


def extract_skills(
    text: str,
    *,
    use_ner: bool = True,
    fast_mode: bool = True,
) -> list[ExtractedSkill]:
    """Public functional API for Component 2."""
    return SkillExtractor(
        SkillExtractionConfig(use_ner=use_ner, fast_mode=fast_mode)
    ).extract(text)


def extract_skill_names(
    text: str,
    *,
    use_ner: bool = True,
    fast_mode: bool = True,
) -> list[str]:
    """Return canonical skill names only."""
    return SkillExtractor(
        SkillExtractionConfig(use_ner=use_ner, fast_mode=fast_mode)
    ).extract_names(text)
