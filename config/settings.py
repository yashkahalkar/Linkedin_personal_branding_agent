import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "linkedin_ai_agent")
    
    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
    
    # App Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Content Settings
    MAX_POST_LENGTH = 3000
    DEFAULT_POSTING_TIMES = ["09:00", "13:00", "17:00"]

settings = Settings()
