from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    profile_setup_done: bool = False

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    profile_setup_done: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Coding Profile ────────────────────────────────────────────────────────────

class ProfileSetup(BaseModel):
    leetcode_username: str
    codeforces_handle: Optional[str] = None
    github_username: Optional[str] = None

class ProfileUpdate(BaseModel):
    leetcode_username: Optional[str] = None
    codeforces_handle: Optional[str] = None
    github_username: Optional[str] = None

class CodingProfileOut(BaseModel):
    id: int
    user_id: int
    leetcode_username: Optional[str]
    codeforces_handle: Optional[str]
    github_username: Optional[str]
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}

# ── Project Repos ─────────────────────────────────────────────────────────────

class ProjectRepoIn(BaseModel):
    repo_urls: list[str]

class ProjectRepoOut(BaseModel):
    id: int
    repo_url: str
    project_name: Optional[str]
    complexity: Optional[str]
    stack_breakdown: Optional[str]  # JSON string
    summary: Optional[str]
    analysed_at: datetime
    model_config = {"from_attributes": True}

class StudentListItem(BaseModel):
    id: int
    username: str
    email: str
    profile_setup_done: bool
    leetcode_username: Optional[str] = None
    codeforces_handle: Optional[str] = None
    github_username: Optional[str] = None
    model_config = {"from_attributes": True}
