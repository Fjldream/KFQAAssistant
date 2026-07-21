from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_api_key: str = ""
    disable_auth: bool = True

    deepseek_api_key: str = Field(default="", repr=False)
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: int = 60

    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    chroma_persist_dir: Path = Path("storage/chroma")
    index_manifest_path: Path = Path("storage/processed/index_manifest.json")
    data_dir: Path = Path("data/help")
    top_k: int = 5
    max_images_per_source: int = 5
    max_images_per_answer: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
