from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/hcp_crm"
    CORS_ORIGINS: str = "http://localhost:3000"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()