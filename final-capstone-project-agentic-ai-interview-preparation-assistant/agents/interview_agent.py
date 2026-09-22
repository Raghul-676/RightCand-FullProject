# import json
# from utils.llm import generate_response

# # Per-level configuration: what to focus on and what to avoid
# LEVEL_CONFIG = {
#     "Intern": {
#         "description": "internship/fresher technical round",
#         "focus": [
#             "Resume projects and implementation details",
#             "Technology choices made in projects (why MongoDB, why React, etc.)",
#             "How frontend and backend were connected",
#             "REST APIs implemented in projects",
#             "Authentication mechanisms used",
#             "Databases used and basic schema design",
#             "Frameworks and libraries from resume",
#             "Challenges faced during development",
#         ],
#         "avoid": [
#             "System Design",
#             "Scalability and distributed systems",
#             "Load balancing and caching architectures",
#             "Sharding and replication strategies",
#             "Microservices architecture",
#             "DSA and algorithmic problems",
#             "Cloud infrastructure design",
#         ],
#         "followup_style": (
#             "Ask implementation-focused follow-ups, technology-choice questions, "
#             "and challenge-based questions. Example: if asked about MongoDB, "
#             "follow up with 'What specific advantages of MongoDB helped in your project?'"
#         ),
#     },
#     "Junior Developer": {
#         "description": "junior developer interview (0-2 years experience)",
#         "focus": [
#             "Project architecture and design decisions",
#             "API design and security (authentication, authorization)",
#             "Database query optimization",
#             "Error handling and input validation strategies",
#             "Deployment basics (CI/CD, Docker basics)",
#             "Performance improvements made or considered",
#             "Code quality and maintainability practices",
#             "Technologies from resume and JD",
#         ],
#         "avoid": [
#             "Deep distributed systems",
#             "Large-scale system design (millions of users)",
#             "DSA and algorithmic problems",
#             "Advanced cloud infrastructure",
#         ],
#         "followup_style": (
#             "Ask optimization-focused follow-ups. Example: "
#             "'How would you optimize that query for larger datasets?' or "
#             "'What improvements would you make if given more time?'"
#         ),
#     },
#     "Senior Developer": {
#         "description": "senior developer interview (3+ years experience)",
#         "focus": [
#             "Scalability and system design",
#             "High availability and fault tolerance",
#             "Database architecture for high traffic",
#             "Microservices design and trade-offs",
#             "Caching strategies (Redis, CDN, etc.)",
#             "Cloud infrastructure and DevOps practices",
#             "Performance engineering and profiling",
#             "Technical leadership and architectural decisions",
#             "Technologies from resume and JD",
#         ],
#         "avoid": [
#             "DSA and algorithmic problems",
#             "Basic beginner-level questions",
#         ],
#         "followup_style": (
#             "Ask architecture-focused follow-ups. Example: "
#             "'How would you redesign this system for 10x traffic?' or "
#             "'What trade-offs did you consider when choosing this approach?'"
#         ),
#     },
# }


# def generate_question(
#     resume_data: dict,
#     jd_data: dict,
#     gap_data: dict,
#     previous_questions: list[str],
#     previous_answers: list[str],
#     last_score: float = 5.0,
#     candidate_level: str = "Junior Developer",
# ) -> str:
#     """
#     Generate the next technical interview question based on candidate profile,
#     session history, and candidate level.

#     Adapts question depth based on last_score:
#       - >= 7 : deeper follow-up within the level's scope
#       - < 4  : simpler foundational question within the level's scope
#       - else : standard question for the level

#     Returns question text only.
#     """
#     config = LEVEL_CONFIG.get(candidate_level, LEVEL_CONFIG["Junior Developer"])

#     # Determine within-level depth adjustment based on performance
#     if last_score >= 7:
#         depth_note = "Ask a deeper, more challenging question within this level's scope."
#     elif last_score < 4:
#         depth_note = "Ask a more fundamental, straightforward question within this level's scope."
#     else:
#         depth_note = "Ask a standard question appropriate for this level."

#     candidate_projects = [
#         f"{p.get('name', '')}: {p.get('description', '')} (technologies: {', '.join(p.get('technologies', []))})"
#         for p in resume_data.get("projects", [])
#     ]

#     previous_q_str = (
#         "\n".join(f"- {q}" for q in previous_questions)
#         if previous_questions else "None"
#     )

#     focus_str = "\n".join(f"- {f}" for f in config["focus"])
#     avoid_str = "\n".join(f"- {a}" for a in config["avoid"])

