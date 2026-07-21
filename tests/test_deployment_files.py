from pathlib import Path

import yaml


# 读取仓库根目录下的文本文件，供部署配置测试复用。
def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


# 验证 Dockerfile 固定 Python 版本、安装依赖，并使用生产方式启动 FastAPI。
def test_dockerfile_defines_api_runtime():
    dockerfile = _read_text("Dockerfile")

    assert "python:3.11-slim" in dockerfile
    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app"' in dockerfile
    assert "--host" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "--port" in dockerfile
    assert "8000" in dockerfile


# 验证 docker compose 会挂载手册目录和向量库目录，并暴露 API 端口。
def test_docker_compose_mounts_runtime_data_and_healthcheck():
    compose = yaml.safe_load(_read_text("docker-compose.yml"))
    service = compose["services"]["kf-rag-api"]

    assert service["build"]["context"] == "."
    assert "8000:8000" in service["ports"]
    assert "./data/help:/app/data/help:ro" in service["volumes"]
    assert "./storage/chroma:/app/storage/chroma" in service["volumes"]
    assert service["env_file"] == [".env"]
    assert "/api/health" in " ".join(service["healthcheck"]["test"])


# 验证 Docker 构建上下文不会打包真实密钥、手册数据和本地向量库。
def test_dockerignore_excludes_local_state_and_secrets():
    dockerignore = _read_text(".dockerignore")

    assert ".env" in dockerignore
    assert "data/" in dockerignore
    assert "storage/" in dockerignore
    assert "__pycache__/" in dockerignore
