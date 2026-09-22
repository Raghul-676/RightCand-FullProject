from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import time

from interview_brain.domain.value_objects import QuestionType, InterviewStatus
from resume_analyser.domain.entities import AnalyserOutput

# --- Atomic State Models ---

class QALog(BaseModel):
    question_text: str
    question_type: QuestionType
    topic: str
    difficulty: int
    candidate_answer_text: str
    correctness_score: int = 0
    completeness_score: int = 0
    communication_score: int = 0
    evaluation_rationale: str = ""

class InterviewTimers(BaseModel):
    start_time_unix: float = Field(default_factory=time.time)
    elapsed_time_seconds: int = 0
    total_allowed_mins: int = 45

class InterviewProgress(BaseModel):
    current_topic: str
    current_difficulty: int = Field(..., ge=1, le=10)
    question_queue: List[str]
    completed_topics: List[str] = []

class InterviewHistory(BaseModel):
    qa_log: List[QALog] = []
    topic_scores: Dict[str, float] = {}  # E.g., {"SQL": 8.5}

# --- The Single Source of Truth ---

class InterviewState(BaseModel):
    """
    The Single Source of Truth for the entire interview.
    All deterministic engines and LLM agents read/write to this.
    """
    session_id: str
    status: InterviewStatus = InterviewStatus.NOT_STARTED
    
    # Static info from Phase 2
    intelligence_payload: AnalyserOutput
    
    # Dynamic state
    progress: InterviewProgress
    history: InterviewHistory = Field(default_factory=InterviewHistory)
    timers: InterviewTimers
