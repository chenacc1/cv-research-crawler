"""Application configuration via Pydantic BaseSettings."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this config file (not CWD).
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # GitHub
    github_token: str = ""

    # Arxiv crawler
    crawler_arxiv_enabled: bool = True
    crawler_arxiv_interval_minutes: int = 360
    crawler_arxiv_delay_seconds: float = 3.0

    # GitHub crawler
    crawler_github_enabled: bool = True
    crawler_github_interval_minutes: int = 120
    crawler_github_delay_seconds: float = 2.0

    # Reports
    report_output_dir: str = "./reports"
    report_daily_cron: str = "0 22 * * *"
    report_weekly_cron: str = "0 10 * * 1"

    # Logging
    log_level: str = "INFO"

    # LLM summary
    llm_api_base: str = "http://localhost:11434"
    llm_api_key: str = ""
    llm_model: str = "gemma4:e4b"
    llm_summary_enabled: bool = True
    llm_summary_max_tokens: int = 150

    # Crawler filter keywords (comma-separated, case-insensitive)
    crawler_keywords: str = "computer vision,deep learning,image,video,detection,segmentation,generation,3d,nerf,diffusion,transformer,multimodal"

    # CORS
    api_cors_origins: str = "http://localhost:5173"

    # App
    app_version: str = "1.0.0"


settings = Settings()
