from enum import Enum

class QuestionType(str, Enum):
    INITIAL = "initial"
    DEEP_DIVE = "deep_dive"
    FOLLOW_UP_CLARIFICATION = "follow_up_clarification"
    HINT = "hint"
    TOPIC_TRANSITION = "topic_transition"

class InterviewStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    EVALUATING = "evaluating"
    GENERATING = "generating"
    COMPLETED = "completed"
