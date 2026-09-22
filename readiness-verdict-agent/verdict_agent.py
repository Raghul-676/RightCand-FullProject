"""
VerdictAgent — decides, turn by turn, which parts of a student's profile to
examine before committing to a placement-readiness verdict, AND now
self-corrects: after emitting a verdict, it checks its own cited_data
against what it actually inspected, and if it lied about its own sources,
it gets told exactly what's wrong and must retry — a real reflect-and-
correct loop, not just a one-shot answer.

Guardrails:
    - MAX_TOOL_CALLS_PER_TURN: hard cap on info-gathering before a verdict
      is forced.
    - MAX_SELF_CORRECTIONS: hard cap on retry attempts after a caught
      citation error, so a confused model can't loop forever.
    - Repeat-call detection: same inspect_* tool + same args twice in a
      row -> forced progression instead of spinning.
    - activity_check is computed deterministically in Python from real
      coding_stats data, never asked of the LLM.
"""
from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone

from groq import Groq, BadRequestError, RateLimitError

from mock_data import get_coding_stats, get_domain_scores, get_interview_history

MODEL = "openai/gpt-oss-120b"
MAX_TOOL_CALLS_PER_TURN = 6
MAX_SELF_CORRECTIONS = 2
INACTIVITY_THRESHOLD_DAYS = 30
LOW_CONTEST_THRESHOLD = 3

# Maps a cited_data source name to the tool call that would actually have
# inspected it — this is the ground truth used to catch false citations.
SOURCE_TO_TOOL = {
    "coding_stats": "inspect_coding_stats",
    "domain_scores": "inspect_domain_scores",
    "interview_history": "inspect_interview_history",
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_coding_stats",
            "description": "Get the student's LeetCode/Codeforces solved counts, ratings, contest counts, and last active date.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_domain_scores",
            "description": "Get the student's per-domain project scores (from the GitHub analyzer) and how many projects back each domain.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_interview_history",
            "description": "Get the student's past mock interview questions, topics, scores, and feedback.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "emit_verdict",
            "description": "Commit to the final readiness verdict. Ends the analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bottleneck": {
                        "type": "string",
                        "description": (
                            "The single biggest gap holding this student back right now. "
                            "If the data doesn't show one dominant weakness — e.g. scores are "
                            "solidly good across coding, domain, and interview performance with "
                            "only minor differences between them — use exactly this value: "
                            "'No significant bottleneck identified — solid across coding, domain, "
                            "and interview performance.' Do not manufacture urgency out of a small "
                            "relative gap (e.g. 72 vs 60) when both numbers are genuinely strong."
                        ),
                    },
                    "next_action": {
                        "type": "string",
                        "description": (
                            "The single highest-leverage thing this student should do next. "
                            "If bottleneck is 'no significant bottleneck', suggest a stretch goal "
                            "instead (e.g. deepen their strongest domain further, or pursue a more "
                            "advanced project) rather than inventing a weakness to fix."
                        ),
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "2-3 sentences justifying the bottleneck and action, citing specific numbers you inspected.",
                    },
                    "cited_data": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Which source(s) you ACTUALLY called an inspect_* tool for and used "
                            "in your reasoning — e.g. ['coding_stats', 'domain_scores']. Only "
                            "include a source here if you genuinely called its inspect tool this "
                            "session. Citing a source you did not inspect will be caught and "
                            "rejected."
                        ),
                    },
                },
                "required": ["bottleneck", "next_action", "reasoning", "cited_data"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are assessing a student's placement readiness for a technical role.

You must inspect the student's actual data before concluding anything - do not guess a
bottleneck without having called the relevant tool. You have three sources you can inspect,
in any order, as many times as needed:
- inspect_coding_stats: DSA/competitive programming strength and recent activity
- inspect_domain_scores: project quality and domain specialization (from real analyzed repos)
- inspect_interview_history: how they actually performed when asked to explain their work live

IMPORTANT REASONING RULES - read carefully, these are common mistakes to avoid:

1. There are TWO DIFFERENT kinds of "depth" problem - do not conflate them:
   a) PROJECT-EXPLANATION depth: interview feedback shows the student struggled to explain
      DESIGN DECISIONS or TRADEOFFS in a project they already built. Fix: revisit and deepen
      understanding of that SPECIFIC existing project.
   b) ALGORITHMIC/CODING depth: interview feedback shows struggling with algorithmic reasoning,
      complexity analysis, or system design AS A SKILL, OR coding_stats shows genuinely weak
      fundamentals. Fix: MORE CODING PRACTICE, not "revisit existing projects."
   Read the interview feedback text carefully to tell which of these two you're looking at.

2. Do not force a bottleneck to exist. If coding stats, domain scores, and interview feedback
   are all solidly good with only minor differences between them, that is NOT a meaningful
   bottleneck - use the "no significant bottleneck" path instead.

