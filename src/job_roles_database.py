"""
Canonical job role database component for FAIR-PATH.

This module exposes Component 3 as a stable API:
    - load all role profiles
    - query by domain
    - query by skill
    - fetch role names/domains
"""
from __future__ import annotations

from dataclasses import dataclass

from src.role_mapping.role_database import COMPREHENSIVE_JOB_DATABASE


@dataclass(frozen=True, slots=True)
class JobRoleProfile:
    role: str
    domain: str
    core_skills: tuple[str, ...]
    optional_skills: tuple[str, ...]
    description: str
    level: str = "Not specified"


def _normalize_skills(skills: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if not skills:
        return ()
    seen: set[str] = set()
    normalized: list[str] = []
    for skill in skills:
        cleaned = str(skill).strip().lower()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return tuple(normalized)


def _default_description(entry: dict) -> str:
    role = entry.get("role", "Unknown Role")
    domain = entry.get("domain", "General")
    core = _normalize_skills(entry.get("core_skills", []))
    if not core:
        return f"{role} role in {domain}."
    top_skills = ", ".join(core[:4])
    return f"{role} role in {domain} focused on {top_skills}."


def _to_profile(entry: dict) -> JobRoleProfile:
    return JobRoleProfile(
        role=str(entry.get("role", "")).strip(),
        domain=str(entry.get("domain", "General")).strip(),
        core_skills=_normalize_skills(entry.get("core_skills", [])),
        optional_skills=_normalize_skills(entry.get("optional_skills", [])),
        description=str(entry.get("description") or _default_description(entry)).strip(),
        level=str(entry.get("level", "Not specified")).strip(),
    )


def load_job_roles() -> list[JobRoleProfile]:
    """Return the full canonical job role database."""
    return [_to_profile(entry) for entry in COMPREHENSIVE_JOB_DATABASE]


def get_job_role(role_name: str) -> JobRoleProfile | None:
    role_name = role_name.strip().lower()
    for role in load_job_roles():
        if role.role.lower() == role_name:
            return role
    return None


def get_roles_by_domain(domain: str) -> list[JobRoleProfile]:
    domain = domain.strip().lower()
    return [role for role in load_job_roles() if role.domain.lower() == domain]


def get_all_role_names() -> list[str]:
    return [role.role for role in load_job_roles()]


def get_all_domains() -> list[str]:
    return sorted({role.domain for role in load_job_roles()})


def search_roles_by_skill(skill: str) -> list[JobRoleProfile]:
    skill = skill.strip().lower()
    results: list[JobRoleProfile] = []
    for role in load_job_roles():
        if skill in role.core_skills or skill in role.optional_skills:
            results.append(role)
    return results
