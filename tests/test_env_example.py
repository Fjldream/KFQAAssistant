from pathlib import Path

from app.core.config import Settings


# 把 settings 字段名转换成 .env 中使用的大写环境变量名。
def _setting_env_name(field_name: str) -> str:
    return field_name.upper()


# 读取 .env.example 中声明过的环境变量名，忽略空行和注释。
def _load_example_env_names() -> set[str]:
    lines = Path(".env.example").read_text(encoding="utf-8").splitlines()
    return {line.split("=", 1)[0].strip() for line in lines if line.strip() and not line.startswith("#")}


# 验证 .env.example 覆盖代码实际读取的配置，避免部署时遗漏关键变量。
def test_env_example_documents_required_configuration():
    env_names = _load_example_env_names()
    settings_env_names = {_setting_env_name(name) for name in Settings.model_fields}

    assert settings_env_names.issubset(env_names)
    assert "KF_RAG_API_URL" in env_names
