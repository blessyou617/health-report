from functools import lru_cache
import json
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "Health Report API"
    DEBUG: bool = True

    # CORS
    CORS_ALLOW_ORIGINS: str = "*"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/health_report"

    # WeChat
    WECHAT_APP_ID: str = "your_app_id"
    WECHAT_APP_SECRET: str = "your_app_secret"

    # WeChat Pay (微信支付)
    WECHAT_MCH_ID: str = "your_merchant_id"
    WECHAT_API_KEY: str = "your_api_key"
    WECHAT_NOTIFY_URL: str = "https://your-domain.com/api/v1/payment/callback"
    WECHAT_MCH_CERT_SERIAL_NO: Optional[str] = None
    WECHAT_MCH_PRIVATE_KEY: Optional[str] = None

    # OpenAI
    OPENAI_API_KEY: str = "your_openai_key"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET: Optional[str] = Field(default=None)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    @property
    def jwt_secret(self) -> str:
        """Compatibility accessor for JWT secret naming."""
        return self.JWT_SECRET or self.SECRET_KEY

    @property
    def cors_allow_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string or JSON array."""
        raw = (self.CORS_ALLOW_ORIGINS or "*").strip()
        if raw == "*":
            return ["*"]

        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass

        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
