from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent if BACKEND_ROOT.name == "backend" else BACKEND_ROOT


# 将相对运行路径解析到仓库根目录，避免从 backend/ 启动时写入 backend/storage。
def resolve_runtime_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return REPO_ROOT / path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_api_key: str = ""
    disable_auth: bool = True
    cors_allowed_origins: str = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:5174,http://localhost:5174,"
        "http://127.0.0.1:3000,http://localhost:3000,"
        "http://127.0.0.1:8080,http://localhost:8080"
    )

    deepseek_api_key: str = Field(default="", repr=False)
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: int = 60
    deepseek_judge_model: str = "deepseek-v4-pro"
    deepseek_judge_timeout_seconds: int = 60
    evaluation_semantic_enabled: bool = True
    evaluation_metrics: str = "faithfulness"

    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    chroma_persist_dir: Path = Path("storage/chroma")
    index_manifest_path: Path = Path("storage/processed/index_manifest.json")
    data_dir: Path = Path("data/help")
    chunk_size: int = 700
    chunk_overlap: int = 100
    top_k: int = 5
    retrieval_max_chunks_per_source: int = 2
    max_images_per_source: int = 5
    max_images_per_answer: int = 8
    enable_query_rewrite: bool = False
    query_rewrite_max_queries: int = 3
    multi_query_candidate_limit: int = 50
    enable_conversation_rewrite: bool = True
    enable_conversation_summary: bool = True
    conversation_summary_every_n_turns: int = 3

    # 统一规范化运行数据路径，让本地、测试和容器入口共享同一套解析规则。
    @field_validator("chroma_persist_dir", "index_manifest_path", "data_dir", mode="after")
    @classmethod
    def normalize_runtime_paths(cls, value: Path) -> Path:
        return resolve_runtime_path(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()
