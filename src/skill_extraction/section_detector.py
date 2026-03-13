"""
Resume section detector.
Identifies Skills, Experience, Projects, Education sections in resume text.
"""
import re

# Patterns that mark the beginning of common resume sections.
SECTION_PATTERNS = {
    "skills": [
        r"(?:technical\s+)?skills?",
        r"core\s+competenc(?:ies|e)",
        r"proficienc(?:ies|y)",
        r"tools?\s*(?:&|and)\s*technologies",
        r"technologies",
    ],
    "experience": [
        r"(?:work|professional|relevant)\s+experience",
        r"experience",
        r"employment\s+history",
        r"work\s+history",
    ],
    "projects": [
        r"projects?",
        r"personal\s+projects?",
        r"academic\s+projects?",
        r"portfolio",
    ],
    "education": [
        r"education(?:al)?\s*(?:background|qualifications?)?",
        r"academic\s+background",
        r"certifications?\s*(?:&|and)?\s*education",
    ],
    "certifications": [
        r"certifications?",
        r"licen[sc]es?\s*(?:&|and)?\s*certifications?",
        r"professional\s+development",
    ],
    "summary": [
        r"(?:professional\s+)?summary",
        r"objective",
        r"profile",
        r"about\s+me",
    ],
}

# Compile once.
_COMPILED: dict[str, re.Pattern] = {}
for section, patterns in SECTION_PATTERNS.items():
    combined = "|".join(patterns)
    # Match line that starts with the heading (possibly preceded by bullets/numbers).
    _COMPILED[section] = re.compile(
        rf"^\s*(?:[-•●▪]|\d+[.)]?)?\s*(?:{combined})\s*[:\-–—]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )


def detect_sections(text: str) -> dict[str, str]:
    """
    Split *text* into labelled sections.

    Returns a dict ``{section_name: section_text, ...}``.
    Any text before the first recognised heading is stored under ``"header"``.
    """
    # Find every heading match with its position.
    found: list[tuple[int, int, str]] = []  # (start, end, section_name)
    for section, pattern in _COMPILED.items():
        for m in pattern.finditer(text):
            found.append((m.start(), m.end(), section))

    if not found:
        return {"full_text": text}

    # Sort by position in the document.
    found.sort(key=lambda x: x[0])

    sections: dict[str, str] = {}

    # Anything before the first heading.
    if found[0][0] > 0:
        sections["header"] = text[: found[0][0]].strip()

    for idx, (start, end, name) in enumerate(found):
        # Section body runs from *end* of this heading to *start* of the next
        # heading (or end of document).
        body_end = found[idx + 1][0] if idx + 1 < len(found) else len(text)
        body = text[end:body_end].strip()
        # If the same section appears twice, concatenate.
        if name in sections:
            sections[name] += "\n" + body
        else:
            sections[name] = body

    return sections
