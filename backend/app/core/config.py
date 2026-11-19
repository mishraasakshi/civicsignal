from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CivicSignal"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    ENABLE_DOCS: bool | None = None  # /docs on or off; default: only in development

    # Security
    JWT_SECRET_KEY: str = Field(default="change-me-to-a-secure-random-secret-key-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REMEMBER_ME_DAYS: int = 30  # how long "Remember me" keeps you logged in
    SESSION_COOKIE_NAME: str = "cs_session"

    # Database URLs
    DATABASE_URL: str = Field(
        default="postgresql://civicuser:civicpassword@localhost:5432/civicsignal"
    )
    DATABASE_READONLY_URL: str = Field(
        default="postgresql://civic_readonly:readonlypassword@localhost:5432/civicsignal"
    )

    # LLM (Groq)
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL_NAME: str = Field(default="llama-3.3-70b-versatile")

    # Machine Learning & Search
    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    FAISS_INDEX_PATH: str = "ml/artifacts/complaint_faiss.index"
    CLASSIFIER_MODEL_PATH: str = "ml/artifacts/classifier_model.pkl"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Domain Constants
    CATEGORIES: list[str] = [
        "water_plumbing",
        "electrical",
        "cleanliness",
        "internet_wifi",
        "furniture",
        "mess_food",
        "security",
        "other",
    ]

    STATUSES: list[str] = [
        "Submitted",
        "Under Review",
        "Assigned",
        "In Progress",
        "Resolved",
        "Closed",
        "Needs More Information",
    ]

    ROLES: list[str] = [
        "reporter",
        "supervisor",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
