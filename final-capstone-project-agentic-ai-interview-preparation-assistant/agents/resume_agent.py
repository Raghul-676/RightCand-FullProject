# import json
# from utils.llm import generate_json_response


# def analyze_resume(resume_text: str) -> dict:
#     """
#     Analyze resume text and extract structured information.
#     Returns dict with skills, projects, experience, and education.
#     """
#     prompt = f"""Analyze the following resume and extract information into a JSON object.

# Return ONLY valid JSON with this exact structure (no markdown, no extra text):
# {{
#   "skills": ["skill1", "skill2"],
#   "projects": [
#     {{"name": "Project Name", "description": "Brief description", "technologies": ["tech1"]}}
#   ],
#   "experience": [
#     {{"title": "Job Title", "company": "Company", "duration": "Duration", "responsibilities": ["resp1"]}}
#   ],
#   "education": [
#     {{"degree": "Degree", "institution": "Institution", "year": "Year"}}
#   ]
# }}

# Resume:
# {resume_text}"""

#     response = generate_json_response(prompt)

#     # Strip markdown code fences if present
#     cleaned = response.strip()
#     if cleaned.startswith("```"):
#         cleaned = cleaned.split("```")[1]
#         if cleaned.startswith("json"):
#             cleaned = cleaned[4:]
#         cleaned = cleaned.strip()

#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         # Fallback: return minimal structure to avoid crashing downstream agents
#         return {"skills": [], "projects": [], "experience": [], "education": []}


import json
from utils.llm import generate_json_response


def _sanitize_string_list(value) -> list[str]:
    """
    response_format=json_object only guarantees valid JSON syntax, not that
    the model actually followed the requested schema. This strips out any
    entry that isn't a plain string, so downstream code (like gap_agent's
    skill.lower() calls) never crashes on a malformed entry the model
    produced despite the prompt's instructions.
    """
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()]


def analyze_resume(resume_text: str) -> dict:
    """
    Analyze resume text and extract structured information.
    Returns dict with skills, projects, experience, and education.
    """
    prompt = f"""Analyze the following resume and extract information into a JSON object.

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "skills": ["skill1", "skill2"],
  "projects": [
    {{"name": "Project Name", "description": "Brief description", "technologies": ["tech1"]}}
  ],
  "experience": [
    {{"title": "Job Title", "company": "Company", "duration": "Duration", "responsibilities": ["resp1"]}}
  ],
  "education": [
    {{"degree": "Degree", "institution": "Institution", "year": "Year"}}
  ]
}}

Resume:
{resume_text}"""

    response = generate_json_response(prompt)

    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"[resume_agent] JSON parse failed, raw response was: {response!r}")
        return {"skills": [], "projects": [], "experience": [], "education": []}

    # Schema validation — "skills" specifically, since it's what gap_agent
    # depends on directly. projects/experience/education are left as-is
    # here since gap_agent doesn't touch them, but the same _sanitize
    # pattern applies if you later depend on their exact shape too.
    result["skills"] = _sanitize_string_list(result.get("skills"))
    if not isinstance(result.get("projects"), list):
        result["projects"] = []
    if not isinstance(result.get("experience"), list):
        result["experience"] = []
    if not isinstance(result.get("education"), list):
        result["education"] = []

    return result