"""
Authentication configuration
"""

import os
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production-min-32-chars")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore"


auth_settings = AuthSettings()
