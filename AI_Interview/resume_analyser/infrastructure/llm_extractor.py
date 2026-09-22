from typing import List
from resume_analyser.application.interfaces import ILLMExtractor
from core.logger import get_logger

logger = get_logger("MockLLMExtractor")

class MockLLMExtractor(ILLMExtractor):
    """
    A concrete implementation of the ILLMExtractor that returns mocked data.
    In a real production environment, this would be replaced with OpenAIExtractor
    or GeminiExtractor utilizing official SDKs.
    """
    
    def extract_projects(self, career_descriptions: str) -> List[str]:
        logger.info("LLM: Extracting projects from descriptions...")
        # A real LLM would use semantic parsing here. We mock it for the demo.
        if "API" in career_descriptions or "close cycle" in career_descriptions:
            return ["Financial Close Cycle Automation", "Digital Transformation Strategy"]
        return ["Unknown Internal Project"]
        
    def classify_domain(self, summary: str, company_names: List[str]) -> List[str]:
        logger.info("LLM: Classifying business domains...")
        domains = []
        summary_lower = summary.lower()
        if "marketing" in summary_lower or "retail" in summary_lower:
            domains.append("Retail / E-Commerce")
        if "finance" in summary_lower or "accounting" in summary_lower:
            domains.append("Finance / FinTech")
        
        if not domains:
            domains.append("General Software Engineering")
        return domains
        
    def generate_interview_topics(self, skills: List[str], domains: List[str]) -> List[str]:
        logger.info("LLM: Generating adaptive interview topics...")
        topics = []
        if "SQL" in skills:
            topics.extend(["Database Normalization", "Query Optimization", "Joins"])
        if "Redux" in skills:
            topics.extend(["State Management", "Immutability"])
        if "Finance / FinTech" in domains:
            topics.append("Transactional Consistency (ACID)")
            
        return topics[:5] # Limit to 5 priority topics
