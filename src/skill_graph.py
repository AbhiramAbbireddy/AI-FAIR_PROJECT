"""
Dynamic skill graph for FAIR-PATH.

Builds a dependency graph from the project's existing learning-time and skill
hierarchy databases, then answers practical questions:
- which missing skill is the main bottleneck?
- what is the shortest dependency path to a target skill?
- which current skills partially substitute for missing ones?
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from src.config.settings import BASE_DIR
from src.skill_extraction.normalizer import normalize_skill


LEARNING_DB_PATH = BASE_DIR / "data" / "learning_time_database.json"
HIERARCHY_DB_PATH = BASE_DIR / "data" / "skill_hierarchy.json"

TRANSFERABILITY_MAP: dict[str, dict[str, float]] = {
    "tensorflow": {"pytorch": 0.8, "scikit-learn": 0.35},
    "pytorch": {"tensorflow": 0.8, "scikit-learn": 0.35},
    "langchain": {"llamaindex": 0.75},
    "llamaindex": {"langchain": 0.75},
    "docker": {"kubernetes": 0.35},
    "kubernetes": {"docker": 0.5},
    "react": {"vue": 0.55, "angular": 0.45},
    "vue": {"react": 0.55, "angular": 0.40},
    "angular": {"react": 0.45, "vue": 0.40},
    "postgresql": {"mysql": 0.65, "sql": 0.45},
    "mysql": {"postgresql": 0.65, "sql": 0.45},
    "rag": {"retrieval-augmented generation": 1.0},
    "retrieval-augmented generation": {"rag": 1.0},
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


class SkillGraphAnalyzer:
    def __init__(self):
        self.learning_db = _load_json(LEARNING_DB_PATH)
        self.hierarchy_db = _load_json(HIERARCHY_DB_PATH)
        self.graph = self._build_graph()

    def _build_graph(self) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = defaultdict(set)

        for skill, payload in self.learning_db.items():
            child = normalize_skill(skill)
            for prereq in payload.get("prerequisites", []):
                graph[normalize_skill(prereq)].add(child)
                graph.setdefault(child, set())

        for skill, payload in self.hierarchy_db.items():
            child = normalize_skill(skill)
            parent = normalize_skill(str(payload.get("parent", "")).strip())
            if parent:
                graph[parent].add(child)
                graph.setdefault(child, set())

        return graph

    def _prerequisites_for(self, skill: str) -> list[str]:
        normalized = normalize_skill(skill)
        learning_prereqs = [
            normalize_skill(item)
            for item in self.learning_db.get(normalized, {}).get("prerequisites", [])
            if str(item).strip()
        ]
        parent = normalize_skill(str(self.hierarchy_db.get(normalized, {}).get("parent", "")).strip())
        merged = list(dict.fromkeys(learning_prereqs + ([parent] if parent else [])))
        return [item for item in merged if item]

    def _shortest_path_from_known(self, known_skills: set[str], target_skill: str) -> list[str]:
        normalized_target = normalize_skill(target_skill)
        if normalized_target in known_skills:
            return [normalized_target]

        visited: set[str] = set()
        queue: deque[tuple[str, list[str]]] = deque()
        for root in known_skills:
            queue.append((root, [root]))
            visited.add(root)

        while queue:
            current, path = queue.popleft()
            for neighbor in self.graph.get(current, set()):
                if neighbor in visited:
                    continue
                next_path = path + [neighbor]
                if neighbor == normalized_target:
                    return next_path
                visited.add(neighbor)
                queue.append((neighbor, next_path))

        # fall back to prerequisite chain if disconnected
        path = []
        cursor = normalized_target
        seen: set[str] = set()
        while cursor and cursor not in seen:
            path.append(cursor)
            seen.add(cursor)
            prereqs = self._prerequisites_for(cursor)
            cursor = prereqs[0] if prereqs else ""
            if cursor in known_skills:
                path.append(cursor)
                break
        return list(reversed(path))

    def _substitutes_for(self, known_skills: set[str], missing_skill: str) -> list[dict[str, Any]]:
        normalized_missing = normalize_skill(missing_skill)
        matches = []
        for source_skill, score in TRANSFERABILITY_MAP.get(normalized_missing, {}).items():
            if normalize_skill(source_skill) in known_skills:
                matches.append(
                    {
                        "source_skill": normalize_skill(source_skill),
                        "target_skill": normalized_missing,
                        "transferability": round(float(score), 2),
                        "recommendation": f"You already know {source_skill}. Bridging to {normalized_missing} should be faster than starting from scratch.",
                    }
                )
        return sorted(matches, key=lambda item: item["transferability"], reverse=True)

    def analyze(
        self,
        *,
        known_skills: list[str],
        missing_skills: list[str],
        target_role: str = "",
    ) -> dict[str, Any]:
        known = {normalize_skill(skill) for skill in known_skills if str(skill).strip()}
        missing = [normalize_skill(skill) for skill in missing_skills if str(skill).strip()]

        dependency_paths = []
        blocker_counter: Counter[str] = Counter()
        substitute_matches = []
        unlock_map: dict[str, list[str]] = defaultdict(list)

        for missing_skill in missing:
            path = self._shortest_path_from_known(known, missing_skill)
            dependency_paths.append(
                {
                    "skill": missing_skill,
                    "path": path,
                    "distance": max(len(path) - 1, 0),
                }
            )

            for prereq in self._prerequisites_for(missing_skill):
                if prereq not in known:
                    blocker_counter[prereq] += 1
                    unlock_map[prereq].append(missing_skill)

            substitute_matches.extend(self._substitutes_for(known, missing_skill))

        bottlenecks = [
            {
                "skill": skill,
                "unlocks": sorted(set(unlock_map.get(skill, []))),
                "unlock_count": count,
            }
            for skill, count in blocker_counter.most_common(5)
        ]

        critical_path = sorted(dependency_paths, key=lambda item: (-item["distance"], item["skill"]))[:3]
        graph_nodes = []
        for item in dependency_paths[:6]:
            graph_nodes.extend(item["path"])
        graph_nodes = list(dict.fromkeys(graph_nodes))

        mermaid_lines = ["flowchart TD"]
        added_edges: set[tuple[str, str]] = set()
        for item in dependency_paths[:6]:
            path = item["path"]
            for left, right in zip(path, path[1:]):
                edge = (left, right)
                if edge in added_edges:
                    continue
                added_edges.add(edge)
                mermaid_lines.append(f'    "{left}" --> "{right}"')

        return {
            "target_role": target_role,
            "dependency_paths": dependency_paths,
            "bottlenecks": bottlenecks,
            "substitute_matches": substitute_matches[:5],
            "critical_path": critical_path,
            "graph_skills": graph_nodes,
            "mermaid": "\n".join(mermaid_lines),
            "summary": self._summary(target_role, bottlenecks, substitute_matches, critical_path),
        }

    @staticmethod
    def _summary(
        target_role: str,
        bottlenecks: list[dict[str, Any]],
        substitute_matches: list[dict[str, Any]],
        critical_path: list[dict[str, Any]],
    ) -> str:
        if bottlenecks:
            top = bottlenecks[0]
            return (
                f"For {target_role or 'this role'}, the main bottleneck is {top['skill']}, "
                f"which unlocks {top['unlock_count']} downstream skill areas."
            )
        if substitute_matches:
            top = substitute_matches[0]
            return (
                f"You already have a useful substitute: {top['source_skill']} can accelerate learning {top['target_skill']} "
                f"with about {int(top['transferability'] * 100)}% transferability."
            )
        if critical_path:
            top = critical_path[0]
            return f"The longest dependency path currently ends at {top['skill']}."
        return "No meaningful dependency bottlenecks were detected."
