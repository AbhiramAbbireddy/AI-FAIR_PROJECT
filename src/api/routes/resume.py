"""
Resume analysis endpoints.
"""
from __future__ import annotations

import os
import tempfile

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from src.skill_extraction.extractor import extract_skills, extract_text
from src.models.schemas import ExtractedSkill

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/extract-skills", response_model=list[ExtractedSkill])
async def extract_skills_endpoint(
    file: UploadFile = File(...),
    use_ner: bool = Form(True),
):
    """Upload a resume (PDF/DOCX/TXT) and extract skills."""
    allowed_ext = {".pdf", ".docx", ".txt"}
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in allowed_ext:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    # Write to temp file
    suffix = ext or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = extract_text(tmp_path, filename=file.filename or "")
        skills = extract_skills(text, use_ner=use_ner)
        return skills
    finally:
        os.unlink(tmp_path)


@router.post("/parse-text")
async def parse_resume_text(text: str = Form(...)):
    """Parse raw resume text and extract skills."""
    skills = extract_skills(text, use_ner=True)
    return {"skills": skills, "count": len(skills)}
