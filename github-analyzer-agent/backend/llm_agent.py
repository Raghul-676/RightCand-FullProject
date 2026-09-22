"""
The ONLY module in the pipeline that calls an LLM. It is deliberately
constrained: the model never sees the repo name, star count, or anything
that could bias it toward guessing. It only sees the evidence bundle
assembled by evidence.py, plus the deterministic tech stack facts, and it
is required to cite which evidence path supports each claim.
"""
from __future__ import annotations
import json
import os
from typing import Optional

from groq import Groq

from models import Claim, EvidenceItem, TechStack, ComplexityScore

MODEL = "llama-3.3-70b-versatile"

# Fixed taxonomy — domain classification must pick from this list, not
# freehand text. Keeps the field filterable/queryable across every analyzed
# repo instead of being a one-off paraphrase of the project name.
DOMAIN_TAXONOMY = [
    "Web Development - Frontend",
    "Web Development - Backend",
    "Web Development - Full Stack",
    "Mobile Development",
    "ML/AI - Computer Vision",
    "ML/AI - NLP",
    "ML/AI - Predictive/Tabular",
    "Data Engineering",
    "DevOps/Cloud",
    "Cybersecurity",
    "IoT/Embedded",
    "Blockchain",
    "Game Development",
    "AR/VR",
    "Other",
]

SYSTEM_PROMPT = f"""You are a code analysis assistant. You will be given:
1. A set of deterministic facts about a code repository (languages, dependencies, complexity signals).
2. A set of evidence excerpts (file path + content) pulled directly from that repository.

Your job is to produce exactly three things, grounded ONLY in what is provided:

- "domain": classify the project using this fixed taxonomy — pick 1 or 2 categories
  that best fit (a project can span two, e.g. Full Stack + ML/AI). Do not invent new
  category names outside this list:
  {json.dumps(DOMAIN_TAXONOMY)}
  Also include a one-sentence free-text description of what makes it fit that category.

- "summary": a 2-3 sentence plain-language summary of what the project does.

- "frameworks": identify recognizable frameworks/libraries (e.g. React, Next.js, FastAPI, Flask, Django, Spring Boot, PyTorch, TensorFlow, HuggingFace Transformers, Streamlit, etc.) used in the project based on the provided dependencies and code files. Return a simple list of framework names (strings).

STRICT RULES:
- Do not invent facts not present in the evidence or deterministic data.
- Do not assume anything from the repo name alone if the evidence doesn't support it.
- For each of "domain" and "summary", include a "cited_paths" list: the exact file paths (from
  the evidence provided) that justify your claim. If you cannot support a claim with a specific
  file, say so explicitly in the text (e.g. "insufficient evidence to determine X") rather than guessing.
- Output strict JSON only, matching this schema, no markdown fences, no commentary:
{{
  "domain": {{"categories": ["..."], "text": "...", "cited_paths": ["..."]}},
  "summary": {{"text": "...", "cited_paths": ["..."]}},
  "frameworks": ["FrameworkName1", "FrameworkName2"]
}}
"""


def _build_user_prompt(tech_stack: TechStack, complexity: ComplexityScore, evidence: list[EvidenceItem]) -> str:
    facts = {
        "languages": tech_stack.languages,
        "dependencies": tech_stack.dependencies,
        "manifests_found": tech_stack.manifests_found,
        "complexity_tier": complexity.tier,
        "complexity_signals": complexity.signals,
    }
    evidence_blocks = "\n\n".join(
        f"--- FILE: {e.path} (type: {e.kind}) ---\n{e.excerpt}" for e in evidence
    )
    return (
        f"DETERMINISTIC FACTS:\n{json.dumps(facts, indent=2)}\n\n"
        f"EVIDENCE FILES:\n{evidence_blocks if evidence_blocks else '(no evidence files could be retrieved)'}"
    )


def synthesize(tech_stack: TechStack, complexity: ComplexityScore, evidence: list[EvidenceItem]) -> tuple[Claim, Claim, list[str]]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

    client = Groq(api_key=api_key)
    user_prompt = _build_user_prompt(tech_stack, complexity, evidence)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        domain = parsed["domain"]
        summary = parsed["summary"]
        frameworks = parsed.get("frameworks", [])
    except (json.JSONDecodeError, KeyError):
        domain = {"categories": [], "text": "Could not confidently determine domain from available evidence.", "cited_paths": []}
        summary = {"text": "Could not generate a grounded summary from available evidence.", "cited_paths": []}
        frameworks = []

    domain_claim = Claim(
        text=domain.get("text", ""),
        cited_paths=domain.get("cited_paths", []),
        categories=domain.get("categories", []),
    )
    summary_claim = Claim(text=summary.get("text", ""), cited_paths=summary.get("cited_paths", []))
    return domain_claim, summary_claim, frameworks


# """
# The ONLY module in the pipeline that calls an LLM. It is deliberately
# constrained: the model never sees the repo name, star count, or anything
# that could bias it toward guessing. It only sees the evidence bundle
# assembled by evidence.py, plus the deterministic tech stack facts, and it
# is required to cite which evidence path (or dependency string) supports
# each claim.
# """
# from __future__ import annotations
# import json
# import os
# from typing import Optional

# from groq import Groq

# from models import Claim, EvidenceItem, TechStack, ComplexityScore

# MODEL = "llama-3.3-70b-versatile"

# # Fixed taxonomy — domain classification must pick from this list, not
# # freehand text. Keeps the field filterable/queryable across every analyzed
# # repo instead of being a one-off paraphrase of the project name.
# DOMAIN_TAXONOMY = [
#     "Web Development - Frontend",
#     "Web Development - Backend",
#     "Web Development - Full Stack",
#     "Mobile Development",
#     "ML/AI - Computer Vision",
#     "ML/AI - NLP",
#     "ML/AI - Predictive/Tabular",
#     "Data Engineering",
#     "DevOps/Cloud",
#     "Cybersecurity",
#     "IoT/Embedded",
#     "Blockchain",
#     "Game Development",
#     "AR/VR",
#     "Other",
# ]

