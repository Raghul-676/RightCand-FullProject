import json
from typing import List, Dict, Any

from resume_analyser.domain.entities import (
    RawResume, AnalyserOutput, CandidateProfile, Identity, Experience, 
    EducationOut, SkillOut, InterviewBlueprint, KnowledgeGraph, Node, Edge
)
from resume_analyser.domain.value_objects import CareerLevel, Proficiency, NodeType, RelationType
from resume_analyser.application.interfaces import ILLMExtractor
from resume_analyser.infrastructure.rule_based_extractor import RuleBasedExtractor
from core.logger import get_logger

logger = get_logger("AnalyzeResumeUseCase")

class AnalyzeResumeUseCase:
    def __init__(self, llm_extractor: ILLMExtractor):
        self.llm_extractor = llm_extractor

    def execute(self, raw_resume_json: Dict[str, Any]) -> AnalyserOutput:
        logger.info("Step 1: Schema Validation (Pydantic)")
        raw_resume = RawResume(**raw_resume_json)
        
        logger.info("Step 2 & 3: Rule-Based Extraction & Analysis")
        # Direct field mappings
        identity = Identity(
            name=raw_resume.profile.anonymized_name,
            current_role=raw_resume.profile.current_title,
            current_industry=raw_resume.profile.current_industry
        )
        
        career_level = RuleBasedExtractor.derive_career_level(raw_resume.profile.years_of_experience)
        experience = Experience(
            years_of_experience=raw_resume.profile.years_of_experience,
            career_level=career_level
        )
        
        education_list = [
            EducationOut(degree=edu.degree, institution=edu.institution) 
            for edu in raw_resume.education
        ]
        
        skills_list = [
            SkillOut(name=sk.name, proficiency=sk.proficiency) 
            for sk in raw_resume.skills
        ]
        
        languages = [lang.language for lang in raw_resume.languages]
        
        candidate_profile = CandidateProfile(
            identity=identity,
            experience=experience,
            education=education_list,
            skills=skills_list,
            languages=languages
        )
        
        logger.info("Step 4 & 5: Tech Stack & Hidden Project Extraction (Hybrid)")
        base_tech = RuleBasedExtractor.extract_base_tech_stack(raw_resume)
        
        # Combine all career descriptions for context
        all_descriptions = " ".join([job.description for job in raw_resume.career_history if job.description])
        
        # LLM calls (Note: In a real system with AsyncIO, these could run concurrently)
        extracted_projects = self.llm_extractor.extract_projects(all_descriptions)
        classified_domains = self.llm_extractor.classify_domain(raw_resume.profile.summary, [job.company for job in raw_resume.career_history])
        
        logger.info("Step 6: Interview Topic Generation (LLM)")
        skill_names = [sk.name for sk in raw_resume.skills]
        topics = self.llm_extractor.generate_interview_topics(skill_names, classified_domains)
        
        logger.info("Step 7: Generating Blueprint")
        # Derive initial difficulty from 1 to 10 based on career level
        difficulty_map = {
            CareerLevel.FRESHER: 2,
            CareerLevel.JUNIOR: 4,
            CareerLevel.MID_LEVEL: 6,
            CareerLevel.SENIOR: 8,
            CareerLevel.PRINCIPAL: 10
        }
        blueprint = InterviewBlueprint(
            initial_difficulty_rating=difficulty_map.get(career_level, 5),
            estimated_interview_length_mins=45,
            recommended_starting_category="System Design" if career_level in (CareerLevel.SENIOR, CareerLevel.PRINCIPAL) else "Core Fundamentals",
            priority_topics=topics,
            resume_specific_topics=extracted_projects
        )
        
        logger.info("Step 8: Assembling Knowledge Graph")
        nodes = []
        edges = []
        
        # Add Candidate Node
        cand_id = identity.name
        nodes.append(Node(id=cand_id, type=NodeType.CANDIDATE))
        
        # Add Tech Nodes
        for tech in base_tech:
            # Capitalize standard names
            clean_tech = tech.capitalize() if tech.islower() else tech
            nodes.append(Node(id=clean_tech, type=NodeType.TECHNOLOGY))
            edges.append(Edge(source=cand_id, relation=RelationType.KNOWS, target=clean_tech))
            
        # Add Domain Nodes
        for domain in classified_domains:
            nodes.append(Node(id=domain, type=NodeType.DOMAIN))
            edges.append(Edge(source=cand_id, relation=RelationType.WORKED_IN, target=domain))
            
        knowledge_graph = KnowledgeGraph(nodes=nodes, edges=edges)
        
        logger.info("Step 9: Pipeline Complete. Outputting AnalyserOutput JSON.")
        return AnalyserOutput(
            candidate_profile=candidate_profile,
            interview_blueprint=blueprint,
            knowledge_graph=knowledge_graph
        )
