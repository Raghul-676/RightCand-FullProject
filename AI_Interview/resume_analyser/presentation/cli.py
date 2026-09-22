import json
import sys
import os

# Add project root to python path to allow direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from resume_analyser.infrastructure.llm_extractor import MockLLMExtractor
from resume_analyser.application.use_cases.analyze_resume_use_case import AnalyzeResumeUseCase
from core.logger import get_logger

logger = get_logger("ResumeAnalyserCLI")

def run():
    logger.info("Starting Resume Analyser CLI...")
    
    # 1. Dependency Injection setup
    llm_extractor = MockLLMExtractor()
    use_case = AnalyzeResumeUseCase(llm_extractor=llm_extractor)
    
    # 2. Load input JSON
    try:
        with open("sample_resume.json", "r") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        logger.error("sample_resume.json not found! Please run python create_sample.py first.")
        return
        
    # 3. Execute Pipeline
    output = use_case.execute(raw_data)
    
    # 4. Show Output
    print("\n" + "="*80)
    print("FINAL INTELLIGENCE GRAPH (Ready for Interview Agent):")
    print("="*80)
    print(output.model_dump_json(indent=2))
    print("="*80 + "\n")

if __name__ == "__main__":
    run()
