from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from interview_brain.domain.state import InterviewState

class IQuestionGenerator(ABC):
    """
    Interface for the LLM agent that generates the next technical question.
    """
    @abstractmethod
    async def generate_next_question(self, state: InterviewState) -> Dict[str, Any]:
        """
        Returns JSON containing:
        {
            "question_text": "...",
            "question_type": "deep_dive",
            "topic": "...",
            "difficulty": 8,
            "tts_priority": "normal"
        }
        """
        pass

class ITechnicalEvaluator(ABC):
    """
    Interface for the LLM agent that evaluates the candidate's answer.
    """
    @abstractmethod
    async def evaluate_answer(self, state: InterviewState, answer_text: str) -> Dict[str, Any]:
        """
        Returns JSON containing:
        {
            "correctness_score": 8,
            "completeness_score": 7,
            "communication_score": 9,
            "evaluation_rationale": "..."
        }
        """
        pass
