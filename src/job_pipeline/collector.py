"""
Job Data Collection Pipeline
============================
Collects job postings from multiple API sources, normalises them
into a standard schema, and stores them.

Supported sources:
    - **JSearch API** (RapidAPI) – preferred
    - **Adzuna API**
    - **Static CSV** fallback (existing Kaggle dataset)

Usage::

    collector = JobCollector()
    jobs = collector.search("python developer", location="remote", max_results=50)
    collector.save(jobs)
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import urllib.parse
from datetime import datetime
from typing import Optional

import pandas as pd

from src.config.settings import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_BASE_URL,
    JOBS_DB_PATH,
    JOBS_PARSED_PATH,
    JSEARCH_API_KEY,
    JSEARCH_BASE_URL,
    REMOTIVE_BASE_URL,
    SERPAPI_KEY,
)
from src.models.schemas import JobPosting
from src.skill_extraction.extractor import _dict_match, _get_skill_vocab

# ---------------------------------------------------------------------------
# JSearch API (RapidAPI)
# ---------------------------------------------------------------------------


def _jsearch_query(
    query: str,
    location: str = "",
    max_results: int = 20,
    remote_only: bool = False,
) -> list[JobPosting]:
    """Fetch jobs from JSearch API."""
    if not JSEARCH_API_KEY:
        return []

    try:
        import requests
    except ImportError:
        return []

    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {
        "query": f"{query} in {location}" if location else query,
        "num_pages": str(max(1, max_results // 10)),
        "date_posted": "month",
    }
    if remote_only:
        params["remote_jobs_only"] = "true"

    url = f"{JSEARCH_BASE_URL}/search"
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []
    data = resp.json().get("data", [])

    vocab = _get_skill_vocab()
    postings: list[JobPosting] = []
    for item in data[:max_results]:
        desc = item.get("job_description", "")
        skills = _dict_match(desc, vocab)
        jid = item.get("job_id", hashlib.sha256(desc[:200].encode()).hexdigest()[:12])
        postings.append(
            JobPosting(
                job_id=str(jid),
                title=item.get("job_title", "Unknown"),
                company=item.get("employer_name", "Unknown"),
                description=desc,
                required_skills=skills,
                preferred_skills=[],
                location=item.get("job_city", "") or item.get("job_country", "Unknown"),
                salary_min=item.get("job_min_salary"),
                salary_max=item.get("job_max_salary"),
                remote=item.get("job_is_remote", False),
                experience_level=item.get("job_required_experience", {}).get(
                    "experience_level", "Not specified"
                )
                if isinstance(item.get("job_required_experience"), dict)
                else "Not specified",
                posted_date=item.get("job_posted_at_datetime_utc", ""),
                source="jsearch",
            )
        )
    return postings


# ---------------------------------------------------------------------------
# Adzuna API
# ---------------------------------------------------------------------------


def _adzuna_query(
    query: str,
    location: str = "us",
    max_results: int = 20,
) -> list[JobPosting]:
    """Fetch jobs from Adzuna API."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return []

    try:
        import requests
    except ImportError:
        return []

    country = location.lower()[:2] if location else "us"
    safe_query = urllib.parse.quote_plus(query)
    url = (
        f"{ADZUNA_BASE_URL}/{country}/search/1"
        f"?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}"
        f"&results_per_page={max_results}&what={safe_query}"
    )

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []
    results = resp.json().get("results", [])

    vocab = _get_skill_vocab()
    postings: list[JobPosting] = []
    for item in results[:max_results]:
        desc = item.get("description", "")
        skills = _dict_match(desc, vocab)
        jid = str(item.get("id", hashlib.sha256(desc[:200].encode()).hexdigest()[:12]))
        postings.append(
            JobPosting(
                job_id=jid,
                title=item.get("title", "Unknown"),
                company=item.get("company", {}).get("display_name", "Unknown"),
                description=desc,
                required_skills=skills,
                preferred_skills=[],
                location=item.get("location", {}).get("display_name", "Unknown"),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                remote="remote" in desc.lower(),
                posted_date=item.get("created", ""),
                source="adzuna",
            )
        )
    return postings


# ---------------------------------------------------------------------------
# Remotive API (free, no key needed — remote jobs)
# ---------------------------------------------------------------------------


