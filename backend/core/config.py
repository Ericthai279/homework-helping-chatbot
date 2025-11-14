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

    # FIX: Include the required AI key
    OPENAI_API_KEY: str

    # --- FIX: Stripe keys are commented out to disable payments ---
    # STRIPE_SECRET_KEY: str
    # STRIPE_PRICE_ID: str
    # STRIPE_WEBHOOK_SECRET: str
    # --- END OF FIX ---

    ALLOWED_ORIGINS: str = "" 
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()