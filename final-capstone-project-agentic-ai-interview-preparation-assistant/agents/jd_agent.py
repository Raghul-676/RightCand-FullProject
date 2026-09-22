# import json
# from utils.llm import generate_json_response


# def analyze_jd(jd_text: str) -> dict:
#     """
#     Analyze job description text and extract structured requirements.
#     Returns dict with required_skills, preferred_skills, responsibilities, and experience_requirements.
#     """
#     prompt = f"""Analyze the following job description and extract information into a JSON object.

# Return ONLY valid JSON with this exact structure (no markdown, no extra text):
# {{
#   "required_skills": ["skill1", "skill2"],
#   "preferred_skills": ["skill1", "skill2"],
#   "responsibilities": ["responsibility1", "responsibility2"],
#   "experience_requirements": ["requirement1", "requirement2"]
# }}

# Job Description:
# {jd_text}"""

#     response = generate_json_response(prompt)

#     cleaned = response.strip()
#     if cleaned.startswith("```"):
#         cleaned = cleaned.split("```")[1]
#         if cleaned.startswith("json"):
#             cleaned = cleaned[4:]
#         cleaned = cleaned.strip()

#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         return {
#             "required_skills": [],
#             "preferred_skills": [],
#             "responsibilities": [],
#             "experience_requirements": [],
#         }


import json
from utils.llm import generate_json_response


def _sanitize_string_list(value) -> list[str]:
    """Same rationale as resume_agent.py — see that file's comment."""
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()]


def analyze_jd(jd_text: str) -> dict:
    """
    Analyze job description text and extract structured requirements.
    Returns dict with required_skills, preferred_skills, responsibilities, and experience_requirements.
    """
    prompt = f"""Analyze the following job description and extract information into a JSON object.

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "responsibilities": ["responsibility1", "responsibility2"],
  "experience_requirements": ["requirement1", "requirement2"]
}}

Job Description:
{jd_text}"""

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
        print(f"[jd_agent] JSON parse failed, raw response was: {response!r}")
        return {
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "experience_requirements": [],
        }

    # required_skills is validated directly since gap_agent depends on it
    # (and now does .lower() on every entry — a non-string entry here would
    # crash that, same reasoning as resume_agent.py).
    result["required_skills"] = _sanitize_string_list(result.get("required_skills"))
    result["preferred_skills"] = _sanitize_string_list(result.get("preferred_skills"))
    if not isinstance(result.get("responsibilities"), list):
        result["responsibilities"] = []
    if not isinstance(result.get("experience_requirements"), list):
        result["experience_requirements"] = []

    return result