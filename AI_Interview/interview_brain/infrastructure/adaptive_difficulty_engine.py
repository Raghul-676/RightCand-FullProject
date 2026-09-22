from interview_brain.domain.state import InterviewState
from core.logger import get_logger

logger = get_logger("AdaptiveDifficultyEngine")

class AdaptiveDifficultyEngine:
    """
    Determines if the AI should make the interview harder, easier, 
    or switch topics entirely, based on the last evaluation.
    """
    
    @staticmethod
    def adapt(state: InterviewState) -> None:
        if not state.history.qa_log:
            return
            
        last_log = state.history.qa_log[-1]
        score = last_log.correctness_score
        
        logger.info(f"Adaptive Engine assessing score: {score}/10 on topic '{last_log.topic}'")
        
        if score >= 8:
            if state.progress.current_difficulty < 10:
                state.progress.current_difficulty += 1
                logger.info(f"Candidate doing well. Increasing difficulty to {state.progress.current_difficulty}.")
            else:
                # Mastered the topic, force transition
                logger.info(f"Candidate mastered topic. Popping next topic.")
                AdaptiveDifficultyEngine._transition_topic(state)
                
        elif score < 5:
            if state.progress.current_difficulty > 1:
                state.progress.current_difficulty -= 1
                logger.info(f"Candidate struggling. Decreasing difficulty to {state.progress.current_difficulty}.")
            else:
                logger.info(f"Candidate failed topic at lowest difficulty. Moving on.")
                AdaptiveDifficultyEngine._transition_topic(state)

    @staticmethod
    def _transition_topic(state: InterviewState) -> None:
        state.progress.completed_topics.append(state.progress.current_topic)
        if state.progress.question_queue:
            state.progress.current_topic = state.progress.question_queue.pop(0)
            # Reset difficulty to the baseline blueprint difficulty for the new topic
            state.progress.current_difficulty = state.intelligence_payload.interview_blueprint.initial_difficulty_rating
        else:
            logger.info("No more topics left in queue.")
