from typing import List, Optional, Any
from pydantic_settings import BaseSettings
from pydantic import model_validator
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

    # This is not used because main.py is set to ["*"]
    # but we leave it here for future use.
    ALLOWED_ORIGINS: str = "" 

    # --- THIS WAS THE FIX ---
    # I have removed the 'GOOGLE_API_KEY: str' line.
    # Your project uses Ollama, so this key is not needed 
    # and was causing a startup crash.
    # ------------------------

    class Config:
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()