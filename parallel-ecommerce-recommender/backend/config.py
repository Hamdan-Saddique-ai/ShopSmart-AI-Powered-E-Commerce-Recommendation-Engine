import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # ML Parameters
    N_RECOMMENDATIONS = 10
    SIMILARITY_THRESHOLD = 0.3
    
    # Performance
    NUM_PROCESSES = 4
    CACHE_TTL = 300  # 5 minutes