from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    football_data_api_key: str = ""
    database_url: str = "sqlite:///./data/worldcup.db"
    cache_ttl_seconds: int = 3600
    refresh_interval_minutes: int = 60
    football_data_competition_id: int = 2000
    football_data_form_lookback_days: int = 60
    cors_origins: str = "http://localhost:5173"
    disable_scheduler: bool = False

    football_data_base_url: str = "https://api.football-data.org/v4"
    polymarket_gamma_base_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_base_url: str = "https://clob.polymarket.com"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
