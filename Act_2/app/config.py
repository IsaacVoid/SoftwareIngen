from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str


    ACCESS_TOKEN_EXPIRES_MIN: int = Field(default=15, ge=5, le=1440)
    REFRESH_TOKEN_EXPIRES_DAYS: int = Field(default=7, ge=1, le=60)


    DATABASE_URL: str = "sqlite:///./app.db"


    CORS_ORIGINS: str = "*"
    COOKIE_DOMAIN: str = "localhost"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax" # 'lax' | 'strict' | 'none'


    class Config:
        env_file = ".env"


settings = Settings()
