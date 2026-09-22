from agents.interview_agent import generate_question


class QuestionGeneratorAgent:
    """
    Question Generator Agent.

    Wraps the existing generate_question() with 4 tools that enrich the context
    before the LLM call, making the question generation more informed and targeted.

    Tools (fixed sequence):
        1. fetch_resume_context  — extracts relevant resume info for current slot
        2. fetch_previous_qa     — retrieves previous questions and answers
        3. fetch_plan_slot       — gets the current slot's topic from the plan
        4. generate              — calls generate_question() with enriched context
    """

    def __init__(
        self,
        resume_data:     dict,
        jd_data:         dict,
        gap_data:        dict,
        interview_plan:  dict,
        previous_questions: list[str],
        previous_answers:   list[str],
        last_score:      float,
        candidate_level: str,
        question_number: int,
    ):
        self.resume_data        = resume_data
        self.jd_data            = jd_data
        self.gap_data           = gap_data
        self.interview_plan     = interview_plan
        self.previous_questions = previous_questions
        self.previous_answers   = previous_answers
        self.last_score         = last_score
        self.candidate_level    = candidate_level
        self.question_number    = question_number
        self.memory             = {}   # stores intermediate tool outputs

    # ── Tool 1 ────────────────────────────────────────────────────────────────

    def fetch_resume_context(self) -> dict:
        """
        Tool 1: Extract the most relevant resume context for the current slot.
        Pulls skills, projects, and experience as a focused subset.
        """
        slot      = self.interview_plan.get(str(self.question_number), {})
        slot_type = slot.get("type", "project")
        topic     = slot.get("topic", "").lower()

        context = {"skills": [], "projects": [], "experience": []}

        if slot_type in ("project", "skill"):
            # Filter projects that relate to the current slot topic
            context["projects"] = [
                p for p in self.resume_data.get("projects", [])
                if topic in p.get("name", "").lower()
                or any(topic in t.lower() for t in p.get("technologies", []))
            ] or self.resume_data.get("projects", [])   # fallback to all if none match

            context["skills"] = [
                s for s in self.resume_data.get("skills", [])
                if topic in s.lower()
            ] or self.resume_data.get("skills", [])

        elif slot_type == "gap":
            context["skills"]  = self.gap_data.get("missing_skills", [])
            context["projects"] = self.resume_data.get("projects", [])

        else:   # behavioral
            context["experience"] = self.resume_data.get("experience", [])
            context["projects"]   = self.resume_data.get("projects", [])

        self.memory["resume_context"] = context
        return context

    # ── Tool 2 ────────────────────────────────────────────────────────────────

    def fetch_previous_qa(self) -> dict:
        """
        Tool 2: Retrieve the last 3 Q&A pairs to give the generator
        short-term context without overwhelming the prompt.
        """
        recent_questions = self.previous_questions[-3:]
        recent_answers   = self.previous_answers[-3:]

        self.memory["recent_qa"] = {
            "questions": recent_questions,
            "answers":   recent_answers,
        }
        return self.memory["recent_qa"]

    # ── Tool 3 ────────────────────────────────────────────────────────────────

    def fetch_plan_slot(self) -> dict:
        """
        Tool 3: Get the current question slot's guidance from the interview plan.
        Returns topic, focus, and type for this question number.
        """
        slot = self.interview_plan.get(str(self.question_number), {
            "topic": "Resume Project",
            "focus": "Implementation details",
            "type":  "project",
        })

        self.memory["current_slot"] = slot
        return slot

    # ── Tool 4 ────────────────────────────────────────────────────────────────

    def generate(self) -> str:
        """
        Tool 4: Call the existing generate_question() with enriched context
        gathered from tools 1-3.

        Injects plan slot guidance into gap_data so the existing function
        receives the richer context without changing its signature.
        """
        slot           = self.memory.get("current_slot", {})
        resume_context = self.memory.get("resume_context", {})
        recent_qa      = self.memory.get("recent_qa", {})

        # Build enriched resume_data using filtered resume context
        enriched_resume = {
            **self.resume_data,
            "projects":   resume_context.get("projects", self.resume_data.get("projects", [])),
            "skills":     resume_context.get("skills",   self.resume_data.get("skills", [])),
            "experience": resume_context.get("experience", self.resume_data.get("experience", [])),
        }

        # Inject plan slot hint into gap_data as extra context
        enriched_gap = {
            **self.gap_data,
            "plan_topic":  slot.get("topic", ""),
            "plan_focus":  slot.get("focus", ""),
            "plan_type":   slot.get("type", ""),
        }

        question = generate_question(
            enriched_resume,
            self.jd_data,
            enriched_gap,
            recent_qa.get("questions", self.previous_questions),
            recent_qa.get("answers",   self.previous_answers),
            self.last_score,
            self.candidate_level,
        )

        self.memory["generated_question"] = question
        return question

    # ── run ───────────────────────────────────────────────────────────────────

    def run(self) -> str:
        """
        Execute all tools in fixed sequence and return the generated question.
        Step 1: fetch_resume_context
        Step 2: fetch_previous_qa
        Step 3: fetch_plan_slot
        Step 4: generate
        """
        self.fetch_resume_context()
        self.fetch_previous_qa()
        self.fetch_plan_slot()
        return self.generate()