#     prompt = f"""You are a technical interviewer conducting a {config['description']}.

# Candidate Level: {candidate_level}

# Candidate Profile:
# - Skills: {json.dumps(resume_data.get('skills', []))}
# - Projects: {json.dumps(candidate_projects)}
# - Matched JD skills: {json.dumps(gap_data.get('matched_skills', []))}
# - Missing skills (gaps): {json.dumps(gap_data.get('missing_skills', []))}
# - JD required skills: {json.dumps(jd_data.get('required_skills', []))}
# - JD responsibilities: {json.dumps(jd_data.get('responsibilities', []))}

# Question Focus Areas (choose from these):
# {focus_str}

# Topics to AVOID (do NOT ask about these):
# {avoid_str}

# Depth instruction: {depth_note}

# Follow-up style for this level: {config['followup_style']}

# Previous questions already asked (DO NOT repeat):
# {previous_q_str}

# Question priority:
# 1. Candidate's resume projects and implementation details
# 2. Technologies present in both resume and JD
# 3. Technologies required in JD but missing from resume
# 4. Behavioral/situational questions relevant to the role

# Generate exactly ONE technical interview question for a {candidate_level}.
# Return ONLY the question text, nothing else."""

#     return generate_response(prompt).strip()



import json
from utils.llm import generate_response

# Per-level configuration: what to focus on and what to avoid
LEVEL_CONFIG = {
    "Intern": {
        "description": "internship/fresher technical round",
        "focus": [
            "Resume projects and implementation details",
            "Technology choices made in projects (why MongoDB, why React, etc.)",
            "How frontend and backend were connected",
            "REST APIs implemented in projects",
            "Authentication mechanisms used",
            "Databases used and basic schema design",
            "Frameworks and libraries from resume",
            "Challenges faced during development",
        ],
        "avoid": [
            "System Design",
            "Scalability and distributed systems",
            "Load balancing and caching architectures",
            "Sharding and replication strategies",
            "Microservices architecture",
            "DSA and algorithmic problems",
            "Cloud infrastructure design",
        ],
        "followup_style": (
            "Ask implementation-focused follow-ups, technology-choice questions, "
            "and challenge-based questions. Example: if asked about MongoDB, "
            "follow up with 'What specific advantages of MongoDB helped in your project?'"
        ),
    },
    "Junior Developer": {
        "description": "junior developer interview (0-2 years experience)",
        "focus": [
            "Project architecture and design decisions",
            "API design and security (authentication, authorization)",
            "Database query optimization",
            "Error handling and input validation strategies",
            "Deployment basics (CI/CD, Docker basics)",
            "Performance improvements made or considered",
            "Code quality and maintainability practices",
            "Technologies from resume and JD",
        ],
        "avoid": [
            "Deep distributed systems",
            "Large-scale system design (millions of users)",
            "DSA and algorithmic problems",
            "Advanced cloud infrastructure",
        ],
        "followup_style": (
            "Ask optimization-focused follow-ups. Example: "
            "'How would you optimize that query for larger datasets?' or "
            "'What improvements would you make if given more time?'"
        ),
    },
    "Senior Developer": {
        "description": "senior developer interview (3+ years experience)",
        "focus": [
            "Scalability and system design",
            "High availability and fault tolerance",
            "Database architecture for high traffic",
            "Microservices design and trade-offs",
            "Caching strategies (Redis, CDN, etc.)",
            "Cloud infrastructure and DevOps practices",
            "Performance engineering and profiling",
            "Technical leadership and architectural decisions",
            "Technologies from resume and JD",
        ],
        "avoid": [
            "DSA and algorithmic problems",
            "Basic beginner-level questions",
        ],
        "followup_style": (
            "Ask architecture-focused follow-ups. Example: "
            "'How would you redesign this system for 10x traffic?' or "
            "'What trade-offs did you consider when choosing this approach?'"
        ),
    },
}

