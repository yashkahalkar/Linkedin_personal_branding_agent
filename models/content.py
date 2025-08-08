from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

class PostType(str, Enum):
    TEXT = "text"
    ARTICLE = "article"
    CAROUSEL = "carousel"
    POLL = "poll"
    VIDEO = "video"

class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class LinkedInPost(BaseModel):
    post_id: str = Field(..., description="Unique post identifier")
    user_id: str
    content: str
    post_type: PostType = PostType.TEXT
    hashtags: List[str] = []
    mentions: List[str] = []
    media_urls: List[str] = []
    scheduled_time: Optional[datetime] = None
    published_time: Optional[datetime] = None
    status: PostStatus = PostStatus.DRAFT
    linkedin_post_id: Optional[str] = None
    
    # Analytics
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    engagement_rate: float = 0.0
    
    # Generation metadata
    generated_from_topic: Optional[str] = None
    ai_confidence_score: float = 0.0
    content_pillar: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContentCalendar(BaseModel):
    user_id: str
    month: int
    year: int
    scheduled_posts: List[str] = []  # List of post_ids
    content_themes: Dict[str, List[str]] = {}  # Week -> themes
    updated_at: datetime = Field(default_factory=datetime.utcnow)