def _remotive_query(
    query: str,
    max_results: int = 20,
) -> list[JobPosting]:
    """Fetch remote jobs from Remotive API (free, no key required)."""
    try:
        import requests
    except ImportError:
        return []

    params = {"search": query, "limit": str(max_results)}
    try:
        resp = requests.get(REMOTIVE_BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    jobs_data = resp.json().get("jobs", [])
    vocab = _get_skill_vocab()
    postings: list[JobPosting] = []
    for item in jobs_data[:max_results]:
        raw_desc = item.get("description", "")
        # Strip HTML tags
        desc = re.sub(r"<[^>]+>", " ", raw_desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        skills = _dict_match(desc, vocab)
        postings.append(
            JobPosting(
                job_id=str(item.get("id", "")),
                title=item.get("title", "Unknown"),
                company=item.get("company_name", "Unknown"),
                description=desc,
                required_skills=skills,
                preferred_skills=[],
                location=item.get("candidate_required_location", "Remote"),
                remote=True,
                experience_level=item.get("job_type", "Not specified"),
                posted_date=item.get("publication_date", ""),
                source="remotive",
            )
        )
    return postings


# ---------------------------------------------------------------------------
# SerpAPI — Google Jobs (free tier: 100 searches/month)
# ---------------------------------------------------------------------------


def _serpapi_query(
    query: str,
    location: str = "",
    max_results: int = 20,
) -> list[JobPosting]:
    """Fetch jobs from Google Jobs via SerpAPI."""
    if not SERPAPI_KEY:
        return []
    try:
        import requests
    except ImportError:
        return []

    params = {
        "engine": "google_jobs",
        "q": query,
        "api_key": SERPAPI_KEY,
    }
    if location:
        params["location"] = location

    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    jobs_data = resp.json().get("jobs_results", [])
    vocab = _get_skill_vocab()
    postings: list[JobPosting] = []
    for item in jobs_data[:max_results]:
        desc = item.get("description", "")
        skills = _dict_match(desc, vocab)
        jid = hashlib.sha256(
            (item.get("title", "") + item.get("company_name", "")).encode()
        ).hexdigest()[:12]
        loc = item.get("location", "Unknown")
        postings.append(
            JobPosting(
                job_id=jid,
                title=item.get("title", "Unknown"),
                company=item.get("company_name", "Unknown"),
                description=desc,
                required_skills=skills,
                preferred_skills=[],
                location=loc,
                remote="remote" in loc.lower() or "remote" in desc.lower(),
                posted_date=item.get("detected_extensions", {}).get("posted_at", ""),
                source="serpapi_google",
            )
        )
    return postings


# ---------------------------------------------------------------------------
# Static CSV fallback (existing parsed data)
# ---------------------------------------------------------------------------


def load_static_jobs(
    path: Optional[str] = None, max_rows: int = 5000
) -> list[JobPosting]:
    """Load jobs from the existing ``jobs_parsed.csv``."""
    path = path or str(JOBS_PARSED_PATH)
    if not os.path.exists(path):
        return []
    from src.matching.semantic_matcher import jobs_df_to_postings

    df = pd.read_csv(path, nrows=max_rows)
    return jobs_df_to_postings(df)


# ---------------------------------------------------------------------------
# Unified collector
# ---------------------------------------------------------------------------


class JobCollector:
    """Unified job collection across all sources."""

    def search(
        self,
        query: str = "software engineer",
        location: str = "",
        max_results: int = 30,
        remote_only: bool = False,
    ) -> list[JobPosting]:
        """Search all configured API sources, then deduplicate."""
        all_jobs: list[JobPosting] = []

        # Try JSearch (RapidAPI)
        all_jobs.extend(_jsearch_query(query, location, max_results, remote_only))
        # Try Adzuna
        all_jobs.extend(_adzuna_query(query, location, max_results))
        # Try Remotive (free, no key)
        all_jobs.extend(_remotive_query(query, max_results))
        # Try SerpAPI / Google Jobs
        all_jobs.extend(_serpapi_query(query, location, max_results))

        # Fallback to static
        if not all_jobs:
            all_jobs = load_static_jobs(max_rows=max_results)

        # Deduplicate by job_id
        seen: set[str] = set()
        unique: list[JobPosting] = []
        for j in all_jobs:
            if j.job_id not in seen:
                seen.add(j.job_id)
                unique.append(j)
        return unique[:max_results]

    def save(self, jobs: list[JobPosting], path: Optional[str] = None) -> None:
        """Append jobs to a local CSV store."""
        path = path or str(JOBS_DB_PATH)
        file_exists = os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "job_id", "title", "company", "description", "required_skills",
                    "preferred_skills", "location", "salary_min", "salary_max",
                    "remote", "experience_level", "posted_date", "source",
                    "collected_at",
                ],
            )
            if not file_exists:
                writer.writeheader()
            for job in jobs:
                writer.writerow({
                    "job_id": job.job_id,
                    "title": job.title,
                    "company": job.company,
                    "description": job.description[:500],
                    "required_skills": ",".join(job.required_skills),
                    "preferred_skills": ",".join(job.preferred_skills),
                    "location": job.location,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "remote": job.remote,
                    "experience_level": job.experience_level,
                    "posted_date": job.posted_date,
                    "source": job.source,
                    "collected_at": datetime.utcnow().isoformat(),
                })
