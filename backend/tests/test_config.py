from pathlib import Path

from app.core.config import Settings


def test_settings_defaults_are_local_friendly():
    repo_root = Path(__file__).resolve().parents[2]
    settings = Settings(deepseek_api_key="", _env_file=None)

    assert settings.app_env == "local"
    assert settings.disable_auth is True
    assert settings.deepseek_model == "deepseek-v4-flash"
    assert settings.deepseek_judge_model == "deepseek-v4-flash"
    assert settings.embedding_model_name == "BAAI/bge-small-zh-v1.5"
    assert settings.data_dir == repo_root / "data/help"
    assert settings.chroma_persist_dir == repo_root / "storage/chroma"
    assert settings.index_manifest_path == repo_root / "storage/processed/index_manifest.json"
    assert settings.chunk_size == 700
    assert settings.chunk_overlap == 100
    assert settings.top_k == 5
    assert settings.max_images_per_source == 5
    assert settings.max_images_per_answer == 8
    assert settings.enable_query_rewrite is False
    assert settings.query_rewrite_max_queries == 3
    assert settings.multi_query_candidate_limit == 50
    assert settings.enable_conversation_rewrite is True
    assert settings.enable_conversation_summary is True
    assert settings.conversation_summary_every_n_turns == 3


def test_settings_resolves_relative_runtime_paths_from_repo_root():
    repo_root = Path(__file__).resolve().parents[2]
    settings = Settings(
        deepseek_api_key="",
        data_dir=Path("custom/help"),
        chroma_persist_dir=Path("custom/chroma"),
        index_manifest_path=Path("custom/processed/index_manifest.json"),
        _env_file=None,
    )

    assert settings.data_dir == repo_root / "custom/help"
    assert settings.chroma_persist_dir == repo_root / "custom/chroma"
    assert settings.index_manifest_path == repo_root / "custom/processed/index_manifest.json"
