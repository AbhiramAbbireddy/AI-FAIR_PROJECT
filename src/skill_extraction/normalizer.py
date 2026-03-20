"""
Skill normalizer: deduplication, alias resolution, canonical mapping, and semantic fallback.
"""
from __future__ import annotations

import re
from typing import Optional
from src.config.settings import SKILL_ALIASES, SKILL_DEDUP_GROUPS, SBERT_MODEL


# Build a reverse lookup:  variant → canonical name.
_VARIANT_TO_CANONICAL: dict[str, str] = {}
for canonical, variants in SKILL_DEDUP_GROUPS.items():
    _VARIANT_TO_CANONICAL[canonical.lower()] = canonical.lower()
    for v in variants:
        _VARIANT_TO_CANONICAL[v.lower()] = canonical.lower()

# Also integrate alias map.
for alias, canonical in SKILL_ALIASES.items():
    _VARIANT_TO_CANONICAL[alias.lower()] = canonical.lower()

# Lazy-loaded semantic matcher
_semantic_matcher = None
_skill_vocab_embeddings = None


def _get_semantic_matcher():
    """Lazy-load SBERT model for semantic matching."""
    global _semantic_matcher
    if _semantic_matcher is None:
        try:
            from sentence_transformers import SentenceTransformer, util
            _semantic_matcher = SentenceTransformer(SBERT_MODEL)
        except Exception as e:
            print(f"Warning: Could not load semantic matcher: {e}")
            _semantic_matcher = False  # Disabled flag
    return _semantic_matcher if _semantic_matcher is not False else None


def _get_skill_vocab_embeddings():
    """Get pre-computed embeddings for all skill vocabulary."""
    global _skill_vocab_embeddings
    if _skill_vocab_embeddings is None:
        try:
            import pandas as pd
            from src.config.settings import SKILLS_VOCAB_PATH
            
            df = pd.read_csv(SKILLS_VOCAB_PATH)
            vocab_skills = df['skill'].str.lower().str.strip().tolist()
            
            matcher = _get_semantic_matcher()
            if matcher:
                _skill_vocab_embeddings = {
                    'skills': vocab_skills,
                    'embeddings': matcher.encode(vocab_skills, convert_to_tensor=True)
                }
        except Exception as e:
            print(f"Warning: Could not compute skill embeddings: {e}")
            _skill_vocab_embeddings = False
    
    return _skill_vocab_embeddings if _skill_vocab_embeddings is not False else None


def normalize_skill(skill: str, allow_semantic_fallback: bool = False) -> str:
    """
    Return the canonical form for *skill* using:
    1. Exact matching (aliases + dedup groups)
    2. Semantic similarity (only if explicitly enabled)
    """
    s = skill.strip().lower()
    s = re.sub(r"\s+", " ", s)
    
    # Try exact match first
    if s in _VARIANT_TO_CANONICAL:
        return _VARIANT_TO_CANONICAL[s]
    
    # Try semantic fallback if enabled
    if allow_semantic_fallback and len(s) > 2:  # Only for longer skills
        matched = _semantic_match(skill)
        if matched:
            return matched
    
    return s


def _semantic_match(skill: str, threshold: float = 0.75) -> Optional[str]:
    """
    Use semantic similarity to find matching skill from vocabulary.
    Returns canonical skill name if match found, None otherwise.
    """
    try:
        matcher = _get_semantic_matcher()
        embeddings = _get_skill_vocab_embeddings()
        
        if not matcher or not embeddings:
            return None
        
        from sentence_transformers import util
        
        # Encode the query skill
        query_embedding = matcher.encode(skill, convert_to_tensor=True)
        
        # Find most similar skills
        similarities = util.pytorch_cos_sim(query_embedding, embeddings['embeddings'])[0]
        max_sim, max_idx = similarities.max(dim=0)
        
        if max_sim.item() >= threshold:
            matched_skill = embeddings['skills'][max_idx.item()]
            # Try to further normalize the matched skill
            canonical = _VARIANT_TO_CANONICAL.get(matched_skill, matched_skill)
            return canonical
    except Exception as e:
        # Silently fail if semantic matching has issues
        pass
    
    return None


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
