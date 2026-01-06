"""Configuración de la aplicación.

Este módulo contiene la configuración centralizada usando Pydantic Settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación."""

    # App
    app_name: str = "SIMRES-GLP API"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./simres_glp.db"

    # CORS
    cors_origins: list[str] = ["*"]  # Permitir todos los orígenes en desarrollo

    # Simulación
    max_workers: int = 11
    default_replicas: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Obtener configuración (singleton)."""
    return Settings()
