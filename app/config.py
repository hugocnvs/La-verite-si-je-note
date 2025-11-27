"""Configuration de l'application et des paramètres globaux."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Paramètres chargés depuis l'environnement ou des valeurs par défaut."""

    app_name: str = "La Vérité Si Je Note"
    secret_key: str = "change-me"
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"
    session_cookie: str = "lvn_session"
    api_timeout_seconds: int = 10
    default_page_size: int = 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance de paramètres mise en cache."""
    return Settings()

