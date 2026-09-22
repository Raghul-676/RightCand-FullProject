# import json
# from utils.llm import generate_json_response


# def analyze_gap(resume_data: dict, jd_data: dict) -> dict:
#     """
#     Compare resume skills against JD required skills.
#     Returns matched_skills, missing_skills, and match_percentage.
#     """
#     resume_skills = resume_data.get("skills", [])
#     required_skills = jd_data.get("required_skills", [])

#     prompt = f"""Compare the candidate's skills against the job's required skills.

# Candidate skills: {json.dumps(resume_skills)}
# Required skills: {json.dumps(required_skills)}

# Return ONLY valid JSON with this exact structure (no markdown, no extra text):
# {{
#   "matched_skills": ["skills present in both lists"],
#   "missing_skills": ["skills required but not in candidate's resume"]
# }}

# Use case-insensitive comparison. Group similar technologies (e.g., "JS" and "JavaScript" are the same)."""

#     response = generate_json_response(prompt)

#     cleaned = response.strip()
#     if cleaned.startswith("```"):
#         cleaned = cleaned.split("```")[1]
#         if cleaned.startswith("json"):
#             cleaned = cleaned[4:]
#         cleaned = cleaned.strip()

#     try:
#         result = json.loads(cleaned)
#     except json.JSONDecodeError:
#         result = {"matched_skills": [], "missing_skills": required_skills}

#     # Calculate match percentage
#     total = len(required_skills)
#     print(f"[DEBUG] resume_skills = {resume_skills!r}")
#     print(f"[DEBUG] required_skills = {required_skills!r}")
#     print(f"[DEBUG] raw LLM response = {response!r}")
#     print(f"[DEBUG] parsed result = {result!r}")

#     matched = len(result.get("matched_skills", []))
#     match_percentage = round((matched / total * 100) if total > 0 else 0, 1)
#     result["match_percentage"] = match_percentage

#     return result


import json
from utils.llm import generate_json_response


def analyze_gap(resume_data: dict, jd_data: dict) -> dict:
    """
    Compare resume skills against JD required skills.
    Returns matched_skills, missing_skills, and match_percentage.
    """
    resume_skills = resume_data.get("skills", [])
    required_skills = jd_data.get("required_skills", [])

    prompt = f"""Compare the candidate's skills against the job's required skills.

Candidate skills: {json.dumps(resume_skills)}
Required skills: {json.dumps(required_skills)}

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "matched_skills": ["skills present in both lists — use the EXACT wording from Required Skills, not the candidate's wording"]
}}

Use case-insensitive comparison. Group similar technologies (e.g., "JS" and "JavaScript" are the same) —
but always report the matched skill using its exact spelling from the Required Skills list above,
so it can be validated against that list."""

    response = generate_json_response(prompt)

    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        raw_matched = result.get("matched_skills", [])
    except json.JSONDecodeError:
        print(f"[gap_agent] JSON parse failed, raw response was: {response!r}")
        raw_matched = []

    # VALIDATION: only trust a matched skill if it actually appears in
    # required_skills (case-insensitive). This is what prevents hallucinated,
    # duplicated, or misspelled entries from inflating the percentage.
    required_lower = {s.lower(): s for s in required_skills}
    validated_matched = []
    seen = set()
    for skill in raw_matched:
        key = skill.lower().strip()
        if key in required_lower and key not in seen:
            validated_matched.append(required_lower[key])  # use the JD's exact original spelling
            seen.add(key)

    # missing_skills is computed deterministically as the complement — never
    # asked of the LLM separately, so it's guaranteed consistent with
    # matched_skills by construction, not by hoping two LLM outputs agree.
    validated_missing = [s for s in required_skills if s.lower() not in seen]

    total = len(required_skills)
    matched = len(validated_matched)
    match_percentage = round(min(matched / total * 100, 100.0) if total > 0 else 0, 1)

    print(f"[DEBUG] resume_skills = {resume_skills!r}")
    print(f"[DEBUG] required_skills = {required_skills!r}")
    print(f"[DEBUG] raw LLM matched (unvalidated) = {raw_matched!r}")
    print(f"[DEBUG] validated matched = {validated_matched!r}")

    return {
        "matched_skills": validated_matched,
        "missing_skills": validated_missing,
        "match_percentage": match_percentage,
    }