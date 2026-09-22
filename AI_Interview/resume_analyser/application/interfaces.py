from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ILLMExtractor(ABC):
    """
    Interface for the LLM extraction service. 
    By depending on this interface, the business logic is decoupled from OpenAI/Gemini.
    """
    
    @abstractmethod
    def extract_projects(self, career_descriptions: str) -> List[str]:
        """Extract hidden projects from career history text."""
        pass
        
    @abstractmethod
    def classify_domain(self, summary: str, company_names: List[str]) -> List[str]:
        """Infer business domains (e.g., FinTech, Healthcare)."""
        pass
        
    @abstractmethod
    def generate_interview_topics(self, skills: List[str], domains: List[str]) -> List[str]:
        """Generate specific interview topics based on skills."""
        pass
