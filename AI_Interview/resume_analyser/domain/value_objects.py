from enum import Enum

class CareerLevel(str, Enum):
    FRESHER = "Fresher"
    JUNIOR = "Junior"
    MID_LEVEL = "Mid-Level"
    SENIOR = "Senior"
    PRINCIPAL = "Principal"

class Proficiency(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    UNKNOWN = "unknown"

class RelationType(str, Enum):
    KNOWS = "KNOWS"
    WORKED_IN = "WORKED_IN"
    USES_TECH = "USES_TECH"
    STUDIED_AT = "STUDIED_AT"
    WORKED_AT = "WORKED_AT"

class NodeType(str, Enum):
    CANDIDATE = "Candidate"
    TECHNOLOGY = "Technology"
    DOMAIN = "Domain"
    PROJECT = "Project"
    INDUSTRY = "Industry"
    COMPANY = "Company"
    UNIVERSITY = "University"
