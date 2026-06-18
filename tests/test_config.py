from app.core.config import Settings


def test_settings_defaults_are_local_friendly():
    settings = Settings(deepseek_api_key="")

    assert settings.app_env == "local"
    assert settings.disable_auth is True
    assert settings.deepseek_model == "deepseek-v4-flash"
    assert settings.embedding_model_name == "BAAI/bge-small-zh-v1.5"
    assert settings.top_k == 5
    assert settings.max_images_per_source == 5
    assert settings.max_images_per_answer == 8
