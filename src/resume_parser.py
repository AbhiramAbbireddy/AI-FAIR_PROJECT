"""
Canonical resume parsing component for FAIR-PATH.

This module is intentionally small and dependency-light so the rest of the
project can rely on a single source of truth for:
    - text extraction
    - email extraction
    - phone extraction
    - experience estimation
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import pdfplumber

from src.models.schemas import ResumeParseResult


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(
    r"(?:(?:\+?\d{1,3}[\s\-().]*)?(?:\d[\s\-().]*){10,14}\d)"
)

EXPERIENCE_PATTERNS = (
    re.compile(
        r"(?P<years>\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        re.IGNORECASE,
    ),
    re.compile(
        r"experience\s*[:\-]?\s*(?P<years>\d{1,2}(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"over\s+(?P<years>\d{1,2}(?:\.\d+)?)\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
)


def _read_pdf(path: str) -> str:
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def extract_text_from_pdf(source) -> str:
    """Extract text from a file path or Streamlit/FastAPI-style file object."""
    if hasattr(source, "getvalue"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(source.getvalue())
            tmp_path = tmp.name
        try:
            return _read_pdf(tmp_path)
        finally:
            os.unlink(tmp_path)
    return _read_pdf(str(source))


def extract_text_from_docx(path: str) -> str:
    import docx

    document = docx.Document(path)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def extract_text(source, filename: str = "") -> str:
    """Auto-detect the resume format and return plain text."""
    ext = Path(filename).suffix.lower() if filename else ""
    if ext == ".docx":
        return extract_text_from_docx(source if isinstance(source, str) else source)
    if ext == ".pdf" or not ext:
        return extract_text_from_pdf(source)
    if hasattr(source, "read"):
        return source.read().decode("utf-8", errors="ignore")
    with open(source, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def extract_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text or "")
    return match.group(0) if match else None


def _normalize_phone(raw_phone: str) -> str | None:
    digits_only = re.sub(r"\D", "", raw_phone)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return None

    compact = re.sub(r"\s+", " ", raw_phone).strip(" ,;")
    if raw_phone.strip().startswith("+"):
        return compact
    return f"+{digits_only}" if len(digits_only) > 10 else digits_only


def extract_phone(text: str) -> str | None:
    for match in PHONE_PATTERN.finditer(text or ""):
        normalized = _normalize_phone(match.group(0))
        if normalized:
            return normalized
    return None


def extract_experience_years(text: str) -> int | None:
    years_found: list[float] = []
    for pattern in EXPERIENCE_PATTERNS:
        for match in pattern.finditer(text or ""):
            try:
                years_found.append(float(match.group("years")))
            except (TypeError, ValueError):
                continue

    if not years_found:
        return None

    return int(max(years_found))


def parse_resume(source, filename: str = "") -> ResumeParseResult:
    """Parse a resume file or file-like object into structured core metadata."""
    text = extract_text(source, filename=filename)
    return ResumeParseResult(
        text=text,
        email=extract_email(text),
        phone=extract_phone(text),
        experience_years=extract_experience_years(text),
    )
