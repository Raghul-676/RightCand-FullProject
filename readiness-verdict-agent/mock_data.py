"""
Mock student profiles for standalone testing, shaped exactly like your real
schemas (CodingStats, DomainScore from models.py; interview evaluations
shaped like evaluation_agent.py's output). When you integrate this into the
real project, swap the functions below for real DB queries — the shape
returned must stay identical, since verdict_agent.py's tools depend on it.
"""
from datetime import datetime, timedelta

MOCK_STUDENTS = {
    "strong_coder_weak_projects": {
        "coding_stats": {
            "leetcode_solved": 420,
            "leetcode_hard_solved": 55,
            "leetcode_rating": 1850,
            "leetcode_contests": 22,
            "codeforces_rating": 1600,
            "codeforces_contests": 18,
            "last_active_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        },
        "domain_scores": [
            {"domain": "Web Development - Full Stack", "domain_score": 28, "project_count": 1},
        ],
        "interview_history": [
            {"question_type": "project", "topic": "Full Stack project", "overall_score": 4.5,
             "feedback": "Struggled to explain design decisions beyond surface level."},
            {"question_type": "behavioral", "topic": "teamwork", "overall_score": 7.0,
             "feedback": "Clear and confident communication."},
        ],
    },
    "strong_projects_weak_coding": {
        "coding_stats": {
            "leetcode_solved": 45,
            "leetcode_hard_solved": 2,
            "leetcode_rating": 1200,
            "leetcode_contests": 3,
            "codeforces_rating": 0,
            "codeforces_contests": 0,
            "last_active_at": (datetime.utcnow() - timedelta(days=40)).isoformat(),
        },
        "domain_scores": [
            {"domain": "ML/AI - Computer Vision", "domain_score": 78, "project_count": 3},
            {"domain": "Web Development - Full Stack", "domain_score": 65, "project_count": 2},
        ],
        "interview_history": [
            {"question_type": "project", "topic": "Computer Vision project", "overall_score": 8.5,
             "feedback": "Deep understanding of the model architecture and tradeoffs."},
            {"question_type": "gap", "topic": "system design", "overall_score": 3.0,
             "feedback": "Could not reason through basic algorithmic complexity."},
        ],
    },
    "well_rounded": {
        "coding_stats": {
            "leetcode_solved": 280,
            "leetcode_hard_solved": 30,
            "leetcode_rating": 1650,
            "leetcode_contests": 16,
            "codeforces_rating": 1400,
            "codeforces_contests": 12,
            "last_active_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        },
        "domain_scores": [
            {"domain": "Web Development - Full Stack", "domain_score": 72, "project_count": 3},
            {"domain": "Data Engineering", "domain_score": 60, "project_count": 1},
        ],
        "interview_history": [
            {"question_type": "project", "topic": "Full Stack project", "overall_score": 7.5,
             "feedback": "Solid explanation with minor gaps on scaling considerations."},
            {"question_type": "matched_skill", "topic": "React", "overall_score": 8.0,
             "feedback": "Strong grasp of component design patterns."},
        ],
    },
}


def get_coding_stats(student_id: str) -> dict:
    return MOCK_STUDENTS[student_id]["coding_stats"]


def get_domain_scores(student_id: str) -> list[dict]:
    return MOCK_STUDENTS[student_id]["domain_scores"]


def get_interview_history(student_id: str) -> list[dict]:
    return MOCK_STUDENTS[student_id]["interview_history"]
