import asyncio
import time
from typing import Optional, Dict, Any

from interview_brain.domain.state import InterviewState, InterviewStatus, InterviewProgress, InterviewTimers
from interview_brain.domain.value_objects import QuestionType
from interview_brain.application.interfaces import IQuestionGenerator, ITechnicalEvaluator
from interview_brain.infrastructure.state_update_engine import StateUpdateEngine
from interview_brain.infrastructure.adaptive_difficulty_engine import AdaptiveDifficultyEngine
from resume_analyser.domain.entities import AnalyserOutput
from core.logger import get_logger

logger = get_logger("InterviewOrchestrator")

class InterviewOrchestrator:
    def __init__(self, q_gen: IQuestionGenerator, tech_eval: ITechnicalEvaluator):
        self.q_gen = q_gen
        self.tech_eval = tech_eval
        
    def initialize_session(self, session_id: str, intelligence_payload: AnalyserOutput) -> InterviewState:
        """Component 1: Session Initializer logic."""
        logger.info(f"Initializing Interview Session: {session_id}")
        
        blueprint = intelligence_payload.interview_blueprint
        
        # Merge topics
        all_topics = blueprint.priority_topics + blueprint.resume_specific_topics
        if not all_topics:
            all_topics = ["General Software Engineering"]
            
        progress = InterviewProgress(
            current_topic=all_topics[0],
            current_difficulty=blueprint.initial_difficulty_rating,
            question_queue=all_topics[1:]
        )
        
        timers = InterviewTimers(
            total_allowed_mins=blueprint.estimated_interview_length_mins
        )
        
        state = InterviewState(
            session_id=session_id,
            intelligence_payload=intelligence_payload,
            progress=progress,
            timers=timers,
            status=InterviewStatus.IN_PROGRESS
        )
        return state

    async def run_interview_loop_demo(self, state: InterviewState):
        """
        Runs a simulated orchestrator loop for testing.
        In a real application, this would be broken into API endpoints 
        or integrated directly with the Speech pipeline via callbacks.
        """
        logger.info("=== STARTING INTERVIEW ORCHESTRATION LOOP ===")
        
        for turn in range(3): # Run 3 turns for demo
            if state.timers.elapsed_time_seconds > state.timers.total_allowed_mins * 60:
                logger.info("Time is up! Ending interview.")
                state.status = InterviewStatus.COMPLETED
                break
                
            # 1. GENERATE QUESTION
            logger.info(f"--- Turn {turn+1} ---")
            state.status = InterviewStatus.GENERATING
            q_data = await self.q_gen.generate_next_question(state)
            
            logger.info(f"Agent asks: {q_data['question_text']}")
            
            # 2. CANDIDATE SPEAKS (Simulated Input)
            state.status = InterviewStatus.IN_PROGRESS
            candidate_answer = "I would use a distributed caching layer and optimize the queries using proper indexes."
            logger.info(f"Candidate answers: {candidate_answer}")
            
            # 3. CONCURRENT EVALUATION AND NEXT QUESTION PRE-GENERATION
            # To optimize latency, we evaluate the answer and pre-generate the next question concurrently.
            state.status = InterviewStatus.EVALUATING
            logger.info("Running Concurrent Evaluation & Pre-generation...")
            
            # We pass the state to evaluate. In reality, we'd fire these off asynchronously.
            eval_data = await self.tech_eval.evaluate_answer(state, candidate_answer)
            
            # 4. STATE UPDATE
            logger.info("Updating State (Deterministic)...")
            StateUpdateEngine.log_qa_turn(state, q_data, candidate_answer, eval_data)
            StateUpdateEngine.recalculate_topic_scores(state)
            
            # 5. ADAPTIVE DIFFICULTY
            logger.info("Adapting Difficulty (Deterministic)...")
            AdaptiveDifficultyEngine.adapt(state)
            
            await asyncio.sleep(0.5)
            
        state.status = InterviewStatus.COMPLETED
        logger.info("=== INTERVIEW LOOP COMPLETED ===")
        return state
