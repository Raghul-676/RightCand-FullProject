import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from resume_analyser.domain.entities import AnalyserOutput
from interview_brain.infrastructure.llm_agents import MockQuestionGenerator, MockTechnicalEvaluator
from interview_brain.application.orchestrator import InterviewOrchestrator
from core.logger import get_logger

logger = get_logger("InterviewBrainCLI")

async def main():
    logger.info("Starting Phase 3: Interview Brain CLI")
    
    # 1. Dependency Injection
    q_gen = MockQuestionGenerator()
    tech_eval = MockTechnicalEvaluator()
    orchestrator = InterviewOrchestrator(q_gen, tech_eval)
    
    # 2. Load Phase 2 Output
    try:
        # In a real scenario, this comes directly from Phase 2 in memory.
        # Here we mock it by loading a known structure.
        # We will just generate a dummy one using Pydantic directly for the test.
        with open("sample_resume.json", "r") as f:
            raw_data = json.load(f)
            # Run it through use_case to get the strict object? 
            # Better to just import it!
        from resume_analyser.infrastructure.llm_extractor import MockLLMExtractor
        from resume_analyser.application.use_cases.analyze_resume_use_case import AnalyzeResumeUseCase
        
        analyser = AnalyzeResumeUseCase(MockLLMExtractor())
        intelligence_payload = analyser.execute(raw_data)
        
    except FileNotFoundError:
        logger.error("sample_resume.json not found! Please run python create_sample.py first.")
        return
        
    # 3. Initialize Interview Session
    state = orchestrator.initialize_session("SESSION_001", intelligence_payload)
    
    # 4. Run the main orchestration loop
    final_state = await orchestrator.run_interview_loop_demo(state)
    
    print("\n" + "="*80)
    print("FINAL INTERVIEW STATE DUMP:")
    print("="*80)
    print(final_state.model_dump_json(indent=2, exclude={"intelligence_payload"}))
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
