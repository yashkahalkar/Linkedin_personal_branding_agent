from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    email: str
    full_name: str
    linkedin_profile_url: Optional[str] = None
    industry: str
    job_title: str
    company: str
    skills: List[str] = []
    interests: List[str] = []
    bio: str = ""
    brand_voice: str = "professional"  # professional, casual, authoritative, friendly
    target_audience: str = ""
    posting_frequency: int = 3  # posts per week
    preferred_posting_times: List[str] = ["09:00", "13:00", "17:00"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    linkedin_access_token: Optional[str] = None
    linkedin_refresh_token: Optional[str] = None

class ContentStrategy(BaseModel):
    user_id: str
    content_pillars: List[str] = []  # Main themes for content
    hashtag_strategy: List[str] = []
    competitor_profiles: List[str] = []
    trending_topics: List[str] = []
    content_mix: dict = {  # Percentage distribution
        "thought_leadership": 30,
        "industry_insights": 25,
        "personal_experience": 25,
        "company_updates": 20
    }
    updated_at: datetime = Field(default_factory=datetime.utcnow)
