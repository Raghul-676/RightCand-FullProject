"""
Quick validation script - no server, no UI. Run this directly to confirm
the agent reasons sensibly before wiring it into the real project.

Usage:
    export GROQ_API_KEY=your_key_here
    python3 test_verdict.py
"""
from verdict_agent import VerdictAgent
from mock_data import MOCK_STUDENTS

for student_id in MOCK_STUDENTS:
    print(f"\n{'=' * 70}")
    print(f"STUDENT: {student_id}")
    print("=" * 70)

    agent = VerdictAgent(student_id)
    verdict = agent.run()

    print(f"Bottleneck:   {verdict['bottleneck']}")
    print(f"Next action:  {verdict['next_action']}")
    print(f"Activity check: {verdict['activity_check']}")
    print(f"Reasoning:    {verdict['reasoning']}")
    print(f"Cited data:   {verdict['cited_data']}")
    print(f"Tool calls used: {verdict['tool_calls_used']}")
    print(f"Self-corrections: {verdict['self_corrections']}")
    if verdict.get("uncorrected_false_citations"):
        print(f"*** STILL LYING ABOUT CITATIONS AFTER {MAX_SELF_CORRECTIONS} RETRIES: {verdict['uncorrected_false_citations']} ***")
    if verdict.get("fallback"):
        print("*** FELL BACK - agent did not reach a clean verdict ***")
