from pydantic_settings import BaseSettings
from typing import List, Optional, Any
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: str

    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 

    # FIX: This requires the GOOGLE_API_KEY from the environment/dotenv.
    # The old OPENAI_API_KEY field is REMOVED to prevent conflict.
    GOOGLE_API_KEY: str

    # --- STRIPE KEYS (DISABLED) ---
    # Since these fields are commented out, Pydantic ignores them.
    # This prevents the 'Extra inputs are not permitted' error for Stripe/Old Google keys.
    # STRIPE_SECRET_KEY: str
    # STRIPE_PRICE_ID: str
    # STRIPE_WEBHOOK_SECRET: str
    # --- END STRIPE FIX ---

    ALLOWED_ORIGINS: str = "" 
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()