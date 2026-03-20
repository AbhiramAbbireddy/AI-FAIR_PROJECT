from src.skill_extractor import extract_skill_names, extract_skills


def test_extract_skill_names_dictionary_mode():
    text = (
        "Skills\n"
        "Python, SQL, Pandas, NumPy, Docker, Git\n"
        "Experience\n"
        "Built machine learning pipelines and REST APIs with FastAPI."
    )

    skills = extract_skill_names(text, use_ner=False, fast_mode=True)

    assert "python" in skills
    assert "sql" in skills
    assert "docker" in skills
    assert "fastapi" in skills


def test_extract_skills_returns_structured_entries():
    text = (
        "Technical Skills\n"
        "React, JavaScript, HTML, CSS\n"
        "Professional Experience\n"
        "Advanced React developer with strong JavaScript expertise."
    )

    skills = extract_skills(text, use_ner=False, fast_mode=True)

    canonical_names = [skill.canonical for skill in skills]
    assert "react" in canonical_names
    assert "javascript" in canonical_names
    assert any(skill.source_section.lower() == "skills" for skill in skills)


def test_extract_skill_names_normalizes_aliases_without_semantic_model():
    text = "Skills\nJS, ML, K8s, PyTorch"

    skills = extract_skill_names(text, use_ner=False, fast_mode=True)

    assert "javascript" in skills
    assert "machine learning" in skills
    assert "kubernetes" in skills
    assert "pytorch" in skills
