from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentForge Studio"
    app_mode: str = "local"
    database_url: str = "sqlite:///./agentforge.db"
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "agentforge-runs"
    queue_execution_mode: str = "redis"  # redis | sync; tests may use sync
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    llm_provider: str = "openai_compatible"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1200
    max_steps_per_run: int = 32
    max_cost_per_run_usd: float = 1.0
    web_search_endpoint: str = ""
    max_upload_mb: int = 10
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = "change-me-for-local-dev"
    metrics_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
