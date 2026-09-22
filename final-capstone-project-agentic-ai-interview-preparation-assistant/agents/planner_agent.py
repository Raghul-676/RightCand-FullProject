import json
from utils.llm import generate_json_response


class PlannerAgent:
    """
    Interview Planner Agent.

    Runs once after gap analysis to create a flexible 10-question interview plan.

    Tools (fixed sequence):
        1. prioritize_gaps     — identifies critical missing skills
        2. allocate_topic_slots — distributes 10 slots across topics
        3. plan_questions       — generates the final flexible guide via LLM
    """

    def __init__(self, resume_data: dict, jd_data: dict, gap_data: dict, candidate_level: str):
        self.resume_data     = resume_data
        self.jd_data         = jd_data
        self.gap_data        = gap_data
        self.candidate_level = candidate_level
        self.memory          = {}   # stores intermediate tool outputs

    # ── Tool 1 ────────────────────────────────────────────────────────────────

    def prioritize_gaps(self) -> list[str]:
        """
        Tool 1: Identify critical missing skills by cross-referencing
        gap_data missing skills against jd required skills.
        Returns a ranked list of critical gaps.
        """
        missing  = self.gap_data.get("missing_skills", [])
        required = self.jd_data.get("required_skills", [])

        # Skills that are both missing AND explicitly required are critical
        critical = [s for s in missing if any(s.lower() in r.lower() or r.lower() in s.lower() for r in required)]

        # Append remaining missing skills that didn't match directly
        others = [s for s in missing if s not in critical]

        self.memory["critical_gaps"] = critical + others
        return self.memory["critical_gaps"]

    # ── Tool 2 ────────────────────────────────────────────────────────────────

    def allocate_topic_slots(self) -> dict:
        """
        Tool 2: Distribute 10 question slots across topic categories.
        Returns a dict with topic -> number of slots.
        """
        critical_gaps   = self.memory.get("critical_gaps", [])
        matched_skills  = self.gap_data.get("matched_skills", [])
        projects        = self.resume_data.get("projects", [])
        responsibilities = self.jd_data.get("responsibilities", [])

        # Slot allocation logic based on what's available
        project_slots    = 4 if projects else 2
        matched_slots    = 2 if matched_skills else 1
        gap_slots        = 3 if critical_gaps else 1
        behavioral_slots = 10 - project_slots - matched_slots - gap_slots

        allocation = {
            "resume_projects":    project_slots,
            "matched_skills":     matched_slots,
            "missing_skills":     gap_slots,
            "behavioral":         max(behavioral_slots, 1),
        }

        self.memory["slot_allocation"] = allocation
        return allocation

    # ── Tool 3 ────────────────────────────────────────────────────────────────

    def plan_questions(self) -> dict:
        """
        Tool 3: Use LLM to generate a flexible 10-question interview plan
        based on the slot allocation and candidate profile.
        Returns a dict with slot number -> topic/focus guidance.
        """
        allocation  = self.memory.get("slot_allocation", {})
        critical_gaps = self.memory.get("critical_gaps", [])
        projects    = [p.get("name", "") for p in self.resume_data.get("projects", [])]
        matched     = self.gap_data.get("matched_skills", [])

        prompt = f"""You are an experienced technical interviewer planning a structured interview.

Candidate Level: {self.candidate_level}

Slot Allocation for 10 questions:
- Resume project questions: {allocation.get('resume_projects', 4)}
- Matched skill questions: {allocation.get('matched_skills', 2)}
- Missing skill questions: {allocation.get('missing_skills', 3)}
- Behavioral questions: {allocation.get('behavioral', 1)}

Candidate Projects: {json.dumps(projects)}
Matched Skills: {json.dumps(matched)}
Critical Gaps: {json.dumps(critical_gaps)}

Create a flexible interview plan for exactly 10 questions.
Each slot should specify the topic focus and suggested approach.
This is a GUIDE, not a strict script. The interviewer can adapt based on answers.

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "1": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "2": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "3": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "4": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "5": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "6": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "7": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "8": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "9": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}},
  "10": {{"topic": "topic name", "focus": "what to explore", "type": "project|skill|gap|behavioral"}}
}}"""

        response = generate_json_response(prompt)

        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            plan = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback plan if LLM response fails to parse
            plan = {
                str(i): {"topic": "Resume Project", "focus": "Implementation details", "type": "project"}
                for i in range(1, 11)
            }

        self.memory["plan"] = plan
        return plan

    # ── run ───────────────────────────────────────────────────────────────────

    def run(self) -> dict:
        """
        Execute all tools in fixed sequence and return the final interview plan.
        Step 1: prioritize_gaps
        Step 2: allocate_topic_slots
        Step 3: plan_questions
        """
        self.prioritize_gaps()
        self.allocate_topic_slots()
        plan = self.plan_questions()
        return plan
