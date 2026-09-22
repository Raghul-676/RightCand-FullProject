# Readiness Verdict Agent — standalone prototype

## What this is

A tool-calling agent that inspects a student's coding stats, project domain
scores, and mock interview history, then commits to ONE specific bottleneck
and ONE next action — grounded in the actual numbers it looked at, same
citation discipline as your GitHub analyzer and Interview Prep Assistant.

## Test it standalone (no DB, no server, no UI)

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
python3 test_verdict.py
```

This runs the agent against three mock personas (`mock_data.py`):
- **strong_coder_weak_projects** — great DSA, thin/shallow projects
- **strong_projects_weak_coding** — deep projects, weak fundamentals, also inactive 40 days
- **well_rounded** — solid across the board

Read the printed output for each. What you're checking for:
- Does the bottleneck actually match the persona's designed weak point?
- Is `cited_data` non-empty and does `reasoning` reference real numbers,
  not generic advice like "keep practicing DSA"?
- Does `tool_calls_used` stay well under `MAX_TOOL_CALLS_PER_TURN` (6)?
  If it's regularly hitting the cap, the guardrail is masking real
  reasoning failures — worth investigating before integrating.

## What changes when you wire this into the real project

`mock_data.py`'s three functions (`get_coding_stats`, `get_domain_scores`,
`get_interview_history`) are the ONLY thing that needs to change. Replace
each with a real DB query against `CodingStats`, `DomainScore`, and wherever
you end up persisting interview evaluations (not yet a DB table in your
current Streamlit-based Interview Prep Assistant — you'll need to decide
where that lives before this piece can use real interview data; until then
you could ship this with just coding_stats + domain_scores, no
interview_history, and adjust the tool list accordingly).

`verdict_agent.py` itself needs zero changes — it only depends on those
three functions' *return shape*, which mock_data.py already matches
byte-for-byte against your real `CodingStats`/`DomainScore` model fields.

## Known gaps in this standalone version (fix before hackathon demo)

- No caching — every call re-runs the full agent loop, costing a Groq
  call per tool inspection. Fine for testing, not for a live demo hitting
  it repeatedly.
- No FastAPI endpoint yet — deliberately, since you said you want to
  validate the logic before touching the real app. Once you're happy with
  the outputs, wrap `VerdictAgent(student_id).run()` in a route.
- `emit_verdict`'s `cited_data` is self-reported by the model, not
  independently validated against which tools were actually called (unlike
  your GitHub analyzer's validator.py, which cross-checks citations
  against real evidence). Worth adding that same validation layer here —
  compare `cited_data` against `self.tool_call_log` — before you'd call
  this launch-ready.
