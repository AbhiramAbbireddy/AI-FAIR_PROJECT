from src.job_roles_database import (
    get_all_domains,
    get_all_role_names,
    get_job_role,
    get_roles_by_domain,
    load_job_roles,
    search_roles_by_skill,
)


def test_load_job_roles_returns_profiles():
    roles = load_job_roles()

    assert roles
    assert any(role.role == "Data Scientist" for role in roles)
    assert all(isinstance(role.core_skills, tuple) for role in roles)


def test_get_job_role_returns_enriched_profile():
    role = get_job_role("Data Scientist")

    assert role is not None
    assert role.domain == "Data Science"
    assert "python" in role.core_skills
    assert role.description


def test_get_roles_by_domain_filters_domain():
    roles = get_roles_by_domain("Software Engineering")

    assert roles
    assert all(role.domain == "Software Engineering" for role in roles)


def test_search_roles_by_skill_finds_matching_roles():
    roles = search_roles_by_skill("docker")
    role_names = {role.role for role in roles}

    assert "DevOps Engineer" in role_names


def test_get_all_role_names_and_domains_are_populated():
    role_names = get_all_role_names()
    domains = get_all_domains()

    assert "Frontend Developer" in role_names
    assert "Software Engineering" in domains
