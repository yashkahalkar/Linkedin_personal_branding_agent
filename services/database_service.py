from pymongo import MongoClient
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from config.settings import settings
from models.user import UserProfile, ContentStrategy
from models.content import LinkedInPost, ContentCalendar

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URL)
        self.db = self.client[settings.DATABASE_NAME]
        self.users = self.db.users
        self.content_strategies = self.db.content_strategies
        self.posts = self.db.posts
        self.calendars = self.db.calendars
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        self.users.create_index("user_id", unique=True)
        self.users.create_index("email", unique=True)
        self.posts.create_index("user_id")
        self.posts.create_index("scheduled_time")
        self.posts.create_index("published_time")
        self.content_strategies.create_index("user_id", unique=True)
        self.calendars.create_index([("user_id", 1), ("month", 1), ("year", 1)], unique=True)
    
    # User operations
    def create_user(self, user_profile: UserProfile) -> bool:
        try:
            result = self.users.insert_one(user_profile.dict())
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        try:
            user_data = self.users.find_one({"user_id": user_id})
            if user_data:
                return UserProfile(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    # Content strategy operations
    def save_content_strategy(self, strategy: ContentStrategy) -> bool:
        try:
            result = self.content_strategies.replace_one(
                {"user_id": strategy.user_id},
                strategy.dict(),
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving content strategy: {e}")
            return False
    
    def get_content_strategy(self, user_id: str) -> Optional[ContentStrategy]:
        try:
            strategy_data = self.content_strategies.find_one({"user_id": user_id})
            if strategy_data:
                # Ensure hashtag_strategy is a list
                if 'hashtag_strategy' in strategy_data:
                    if isinstance(strategy_data['hashtag_strategy'], dict):
                    # Convert dict to flat list
                        hashtags = []
                        for category, tags in strategy_data['hashtag_strategy'].items():
                            if isinstance(tags, list):
                                hashtags.extend([tag.replace('#', '') for tag in tags])
                        strategy_data['hashtag_strategy'] = hashtags
            
                return ContentStrategy(**strategy_data)
            return None
        except Exception as e:
            logger.error(f"Error getting content strategy: {e}")
            return None

    
    # Post operations
    def save_post(self, post: LinkedInPost) -> bool:
        try:
            result = self.posts.replace_one(
                {"post_id": post.post_id},
                post.dict(),
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return False
    
    def get_post(self, post_id: str) -> Optional[LinkedInPost]:
        try:
            post_data = self.posts.find_one({"post_id": post_id})
            if post_data:
                return LinkedInPost(**post_data)
            return None
        except Exception as e:
            logger.error(f"Error getting post: {e}")
            return None
    
    def get_user_posts(self, user_id: str, limit: int = 50) -> List[LinkedInPost]:
        try:
            posts_data = self.posts.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit)
            
            return [LinkedInPost(**post) for post in posts_data]
        except Exception as e:
            logger.error(f"Error getting user posts: {e}")
            return []
    
    def get_scheduled_posts(self, user_id: str) -> List[LinkedInPost]:
        try:
            posts_data = self.posts.find({
                "user_id": user_id,
                "status": "scheduled"
            }).sort("scheduled_time", 1)
            
            return [LinkedInPost(**post) for post in posts_data]
        except Exception as e:
            logger.error(f"Error getting scheduled posts: {e}")
            return []
    
    # Calendar operations
    def save_calendar(self, calendar: ContentCalendar) -> bool:
        try:
            result = self.calendars.replace_one(
                {
                    "user_id": calendar.user_id,
                    "month": calendar.month,
                    "year": calendar.year
                },
                calendar.dict(),
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving calendar: {e}")
            return False
    
    def get_calendar(self, user_id: str, month: int, year: int) -> Optional[ContentCalendar]:
        try:
            calendar_data = self.calendars.find_one({
                "user_id": user_id,
                "month": month,
                "year": year
            })
            if calendar_data:
                return ContentCalendar(**calendar_data)
            return None
        except Exception as e:
            logger.error(f"Error getting calendar: {e}")
            return None
