from typing import Dict, Any
import time
from interview_brain.domain.state import InterviewState, QALog

class StateUpdateEngine:
    """
    Deterministic rule-based engine to safely update the Interview State.
    Keeps the LLM out of state mutation logic.
    """
    
    @staticmethod
    def log_qa_turn(state: InterviewState, q_data: Dict[str, Any], answer: str, eval_data: Dict[str, Any]) -> None:
        """Appends a new turn to the history and updates timers."""
        
        log_entry = QALog(
            question_text=q_data["question_text"],
            question_type=q_data["question_type"],
            topic=q_data["topic"],
            difficulty=q_data["difficulty"],
            candidate_answer_text=answer,
            correctness_score=eval_data["correctness_score"],
            completeness_score=eval_data["completeness_score"],
            communication_score=eval_data["communication_score"],
            evaluation_rationale=eval_data["evaluation_rationale"]
        )
        state.history.qa_log.append(log_entry)
        
        # Update Timer
        state.timers.elapsed_time_seconds = int(time.time() - state.timers.start_time_unix)
        
    @staticmethod
    def recalculate_topic_scores(state: InterviewState) -> None:
        """Averages the correctness scores for all questions under each topic."""
        scores_by_topic = {}
        for log in state.history.qa_log:
            if log.topic not in scores_by_topic:
                scores_by_topic[log.topic] = []
            scores_by_topic[log.topic].append(log.correctness_score)
            
        for topic, scores in scores_by_topic.items():
            state.history.topic_scores[topic] = sum(scores) / len(scores)
