import redis
import json
import logging
from typing import Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def set(self, key: str, value: Any, expiration: int = 3600) -> bool:
        """Set a value in cache with expiration (default 1 hour)"""
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            return self.redis_client.setex(key, expiration, serialized_value)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def set_user_session(self, user_id: str, session_data: dict, expiration: int = 86400):
        """Set user session data (24 hours default)"""
        return self.set(f"session:{user_id}", session_data, expiration)
    
    def get_user_session(self, user_id: str) -> Optional[dict]:
        """Get user session data"""
        return self.get(f"session:{user_id}")
    
    def cache_trending_topics(self, topics: list, expiration: int = 7200):
        """Cache trending topics (2 hours default)"""
        return self.set("trending_topics", topics, expiration)
    
    def get_trending_topics(self) -> Optional[list]:
        """Get cached trending topics"""
        return self.get("trending_topics")
    
    def cache_content_ideas(self, user_id: str, ideas: list, expiration: int = 3600):
        """Cache content ideas for user"""
        return self.set(f"content_ideas:{user_id}", ideas, expiration)
    
    def get_content_ideas(self, user_id: str) -> Optional[list]:
        """Get cached content ideas for user"""
        return self.get(f"content_ideas:{user_id}")
