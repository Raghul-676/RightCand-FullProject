"""
Everything in this file is deterministic. No LLM call ever happens here.
If a fact can be computed from parsers or the GitHub API, it belongs here,
not in the synthesis step.
"""
from __future__ import annotations
import json
import re
from typing import Optional

from models import ComplexityScore, TechStack
from github_client import get_file_content

# Manifest files we know how to parse, and which "kind" of dependency list they hold.
MANIFEST_FILES = {
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "Pipfile": "python",
    "package.json": "node",
    "pom.xml": "java",
    "build.gradle": "java",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "Gemfile": "ruby",
    "composer.json": "php",
}



CODE_FILE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb",
    ".php", ".c", ".cpp", ".h", ".cs", ".swift", ".kt",
}


def _extract_deps_from_requirements(text: str) -> list[str]:
    deps = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[=<>~\[; ]", line)[0].strip()
        if name:
            deps.append(name)
    return deps


def _extract_deps_from_package_json(text: str) -> list[str]:
    try:
        data = json.loads(text)
    except Exception:
        return []
    deps = list(data.get("dependencies", {}).keys())
    deps += list(data.get("devDependencies", {}).keys())
    return deps


def build_tech_stack(owner: str, repo: str, branch: str, tree: list[dict], languages: dict[str, int]) -> TechStack:
    total_bytes = sum(languages.values()) or 1
    lang_pct = {lang: round(100 * b / total_bytes, 1) for lang, b in languages.items()}

    tree_paths = {item["path"] for item in tree if item.get("type") == "blob"}
    manifests_found = []
    all_deps: list[str] = []

    for path in tree_paths:
        base = path.split("/")[-1]
        if base in MANIFEST_FILES and path.count("/") <= 1:  # prefer root/near-root manifests
            content = get_file_content(owner, repo, path, branch)
            if content is None:
                continue
            manifests_found.append(path)
            if base == "package.json":
                all_deps += _extract_deps_from_package_json(content)
            elif base in ("requirements.txt", "Pipfile"):
                all_deps += _extract_deps_from_requirements(content)
            # Other manifest formats (pom.xml, Cargo.toml, go.mod) are recorded
            # as "found" but left unparsed in this v1 — safer to say nothing
            # than to mis-parse XML/TOML with a regex.

    return TechStack(
        languages=lang_pct,
        dependencies=sorted(set(all_deps)),
        manifests_found=sorted(manifests_found),
        frameworks_detected=[],
    )


def compute_complexity(tree: list[dict], tech_stack: TechStack, repo_meta: dict) -> ComplexityScore:
    """
    Fixed weighted rubric — every number here is auditable and reproducible.
    This is intentionally NOT an LLM judgment call.
    """
    blobs = [item for item in tree if item.get("type") == "blob"]
    code_files = [b for b in blobs if any(b["path"].endswith(ext) for ext in CODE_FILE_EXTENSIONS)]
    file_count = len(blobs)
    code_file_count = len(code_files)
    max_depth = max((p["path"].count("/") for p in blobs), default=0)
    top_level_dirs = {p["path"].split("/")[0] for p in blobs if "/" in p["path"]}
    dep_count = len(tech_stack.dependencies)
    lang_count = len(tech_stack.languages)

    has_tests = any("test" in b["path"].lower() for b in blobs)
    has_ci = any(b["path"].startswith(".github/workflows/") for b in blobs)
    has_docker = any(b["path"].split("/")[-1] in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml") for b in blobs)

    # Weighted signal scoring, capped contributions so no single metric dominates.
    signals = {
        "code_file_count": code_file_count,
        "max_folder_depth": max_depth,
        "top_level_modules": len(top_level_dirs),
        "dependency_count": dep_count,
        "language_count": lang_count,
        "has_tests": 1.0 if has_tests else 0.0,
        "has_ci": 1.0 if has_ci else 0.0,
        "has_docker": 1.0 if has_docker else 0.0,
    }

    score = 0.0
    score += min(code_file_count / 150, 1.0) * 25      # up to 25 pts for scale
    score += min(max_depth / 6, 1.0) * 15               # up to 15 pts for nesting
    score += min(len(top_level_dirs) / 8, 1.0) * 15     # up to 15 pts for modularity
    score += min(dep_count / 25, 1.0) * 20              # up to 20 pts for dependency surface
    score += min(lang_count / 4, 1.0) * 10              # up to 10 pts for polyglot
    score += (5 if has_tests else 0) + (5 if has_ci else 0) + (5 if has_docker else 0)  # up to 15 pts engineering maturity

    score = round(min(score, 100))

    if score < 30:
        tier = "simple"
    elif score < 55:
        tier = "moderate"
    elif score < 75:
        tier = "complex"
    else:
        tier = "advanced"

    rationale_parts = [
        f"{code_file_count} code files across {len(top_level_dirs)} top-level module(s)",
        f"max folder depth {max_depth}",
        f"{dep_count} declared dependencies across {lang_count} language(s)",
    ]
    engineering_bits = []
    if has_tests:
        engineering_bits.append("tests present")
    if has_ci:
        engineering_bits.append("CI workflow present")
    if has_docker:
        engineering_bits.append("containerized (Docker)")
    if engineering_bits:
        rationale_parts.append(", ".join(engineering_bits))

    rationale = "; ".join(rationale_parts) + "."

    return ComplexityScore(score=score, tier=tier, signals=signals, rationale=rationale)


# """
# Everything in this file is deterministic. No LLM call ever happens here.
# If a fact can be computed from parsers or the GitHub API, it belongs here,
# not in the synthesis step.
# """
# from __future__ import annotations
# import json
# import re
# from typing import Optional

# from models import ComplexityScore, TechStack
# from github_client import get_file_content

# # Manifest files we know how to parse, and which "kind" of dependency list they hold.
# MANIFEST_FILES = {
#     "requirements.txt": "python",
#     "pyproject.toml": "python",
#     "Pipfile": "python",
#     "package.json": "node",
#     "pom.xml": "java",
#     "build.gradle": "java",
#     "Cargo.toml": "rust",
#     "go.mod": "go",
#     "Gemfile": "ruby",
#     "composer.json": "php",
# }

# # NOTE: framework detection (e.g. "fastapi" -> "FastAPI") used to be a
# # hardcoded keyword dict here. It's now handled by the LLM synthesis step
# # in llm_agent.py instead, reusing the same API call that already receives
# # this file's `dependencies` output — zero extra API calls, and it
# # generalizes beyond a fixed keyword list. See llm_agent.py's
# # `frameworks_detected` field and validator.py's cross-check against this
# # module's deterministic `dependencies` list.

# CODE_FILE_EXTENSIONS = {
#     ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb",
#     ".php", ".c", ".cpp", ".h", ".cs", ".swift", ".kt",
# }


# def _extract_deps_from_requirements(text: str) -> list[str]:
#     deps = []
#     for line in text.splitlines():
#         line = line.strip()
#         if not line or line.startswith("#"):
#             continue
#         name = re.split(r"[=<>~\[; ]", line)[0].strip()
#         if name:
#             deps.append(name)
#     return deps


# def _extract_deps_from_package_json(text: str) -> list[str]:
#     try:
#         data = json.loads(text)
#     except Exception:
#         return []
#     deps = list(data.get("dependencies", {}).keys())
#     deps += list(data.get("devDependencies", {}).keys())
#     return deps


# def build_tech_stack(owner: str, repo: str, branch: str, tree: list[dict], languages: dict[str, int]) -> TechStack:
#     total_bytes = sum(languages.values()) or 1
#     lang_pct = {lang: round(100 * b / total_bytes, 1) for lang, b in languages.items()}

#     tree_paths = {item["path"] for item in tree if item.get("type") == "blob"}
#     manifests_found = []
#     all_deps: list[str] = []

#     for path in tree_paths:
#         base = path.split("/")[-1]
#         if base in MANIFEST_FILES and path.count("/") <= 1:  # prefer root/near-root manifests
#             content = get_file_content(owner, repo, path, branch)
#             if content is None:
#                 continue
#             manifests_found.append(path)
#             if base == "package.json":
#                 all_deps += _extract_deps_from_package_json(content)
#             elif base in ("requirements.txt", "Pipfile"):
#                 all_deps += _extract_deps_from_requirements(content)
#             # Other manifest formats (pom.xml, Cargo.toml, go.mod) are recorded
#             # as "found" but left unparsed in this v1 — safer to say nothing
#             # than to mis-parse XML/TOML with a regex.

#     return TechStack(
#         languages=lang_pct,
#         dependencies=sorted(set(all_deps)),
#         manifests_found=sorted(manifests_found),
#         frameworks_detected=[],  # populated later by synthesize() in llm_agent.py
#     )


# def compute_complexity(tree: list[dict], tech_stack: TechStack, repo_meta: dict) -> ComplexityScore:
#     """
#     Fixed weighted rubric — every number here is auditable and reproducible.
#     This is intentionally NOT an LLM judgment call.
#     """
#     blobs = [item for item in tree if item.get("type") == "blob"]
#     code_files = [b for b in blobs if any(b["path"].endswith(ext) for ext in CODE_FILE_EXTENSIONS)]
#     file_count = len(blobs)
#     code_file_count = len(code_files)
#     max_depth = max((p["path"].count("/") for p in blobs), default=0)
#     top_level_dirs = {p["path"].split("/")[0] for p in blobs if "/" in p["path"]}
#     dep_count = len(tech_stack.dependencies)
#     lang_count = len(tech_stack.languages)

#     has_tests = any("test" in b["path"].lower() for b in blobs)
#     has_ci = any(b["path"].startswith(".github/workflows/") for b in blobs)
#     has_docker = any(b["path"].split("/")[-1] in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml") for b in blobs)

#     # Weighted signal scoring, capped contributions so no single metric dominates.
#     signals = {
#         "code_file_count": code_file_count,
#         "max_folder_depth": max_depth,
#         "top_level_modules": len(top_level_dirs),
#         "dependency_count": dep_count,
#         "language_count": lang_count,
#         "has_tests": 1.0 if has_tests else 0.0,
#         "has_ci": 1.0 if has_ci else 0.0,
#         "has_docker": 1.0 if has_docker else 0.0,
#     }

#     score = 0.0
#     score += min(code_file_count / 150, 1.0) * 25      # up to 25 pts for scale
#     score += min(max_depth / 6, 1.0) * 15               # up to 15 pts for nesting
#     score += min(len(top_level_dirs) / 8, 1.0) * 15     # up to 15 pts for modularity
#     score += min(dep_count / 25, 1.0) * 20              # up to 20 pts for dependency surface
#     score += min(lang_count / 4, 1.0) * 10              # up to 10 pts for polyglot
#     score += (5 if has_tests else 0) + (5 if has_ci else 0) + (5 if has_docker else 0)  # up to 15 pts engineering maturity

#     score = round(min(score, 100))

#     if score < 30:
#         tier = "simple"
#     elif score < 55:
#         tier = "moderate"
#     elif score < 75:
#         tier = "complex"
#     else:
#         tier = "advanced"

#     rationale_parts = [
#         f"{code_file_count} code files across {len(top_level_dirs)} top-level module(s)",
#         f"max folder depth {max_depth}",
#         f"{dep_count} declared dependencies across {lang_count} language(s)",
#     ]
#     engineering_bits = []
#     if has_tests:
#         engineering_bits.append("tests present")
#     if has_ci:
#         engineering_bits.append("CI workflow present")
#     if has_docker:
#         engineering_bits.append("containerized (Docker)")
#     if engineering_bits:
#         rationale_parts.append(", ".join(engineering_bits))

#     rationale = "; ".join(rationale_parts) + "."

#     return ComplexityScore(score=score, tier=tier, signals=signals, rationale=rationale)