# SYSTEM_PROMPT = """You are a code analysis assistant. You will be given:
# 1. A set of deterministic facts about a code repository (languages, dependencies, complexity signals).
# 2. A set of evidence excerpts (file path + content) pulled directly from that repository.

# Your job is to produce exactly three things, grounded ONLY in what is provided:

# - "domain": classify the project using this fixed taxonomy — pick 1 or 2 categories
#   that best fit (a project can span two, e.g. Full Stack + ML/AI). Do not invent new
#   category names outside this list:
#   {domain_taxonomy}
#   Also include a one-sentence free-text description of what makes it fit that category.

# - "summary": a 2-3 sentence plain-language summary of what the project does.

# - "frameworks": identify recognizable frameworks/libraries from the DETERMINISTIC
#   "dependencies" list given to you (e.g. the string "fastapi" -> the framework "FastAPI").
#   For each one you recognize, pair it with the EXACT dependency string from the list that
#   justified it — do not paraphrase or guess the dependency's spelling. Do not include a
#   framework unless its exact matching entry is present in the given dependency list. This
#   list is not limited to any fixed set of frameworks - recognize whatever you genuinely know.

# STRICT RULES:
# - Do not invent facts not present in the evidence or deterministic data.
# - Do not assume anything from the repo name alone if the evidence doesn't support it.
# - For "domain" and "summary", include a "cited_paths" list: exact file paths (from the
#   evidence provided) that justify the claim. If you cannot support a claim with a specific
#   file, say so explicitly in the text (e.g. "insufficient evidence to determine X") rather
#   than guessing.
# - For "frameworks", every "matched_dependency" MUST be copied verbatim from the dependencies
#   list you were given. A framework entry whose matched_dependency is not in that list will be
#   discarded downstream, so do not guess or paraphrase it.
# - Output strict JSON only, matching this schema, no markdown fences, no commentary:
# {{
#   "domain": {{"categories": ["..."], "text": "...", "cited_paths": ["..."]}},
#   "summary": {{"text": "...", "cited_paths": ["..."]}},
#   "frameworks": [{{"name": "FastAPI", "matched_dependency": "fastapi"}}]
# }}
# """


# def _build_user_prompt(tech_stack: TechStack, complexity: ComplexityScore, evidence: list[EvidenceItem]) -> str:
#     facts = {
#         "languages": tech_stack.languages,
#         "dependencies": tech_stack.dependencies,
#         "complexity_tier": complexity.tier,
#         "complexity_signals": complexity.signals,
#     }
#     evidence_blocks = "\n\n".join(
#         f"--- FILE: {e.path} (type: {e.kind}) ---\n{e.excerpt}" for e in evidence
#     )
#     return (
#         f"DETERMINISTIC FACTS:\n{json.dumps(facts, indent=2)}\n\n"
#         f"EVIDENCE FILES:\n{evidence_blocks if evidence_blocks else '(no evidence files could be retrieved)'}"
#     )


# def _validate_frameworks(raw_frameworks: list, known_dependencies: list[str]) -> list[str]:
#     """
#     Cross-check each LLM-claimed framework against the deterministic
#     dependency list. A framework is only kept if its matched_dependency is
#     an exact (case-insensitive) match to something actually in that list —
#     this is what makes the LLM free-recognition safe against hallucination:
#     it can only "discover" frameworks that trace back to a real dependency
#     string, never invent one that isn't there.
#     """
#     dep_lookup = {d.lower(): d for d in known_dependencies}
#     validated = []
#     for entry in raw_frameworks:
#         if not isinstance(entry, dict):
#             continue
#         name = entry.get("name", "").strip()
#         matched = entry.get("matched_dependency", "").strip()
#         if name and matched.lower() in dep_lookup:
#             validated.append(name)
#     return sorted(set(validated))


# def synthesize(tech_stack: TechStack, complexity: ComplexityScore, evidence: list[EvidenceItem]) -> tuple[Claim, Claim, list[str]]:
#     api_key = os.getenv("GROQ_API_KEY")
#     if not api_key:
#         raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

#     client = Groq(api_key=api_key)
#     user_prompt = _build_user_prompt(tech_stack, complexity, evidence)
#     system_prompt = SYSTEM_PROMPT.format(domain_taxonomy=json.dumps(DOMAIN_TAXONOMY))

#     response = client.chat.completions.create(
#         model=MODEL,
#         temperature=0.1,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt},
#         ],
#         response_format={"type": "json_object"},
#     )

#     raw = response.choices[0].message.content
#     try:
#         parsed = json.loads(raw)
#         domain = parsed["domain"]
#         summary = parsed["summary"]
#         raw_frameworks = parsed.get("frameworks", [])
#     except (json.JSONDecodeError, KeyError):
#         domain = {"categories": [], "text": "Could not confidently determine domain from available evidence.", "cited_paths": []}
#         summary = {"text": "Could not generate a grounded summary from available evidence.", "cited_paths": []}
#         raw_frameworks = []

#     domain_claim = Claim(
#         text=domain.get("text", ""),
#         cited_paths=domain.get("cited_paths", []),
#         categories=domain.get("categories", []),
#     )
#     summary_claim = Claim(text=summary.get("text", ""), cited_paths=summary.get("cited_paths", []))
#     frameworks_detected = _validate_frameworks(raw_frameworks, tech_stack.dependencies)

#     return domain_claim, summary_claim, frameworks_detected