3. cited_data must be honest. Only cite a source if you actually called its inspect tool. If you
   claim a source you never inspected, you will be told and required to correct it.

Once you have enough information, call emit_verdict with ONE specific bottleneck, ONE specific
next action, and reasoning that cites the actual numbers you saw. Do not soften this into generic
advice like "keep practicing" - be specific to what you actually observed for this student. Do not
discuss activity/recency in your reasoning - that is handled separately and deterministically."""


class DocumentExtractor:
    """
    Extracts structured student metrics from raw document text using Groq
    """
    def __init__(self):
        pass

    def _client(self) -> Groq:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set.")
        return Groq(api_key=api_key)

    def extract(self, document_text: str) -> dict:
        client = self._client()
        prompt = (
            f"Analyze the following student performance report and extract the student's metrics.\n\n"
            f"--- REPORT START ---\n"
            f"{document_text}\n"
            f"--- REPORT END ---\n\n"
            f"Output the extracted information in raw JSON format strictly matching this schema:\n"
            f"{{\n"
            f"  \"student_name\": string,\n"
            f"  \"coding_stats\": {{\n"
            f"    \"leetcode_solved\": integer,\n"
            f"    \"leetcode_hard_solved\": integer,\n"
            f"    \"leetcode_rating\": integer,\n"
            f"    \"leetcode_contests\": integer,\n"
            f"    \"codeforces_rating\": integer,\n"
            f"    \"codeforces_contests\": integer,\n"
            f"    \"last_active_at\": string (ISO-8601 string or null)\n"
            f"  }},\n"
            f"  \"domain_scores\": [\n"
            f"    {{\n"
            f"      \"domain\": string,\n"
            f"      \"domain_score\": integer,\n"
            f"      \"project_count\": integer\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"interview_history\": [\n"
            f"    {{\n"
            f"      \"question_type\": string (must be one of: 'project', 'behavioral', 'gap', 'matched_skill'),\n"
            f"      \"topic\": string,\n"
            f"      \"overall_score\": number,\n"
            f"      \"feedback\": string\n"
            f"    }}\n"
            f"  ]\n"
            f"}}\n"
        )

        try:
            max_retries = 3
            base_delay = 2.0
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        temperature=0.1,
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a precise JSON extractor. Output ONLY valid JSON matching the requested schema. Never add markdown blocks or notes outside the JSON structure."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    raw_content = response.choices[0].message.content
                    return json.loads(raw_content)
                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    raise
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    raise e
        except Exception as e:
            # Fallback output
            print(f"Extraction failed: {e}")
            return {
                "student_name": "Unknown Student",
                "coding_stats": {
                    "leetcode_solved": 0, "leetcode_hard_solved": 0, "leetcode_rating": 0, "leetcode_contests": 0,
                    "codeforces_rating": 0, "codeforces_contests": 0, "last_active_at": None
                },
                "domain_scores": [],
                "interview_history": []
            }


class VerdictAgent:
    def __init__(self, student_id: str, custom_data: dict | None = None):
        self.student_id = student_id
        self.tool_call_log: list[tuple[str, str]] = []
        self.correction_attempts = 0
        self._coding_stats_seen: dict | None = None
        self.custom_data = custom_data
        self.execution_steps: list[dict] = []

    def _client(self) -> Groq:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set.")
        return Groq(api_key=api_key)

    def _compute_activity_check(self) -> str:
        if self._coding_stats_seen:
            stats = self._coding_stats_seen
        elif self.custom_data:
            stats = self.custom_data.get("coding_stats", {})
        else:
            stats = get_coding_stats(self.student_id)

        last_active_raw = stats.get("last_active_at")
        days_inactive = None
        if last_active_raw:
            try:
                last_active = datetime.fromisoformat(last_active_raw)
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)
                days_inactive = (datetime.now(timezone.utc) - last_active).days
            except Exception:
                days_inactive = None

        total_contests = stats.get("leetcode_contests", 0) + stats.get("codeforces_contests", 0)

        concerns = []
        if days_inactive is not None and days_inactive >= INACTIVITY_THRESHOLD_DAYS:
            concerns.append(f"inactive {days_inactive} days")
        if total_contests <= LOW_CONTEST_THRESHOLD:
            concerns.append(f"only {total_contests} total contests attended")

        if concerns:
            return f"Concern: {', '.join(concerns)}."
        recency = f"active {days_inactive} day(s) ago" if days_inactive is not None else "activity unknown"
        return f"No concern — {recency}, {total_contests} total contests attended."

    def _inspected_sources(self) -> set[str]:
        inspected_tools = {name for name, _ in self.tool_call_log if name != "emit_verdict"}
        return {source for source, tool in SOURCE_TO_TOOL.items() if tool in inspected_tools}

    def run(self) -> dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Assess student '{self.student_id}'. Begin by inspecting whichever data source you think is most informative first."},
        ]
        client = self._client()
        malformed_retries = 0
        MAX_MALFORMED_RETRIES = 2

        for _ in range(MAX_TOOL_CALLS_PER_TURN + MAX_SELF_CORRECTIONS):
            max_api_retries = 3
            api_delay = 2.0
            response = None
            
            for attempt in range(max_api_retries):
                try:
                    response = client.chat.completions.create(
                        model=MODEL,
                        temperature=0.2,
                        messages=messages,
                        tools=TOOLS,
                        tool_choice="auto",
                    )
                    break
                except BadRequestError as e:
                    malformed_retries += 1
                    if malformed_retries > MAX_MALFORMED_RETRIES:
                        return self._fallback_verdict(
                            f"Groq repeatedly failed to generate a valid tool call after "
                            f"{MAX_MALFORMED_RETRIES} retries: {e}"
                        )
                    break  # break inner attempt loop to retry the main turn
                except RateLimitError as e:
                    if attempt < max_api_retries - 1:
                        time.sleep(api_delay * (2 ** attempt))
                        continue
                    raise e
                except Exception as e:
                    if attempt < max_api_retries - 1:
                        time.sleep(api_delay * (2 ** attempt))
                        continue
                    raise e

            if response is None:
                continue  # retry the same turn on bad request/malformed retry

            msg = response.choices[0].message

            # Log assistant details (thought and tool invocation)
            step_tc = []
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    step_tc.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    })
            self.execution_steps.append({
                "type": "assistant",
                "content": msg.content,
                "tool_calls": step_tc
            })

            if not msg.tool_calls:
                return self._fallback_verdict("Model did not call a tool.")

            call = msg.tool_calls[0]
            name = call.function.name
            try:
                args = json.loads(call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            signature = (name, json.dumps(args, sort_keys=True))
            if self.tool_call_log[-1:] == [signature] and name != "emit_verdict":
                return self._fallback_verdict("Model repeated the same inspection twice in a row.")
            self.tool_call_log.append(signature)

            messages.append({
                "role": "assistant", "content": None,
                "tool_calls": [{"id": call.id, "type": "function",
                                 "function": {"name": name, "arguments": call.function.arguments}}],
            })

            if name == "emit_verdict":
                cited = args.get("cited_data", [])
                actually_inspected = self._inspected_sources()
                false_citations = [c for c in cited if c not in actually_inspected]

                if false_citations and self.correction_attempts < MAX_SELF_CORRECTIONS:
                    self.correction_attempts += 1
                    correction_notice = (
                        f"CITATION ERROR: you cited {false_citations} but you never actually "
                        f"called the inspect tool for {[SOURCE_TO_TOOL[c] for c in false_citations]}. "
                        f"You have only genuinely inspected: {sorted(actually_inspected) or 'nothing yet'}. "
                        "Either inspect the missing source(s) now, or re-issue emit_verdict with "
                        "cited_data limited to what you actually inspected."
                    )
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": correction_notice})
                    self.execution_steps.append({
                        "type": "citation_error",
                        "content": correction_notice
                    })
                    continue

                return {
                    "bottleneck": args.get("bottleneck", ""),
                    "next_action": args.get("next_action", ""),
                    "activity_check": self._compute_activity_check(),
                    "reasoning": args.get("reasoning", ""),
                    "cited_data": cited,
                    "tool_calls_used": len(self.tool_call_log),
                    "self_corrections": self.correction_attempts,
                    "uncorrected_false_citations": false_citations,
                    "execution_steps": self.execution_steps,
                }

            if name == "inspect_coding_stats":
                if self.custom_data:
                    self._coding_stats_seen = self.custom_data.get("coding_stats", {})
                else:
                    self._coding_stats_seen = get_coding_stats(self.student_id)
                result = json.dumps(self._coding_stats_seen)
            elif name == "inspect_domain_scores":
                if self.custom_data:
                    scores = self.custom_data.get("domain_scores", [])
                else:
                    scores = get_domain_scores(self.student_id)
                result = json.dumps(scores)
            elif name == "inspect_interview_history":
                if self.custom_data:
                    history = self.custom_data.get("interview_history", [])
                else:
                    history = get_interview_history(self.student_id)
                result = json.dumps(history)
            else:
                result = json.dumps({"error": f"unknown tool {name}"})

            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            self.execution_steps.append({
                "type": "tool",
                "name": name,
                "content": result
            })

        return self._fallback_verdict("Exceeded max tool calls without reaching a clean verdict.")

    def _fallback_verdict(self, reason: str) -> dict:
        return {
            "bottleneck": "Unable to determine — agent did not complete analysis.",
            "next_action": "Retry the assessment.",
            "activity_check": self._compute_activity_check(),
            "reasoning": reason,
            "cited_data": [],
            "tool_calls_used": len(self.tool_call_log),
            "self_corrections": self.correction_attempts,
            "uncorrected_false_citations": [],
            "fallback": True,
            "execution_steps": self.execution_steps,
        }