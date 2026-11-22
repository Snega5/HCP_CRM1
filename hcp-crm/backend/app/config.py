from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / backend/.env"""

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/hcp_crm"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    SECRET_KEY: str = "dev-only-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Fictional development account, created on first startup if no users exist
    SEED_ADMIN_USERNAME: str = "admin"
    SEED_ADMIN_PASSWORD: str = "admin123"
    SEED_ADMIN_NAME: str = "Dr. Demo Admin"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
