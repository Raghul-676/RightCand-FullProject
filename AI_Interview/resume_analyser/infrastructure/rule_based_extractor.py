import re
from typing import List, Set
from resume_analyser.domain.value_objects import CareerLevel
from resume_analyser.domain.entities import RawResume

class RuleBasedExtractor:
    """
    Deterministic data extraction logic.
    Executes instantly with 100% reliability. No LLM required.
    """
    
    @staticmethod
    def derive_career_level(years_of_experience: float) -> CareerLevel:
        if years_of_experience < 2:
            return CareerLevel.FRESHER
        elif years_of_experience < 5:
            return CareerLevel.JUNIOR
        elif years_of_experience < 8:
            return CareerLevel.MID_LEVEL
        elif years_of_experience < 12:
            return CareerLevel.SENIOR
        else:
            return CareerLevel.PRINCIPAL

    @staticmethod
    def extract_base_tech_stack(resume: RawResume) -> List[str]:
        """
        Hybrid tech extraction. 
        First pass: Uses a dictionary matching algorithm for extreme speed.
        """
        KNOWN_TECH_DICTIONARY = {
            "python", "java", "react", "redux", "sql", "aws", "docker", 
            "kubernetes", "django", "fastapi", "grpc", "terraform"
        }
        
        found_tech: Set[str] = set()
        
        # Look in explicit skills
        for skill in resume.skills:
            if skill.name.lower() in KNOWN_TECH_DICTIONARY:
                found_tech.add(skill.name)
                
        # Look in career descriptions
        for job in resume.career_history:
            if job.description:
                words = re.findall(r'\b\w+\b', job.description.lower())
                for word in words:
                    if word in KNOWN_TECH_DICTIONARY:
                        found_tech.add(word)
                        
        return list(found_tech)
