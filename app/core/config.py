from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "AcademyPro API"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/academypro"

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://app.academypro.io"]
    ALLOWED_HOSTS: List[str] = ["api.academypro.io", "localhost"]

    MPESA_CONSUMER_KEY: str = ""
    MPESA_CONSUMER_SECRET: str = ""
    MPESA_SHORTCODE: str = ""
    MPESA_PASSKEY: str = ""
    MPESA_CALLBACK_URL: str = "https://api.academypro.io/v1/payments/mpesa/callback"
    MPESA_ENVIRONMENT: str = "sandbox"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@academypro.io"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "academypro-uploads"
    AWS_S3_REGION: str = "af-south-1"
    CDN_BASE_URL: str = "https://cdn.academypro.io"


settings = Settings()
