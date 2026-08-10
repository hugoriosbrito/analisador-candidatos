from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Clareza API"
    database_url: str = "sqlite:///./clareza.db"
    redis_url: str = "redis://redis:6379/0"
    admin_key: str = "clareza-dev-admin"
    cors_origins: str = "http://localhost:3000"
    search_provider: str = "demo"
    brave_search_api_key: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "gpt-5-mini"

@lru_cache
def get_settings() -> Settings:
    return Settings()
