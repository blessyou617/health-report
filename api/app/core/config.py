import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Health Report API"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/health_report"
    
    # WeChat
    WECHAT_APP_ID: str = "your_app_id"
    WECHAT_APP_SECRET: str = "your_app_secret"
    
    # WeChat Pay (微信支付)
    WECHAT_MCH_ID: str = "your_merchant_id"       # 商户号
    WECHAT_API_KEY: str = "your_api_key"         # API密钥 (商户设置)
    WECHAT_NOTIFY_URL: str = "https://your-domain.com/api/v1/payment/callback"  # 支付回调地址
    
    # OpenAI
    OPENAI_API_KEY: str = "your_openai_key"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
