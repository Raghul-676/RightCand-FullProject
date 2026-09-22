import asyncio
import os
import json
from typing import Dict, Any
from interview_brain.application.interfaces import IQuestionGenerator, ITechnicalEvaluator
from interview_brain.domain.state import InterviewState
from core.logger import get_logger

try:
    from groq import AsyncGroq
except ImportError:
    pass

logger = get_logger("LLMAgents")

class MockQuestionGenerator(IQuestionGenerator):
    """Mock implementation to allow testing the orchestrator loop without API keys."""
    
    async def generate_next_question(self, state: InterviewState) -> Dict[str, Any]:
        logger.info("LLM: Generating next question...")
        await asyncio.sleep(1) # Simulate LLM latency
        
        topic = state.progress.current_topic
        diff = state.progress.current_difficulty
        
        return {
            "question_text": f"At a difficulty of {diff}, how would you implement {topic}?",
            "question_type": "deep_dive",
            "topic": topic,
            "difficulty": diff,
            "tts_priority": "normal"
        }

class MockTechnicalEvaluator(ITechnicalEvaluator):
    """Mock implementation to score the candidate."""
    
    async def evaluate_answer(self, state: InterviewState, answer_text: str) -> Dict[str, Any]:
        logger.info("LLM: Evaluating answer...")
        await asyncio.sleep(1) # Simulate LLM latency
        
        # Simple heuristic for testing: longer answer = better score
        length = len(answer_text.split())
        score = min(10, max(2, length // 2))
        
        return {
            "correctness_score": score,
            "completeness_score": score,
            "communication_score": score,
            "evaluation_rationale": "Mock rationale based on answer length."
        }

class GroqQuestionGenerator(IQuestionGenerator):
    def __init__(self):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        
    async def generate_next_question(self, state: InterviewState) -> Dict[str, Any]:
        logger.info(f"Groq LLM: Generating next question on topic {state.progress.current_topic} at difficulty {state.progress.current_difficulty}...")
        
        # Extract context to minimize tokens
        profile = state.intelligence_payload.candidate_profile
        history_summary = "\n".join([f"Q: {log.question_text}\nA: {log.candidate_answer_text}\nScore: {log.correctness_score}/10" for log in state.history.qa_log[-2:]])
        
        system_prompt = f"""
You are a Senior Staff Software Engineer conducting a technical interview for a {profile.identity.current_role} position.
Your candidate is {profile.identity.name} with {profile.experience.years_of_experience} years of experience.
You do NOT talk like an AI assistant. Be professional, sharp, and concise.
Ask exactly ONE technical question. 
If the candidate rambles, interrupt politely. If they struggle, provide a tiny hint but never reveal the answer.

CURRENT INTERVIEW STATE:
- Target Topic: {state.progress.current_topic}
- Target Difficulty (1-10): {state.progress.current_difficulty}
- Remaining Time: {state.timers.total_allowed_mins * 60 - state.timers.elapsed_time_seconds} seconds

RECENT CONVERSATION HISTORY:
{history_summary if history_summary else "No history yet. This is the first question."}

Respond ONLY in valid JSON matching this exact schema:
{{
    "question_text": "string (the exact words you will speak)",
    "question_type": "string (initial | deep_dive | follow_up_clarification | hint | topic_transition)",
    "topic": "string",
    "difficulty": int (1-10),
    "tts_priority": "string (normal | high)"
}}
"""
        
        response = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": "Generate the next question."
                }
            ],
            model=self.model,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Failed to parse Groq response: {e}")
            return {
                "question_text": "I'm having a technical issue, but let's continue. Can you elaborate on your last point?",
                "question_type": "fallback",
                "topic": state.progress.current_topic,
                "difficulty": state.progress.current_difficulty,
                "tts_priority": "normal"
            }

class GroqTechnicalEvaluator(ITechnicalEvaluator):
    def __init__(self):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        
    async def evaluate_answer(self, state: InterviewState, answer_text: str) -> Dict[str, Any]:
        logger.info("Groq LLM: Evaluating answer...")
        
        if not state.history.qa_log:
            last_q = "Tell me about your background."
            last_topic = "General"
            diff = 5
        else:
            last_log = state.history.qa_log[-1]
            last_q = last_log.question_text
            last_topic = last_log.topic
            diff = last_log.difficulty
            
        system_prompt = f"""
You are the Technical Evaluation Engine of an AI Interview system.
Your job is to evaluate the candidate's spoken answer to the interviewer's question.
Remember, this is transcribed speech. Ignore minor grammatical errors or stuttering (filler words). Focus on technical correctness and depth.

CONTEXT:
Question Asked: "{last_q}"
Topic: {last_topic}
Difficulty Level Expected (1-10): {diff}

CANDIDATE'S SPOKEN ANSWER:
"{answer_text}"

Evaluate the answer and return ONLY valid JSON matching this schema:
{{
    "correctness_score": int (1-10, 10 being perfectly accurate),
    "completeness_score": int (1-10, 10 being exhaustive),
    "communication_score": int (1-10, 10 being clear and structured despite being speech),
    "evaluation_rationale": "string (1-2 sentences explaining why you gave these scores)"
}}
"""
        response = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": "Evaluate the answer."
                }
            ],
            model=self.model,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Failed to parse Groq eval response: {e}")
            return {
                "correctness_score": 5,
                "completeness_score": 5,
                "communication_score": 5,
                "evaluation_rationale": "Fallback evaluation due to parsing error."
            }