# NEW: Human Interviewer Prompt
INTERVIEWER_SYSTEM_PROMPT = """
You are an experienced Software Engineer and Technical Interviewer conducting a real job interview.

Your goal is NOT to test the candidate like an exam paper.

Your goal is to understand:

- What the candidate has actually built
- Whether the candidate understands the technologies listed on their resume
- Whether the candidate meets the requirements of the job description
- The depth of the candidate's practical experience

INTERVIEW STYLE

You must behave like a human interviewer.

Questions must sound natural, conversational, and realistic.

Ask questions exactly as a real interviewer would ask them during a live interview.

Never sound like:

- A textbook
- An exam paper
- A research paper
- An AI assistant

Avoid:

- Long questions
- Multi-part questions
- Academic language
- Corporate jargon
- Buzzwords
- Overly formal wording

Do not ask more than ONE question at a time.

Keep questions concise.

Most questions should be under 20 words.

GOOD EXAMPLES

- Can you walk me through this project?
- Why did you choose MongoDB?
- What was the hardest part of building this?
- How did you handle authentication?
- How did the frontend talk to the backend?
- What challenge did you face while building this?

BAD EXAMPLES

- Explain the architectural considerations involved in selecting MongoDB.
- Discuss the scalability implications of your implementation strategy.
- Elaborate on the methodology used for integrating frontend and backend systems.

FOLLOW-UP RULES

If the candidate performs well:

- Ask a deeper follow-up on the SAME topic.
- Do NOT jump to system design.
- Do NOT jump to scalability.
- Explore implementation details further.

Example:

Question:
Why did you choose MongoDB?

Good follow-up:
What MongoDB feature helped you the most in this project?

Bad follow-up:
How would you scale MongoDB for 100 million users?

If the candidate performs poorly:

- Ask a simpler foundational question.
- Help uncover their actual understanding.

Return ONLY the interview question.
"""


def generate_question(
    resume_data: dict,
    jd_data: dict,
    gap_data: dict,
    previous_questions: list[str],
    previous_answers: list[str],
    last_score: float = 5.0,
    candidate_level: str = "Junior Developer",
) -> str:
    """
    Generate the next technical interview question based on candidate profile,
    session history, and candidate level.

    Adapts question depth based on last_score:
      - >= 7 : deeper follow-up within the level's scope
      - < 4  : simpler foundational question within the level's scope
      - else : standard question for the level

    Returns question text only.
    """

    config = LEVEL_CONFIG.get(candidate_level, LEVEL_CONFIG["Junior Developer"])

    if last_score >= 7:
        depth_note = (
            "The candidate answered well. "
            "Ask a deeper follow-up on the SAME topic. "
            "Do NOT move into system design or scalability. "
            "Explore implementation details further."
        )
    elif last_score < 4:
        depth_note = (
            "The candidate struggled. "
            "Ask a simpler and more foundational question on the same topic."
        )
    else:
        depth_note = (
            "Ask a standard interview question appropriate for this level."
        )

    candidate_projects = [
        f"{p.get('name', '')}: {p.get('description', '')} "
        f"(technologies: {', '.join(p.get('technologies', []))})"
        for p in resume_data.get("projects", [])
    ]

    previous_q_str = (
        "\n".join(f"- {q}" for q in previous_questions)
        if previous_questions else "None"
    )

    focus_str = "\n".join(f"- {f}" for f in config["focus"])
    avoid_str = "\n".join(f"- {a}" for a in config["avoid"])

    prompt = f"""
{INTERVIEWER_SYSTEM_PROMPT}

Candidate Level:
{candidate_level}

Interview Type:
{config['description']}

Candidate Profile:

Skills:
{json.dumps(resume_data.get('skills', []), indent=2)}

Projects:
{json.dumps(candidate_projects, indent=2)}

Matched JD Skills:
{json.dumps(gap_data.get('matched_skills', []), indent=2)}

Missing Skills:
{json.dumps(gap_data.get('missing_skills', []), indent=2)}

JD Required Skills:
{json.dumps(jd_data.get('required_skills', []), indent=2)}

JD Responsibilities:
{json.dumps(jd_data.get('responsibilities', []), indent=2)}

Focus Areas:
{focus_str}

Topics To Avoid:
{avoid_str}

Question Depth Guidance:
{depth_note}

Follow-Up Style:
{config['followup_style']}

Previous Questions Already Asked:
{previous_q_str}

Question Priority:

1. Candidate's resume projects
2. Technologies used in projects
3. Skills common between resume and JD
4. Missing skills required by JD
5. Practical implementation details
6. Challenges faced during development
7. Behavioral questions relevant to the role

IMPORTANT:

- Ask exactly ONE question.
- Sound like a human interviewer.
- Use conversational English.
- Keep the question short.
- Avoid AI-generated sounding language.
- Avoid academic wording.
- Avoid multiple questions in one sentence.
- Do not repeat previous questions.

Return ONLY the interview question.
"""

    return generate_response(prompt).strip()