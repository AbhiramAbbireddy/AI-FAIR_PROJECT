"""
Skill normalizer: deduplication, alias resolution, canonical mapping.
"""
from __future__ import annotations

import re
from src.config.settings import SKILL_ALIASES, SKILL_DEDUP_GROUPS


# Build a reverse lookup:  variant → canonical name.
_VARIANT_TO_CANONICAL: dict[str, str] = {}
for canonical, variants in SKILL_DEDUP_GROUPS.items():
    _VARIANT_TO_CANONICAL[canonical.lower()] = canonical.lower()
    for v in variants:
        _VARIANT_TO_CANONICAL[v.lower()] = canonical.lower()

# Also integrate alias map.
for alias, canonical in SKILL_ALIASES.items():
    _VARIANT_TO_CANONICAL[alias.lower()] = canonical.lower()


def normalize_skill(skill: str) -> str:
    """Return the canonical form for *skill*, or lower-cased original."""
    s = skill.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return _VARIANT_TO_CANONICAL.get(s, s)


def deduplicate(skills: list[str]) -> list[str]:
    """Deduplicate keeping first-seen order, using canonical forms."""
    seen: set[str] = set()
    result: list[str] = []
    for s in skills:
        canon = normalize_skill(s)
        if canon not in seen:
            seen.add(canon)
            result.append(canon)
    return result
