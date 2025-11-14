from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    # Database URL (from Render Environment)
    DATABASE_URL: str

    # JWT Auth (from Render Environment)
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    # OpenAI (from Render Environment)
    OPENAI_API_KEY: str

    # --- FIX: Stripe keys are commented out to disable payments ---
    # Stripe (from Render Environment)
    # STRIPE_SECRET_KEY: str
    # STRIPE_PRICE_ID: str
    # STRIPE_WEBHOOK_SECRET: str
    
    # --- END OF FIX ---

    class Config:
        env_file = ".env" # Load from .env file for local development
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create a single instance to be imported by other files
settings = Settings()