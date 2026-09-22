from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from resume_analyser.domain.value_objects import CareerLevel, Proficiency, RelationType, NodeType

# --- 1. OUTPUT SCHEMAS (What downstream agents need) ---

class Identity(BaseModel):
    name: str
    current_role: str
    current_industry: str

class Experience(BaseModel):
    years_of_experience: float
    career_level: CareerLevel

class EducationOut(BaseModel):
    degree: str
    institution: str

class SkillOut(BaseModel):
    name: str
    proficiency: str

class CandidateProfile(BaseModel):
    identity: Identity
    experience: Experience
    education: List[EducationOut]
    skills: List[SkillOut]
    languages: List[str]

class InterviewBlueprint(BaseModel):
    initial_difficulty_rating: int = Field(..., ge=1, le=10)
    estimated_interview_length_mins: int
    recommended_starting_category: str
    priority_topics: List[str]
    resume_specific_topics: List[str]

class Node(BaseModel):
    id: str
    type: NodeType

class Edge(BaseModel):
    source: str
    relation: RelationType
    target: str

class KnowledgeGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class AnalyserOutput(BaseModel):
    candidate_profile: CandidateProfile
    interview_blueprint: InterviewBlueprint
    knowledge_graph: KnowledgeGraph


# --- 2. INPUT SCHEMAS (Raw Resume JSON validation) ---

class RawProfile(BaseModel):
    anonymized_name: str
    summary: str
    years_of_experience: float
    current_title: str
    current_company: str
    current_industry: str

class RawCareerHistory(BaseModel):
    company: str
    title: str
    description: Optional[str] = ""

class RawEducation(BaseModel):
    institution: str
    degree: str
    field_of_study: str

class RawSkill(BaseModel):
    name: str
    proficiency: Optional[str] = "unknown"

class RawLanguage(BaseModel):
    language: str

class RawResume(BaseModel):
    """
    Validates incoming JSON. Note how 'redrob_signals' is explicitly NOT included 
    in the typed schema, naturally dropping recruiter metadata.
    """
    candidate_id: str
    profile: RawProfile
    career_history: List[RawCareerHistory]
    education: List[RawEducation]
    skills: List[RawSkill]
    languages: List[RawLanguage]
