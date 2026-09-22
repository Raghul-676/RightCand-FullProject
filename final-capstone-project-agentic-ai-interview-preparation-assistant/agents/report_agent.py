import json
from utils.llm import generate_response

# Evaluation expectations per level — used to set the right benchmark in the prompt
LEVEL_EXPECTATIONS = {
    "Intern": (
        "This is an intern/fresher candidate. Evaluate relative to internship expectations. "
        "Do NOT penalize for lack of system design, scalability, or distributed systems knowledge. "
        "Reward good project understanding, technology reasoning, and learning attitude."
    ),
    "Junior Developer": (
        "This is a junior developer (0-2 years). Evaluate relative to junior-level expectations. "
        "Expect solid project knowledge, basic API and database skills, and some awareness of "
        "optimization. Do not penalize for lack of deep architectural knowledge."
    ),
    "Senior Developer": (
        "This is a senior developer (3+ years). Apply high expectations. "
        "Evaluate depth of system design thinking, scalability awareness, architectural "
        "trade-offs, and technical leadership. Gaps in these areas should be reflected."
    ),
}


def generate_report(
    resume_data: dict,
    jd_data: dict,
    gap_data: dict,
    evaluations: list[dict],
    candidate_level: str = "Junior Developer",
) -> str:
    """
    Generate a comprehensive final interview report relative to the candidate's level.
    Returns a formatted report string.
    """
    if not evaluations:
        return "No evaluations available to generate a report."

    # Aggregate performance metrics
    avg_accuracy     = round(sum(e.get("accuracy", 0)      for e in evaluations) / len(evaluations), 1)
    avg_clarity      = round(sum(e.get("clarity", 0)       for e in evaluations) / len(evaluations), 1)
    avg_depth        = round(sum(e.get("depth", 0)         for e in evaluations) / len(evaluations), 1)
    avg_communication= round(sum(e.get("communication", 0) for e in evaluations) / len(evaluations), 1)
    avg_overall      = round(sum(e.get("overall_score", 0) for e in evaluations) / len(evaluations), 1)

    level_context = LEVEL_EXPECTATIONS.get(candidate_level, LEVEL_EXPECTATIONS["Junior Developer"])

    prompt = f"""You are a senior hiring manager. Generate a professional interview performance report.

Candidate Level: {candidate_level}
Level Evaluation Context: {level_context}

Candidate Profile:
- Skills: {json.dumps(resume_data.get('skills', []))}
- Projects: {json.dumps([p.get('name', '') for p in resume_data.get('projects', [])])}
- Resume match: {gap_data.get('match_percentage', 0)}%
- Matched skills: {json.dumps(gap_data.get('matched_skills', []))}
- Missing skills: {json.dumps(gap_data.get('missing_skills', []))}

Interview Performance (averages out of 10, evaluated relative to {candidate_level} expectations):
- Technical Accuracy : {avg_accuracy}
- Clarity           : {avg_clarity}
- Depth             : {avg_depth}
- Communication     : {avg_communication}
- Overall Score     : {avg_overall}

Per-question feedback:
{json.dumps([e.get('feedback', '') for e in evaluations], indent=2)}

Write a professional report with exactly these sections (use these exact headings):

1. INTERVIEW LEVEL
   State the interview level and what it means for evaluation.

2. RESUME MATCH SUMMARY
   Summarize the skills match between resume and JD.

3. TECHNICAL PERFORMANCE
   Evaluate technical accuracy and depth relative to {candidate_level} expectations.

4. COMMUNICATION PERFORMANCE
   Evaluate clarity and communication quality.

5. TECHNICAL DEPTH EVALUATED
   List the specific technology areas and topics that were covered during the interview.

6. STRONG AREAS
   List specific strengths demonstrated.

7. AREAS FOR IMPROVEMENT
   List specific weaknesses or gaps relative to the expected level.

8. HIRING READINESS
   Give one verdict: Strong Hire / Hire / Borderline / No Hire
   Justify the verdict in 2-3 sentences relative to {candidate_level} standards.

9. RECOMMENDATIONS
   Give 3-5 specific, actionable recommendations tailored to {candidate_level}.

Be concise, specific, and professional. All evaluations must be relative to {candidate_level} standards."""

    return generate_response(prompt)
