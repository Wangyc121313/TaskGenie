import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


class Settings:
    APP_NAME: str = "TaskGenie"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "AI-assisted task management system"

    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    OPENAI_VISION_MODEL: str = os.getenv("OPENAI_VISION_MODEL", OPENAI_MODEL)

    MAX_TASKS_PER_PLANNING: int = int(os.getenv("MAX_TASKS_PER_PLANNING", "10"))
    DEFAULT_TASK_PRIORITY: str = os.getenv("DEFAULT_TASK_PRIORITY", "medium")
    DEFAULT_ESTIMATED_HOURS: float = float(os.getenv("DEFAULT_ESTIMATED_HOURS", "2.0"))

    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://10.0.2.2:8081",
        "*",
    ]

    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    AUTO_TAG_ENABLED: bool = os.getenv("AUTO_TAG_ENABLED", "True").lower() == "true"

    AI_TASK_PLANNING_ENABLED: bool = os.getenv("AI_TASK_PLANNING_ENABLED", "True").lower() == "true"
    AI_SCHEDULE_ENABLED: bool = os.getenv("AI_SCHEDULE_ENABLED", "True").lower() == "true"
    AI_RESPONSE_TIMEOUT: int = int(os.getenv("AI_RESPONSE_TIMEOUT", "30"))
    MAX_IMAGE_UPLOAD_MB: int = int(os.getenv("MAX_IMAGE_UPLOAD_MB", "8"))

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


settings = Settings()


class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    CORS_ORIGINS: list = ["https://your-frontend-domain.com"]


def get_settings() -> Settings:
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        return ProductionSettings()
    return DevelopmentSettings()


current_settings = get_settings()
