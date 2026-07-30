import logging
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.schemas.chat import ChatResponse, SourceSnippet
from app.main import create_app
from app.rag.errors import IndexNotReadyError
from app.core.config import get_settings


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_allows_local_frontend_origin(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:5173")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_manual_images_are_served(tmp_path, monkeypatch):
    manual_dir = tmp_path / "help"
    manual_dir.mkdir()
    image = manual_dir / "example.png"
    image.write_bytes(b"image")
    monkeypatch.setenv("DATA_DIR", str(manual_dir))
    get_settings.cache_clear()

    response = TestClient(create_app()).get("/manuals/example.png")

    assert response.status_code == 200


def test_app_starts_when_manual_data_dir_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "missing-help"))
    get_settings.cache_clear()

    response = TestClient(create_app()).get("/api/health")

    assert response.status_code == 200


# 验证就绪检查在核心配置和索引都可用时返回 ready，给部署平台判断服务可接流量。
def test_readiness_endpoint_reports_ready(monkeypatch):
    class FakeVectorStore:
        # 模拟已经构建完成的向量库。
        def count(self):
            return 12

    import app.api.routes_health as routes_health

    monkeypatch.setattr(
        routes_health,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="production",
            disable_auth=False,
            app_api_key="internal-key",
            deepseek_api_key="deepseek-key",
        ),
    )
    monkeypatch.setattr(routes_health, "create_vector_store", lambda: FakeVectorStore())
    client = TestClient(create_app())

    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["chunks"] == 12
    assert response.json()["issues"] == []
    assert response.json()["checks"]["index"] == "ok"


# 验证就绪检查会暴露关键配置问题，避免部署后用户请求才发现服务不可用。
def test_readiness_endpoint_reports_not_ready(monkeypatch):
    class FakeVectorStore:
        # 模拟尚未构建索引的空向量库。
        def count(self):
            return 0

    import app.api.routes_health as routes_health

    monkeypatch.setattr(
        routes_health,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="production",
            disable_auth=True,
            app_api_key="",
            deepseek_api_key="",
        ),
    )
    monkeypatch.setattr(routes_health, "create_vector_store", lambda: FakeVectorStore())
    client = TestClient(create_app())

    response = client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["deepseek_api_key"] == "error"
    assert response.json()["checks"]["auth"] == "error"
    assert response.json()["checks"]["index"] == "error"
    assert response.json()["issues"] == [
        "未配置 DEEPSEEK_API_KEY，问答接口无法调用大模型。",
        "生产环境不能关闭 API Key 认证，请设置 DISABLE_AUTH=false 并配置 APP_API_KEY。",
        "知识库索引为空，请先执行索引构建。",
    ]


# 验证索引状态接口会返回文档、chunk、配置指纹和最后更新时间。
def test_index_status_endpoint_reports_vector_store_count(monkeypatch):
    class FakeVectorStore:
        # 模拟已构建索引的向量库数量。
        def count(self):
            return 12

    import app.api.routes_index as routes_index
    from app.rag.ingestion.index_manifest import IndexManifest, ManifestEntry

    manifest_path = Path("storage/processed/test_manifest.json")
    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            chroma_persist_dir="storage/chroma",
            index_manifest_path=manifest_path,
            embedding_model_name="test-embedding-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())
    monkeypatch.setattr(
        routes_index,
        "load_manifest",
        lambda path: IndexManifest(
            documents={
                "manual/a.html": ManifestEntry(content_hash="a", chunk_ids=["a:1"]),
                "manual/b.html": ManifestEntry(content_hash="b", chunk_ids=["b:1"]),
            },
            index_signature="current-signature",
        ),
    )
    monkeypatch.setattr(routes_index, "build_index_signature", lambda **kwargs: "current-signature")
    monkeypatch.setattr(routes_index, "is_rebuild_pending", lambda path: False)
    monkeypatch.setattr(
        routes_index,
        "get_manifest_modified_at",
        lambda path: "2026-07-21T10:00:00+00:00",
    )
    client = TestClient(create_app())

    response = client.get("/api/index/status")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["chunks"] == 12
    assert response.json()["documents"] == 2
    assert response.json()["last_built_at"] == "2026-07-21T10:00:00+00:00"
    assert response.json()["index_signature"] == "current-signature"
    assert response.json()["current_signature"] == "current-signature"
    assert response.json()["config_matches"] is True
    assert response.json()["rebuild_pending"] is False
    assert response.json()["persist_dir"] == "storage/chroma"
    assert response.json()["manifest_path"] == str(manifest_path)
    assert response.json()["issue"] is None


# 验证索引为空时状态接口会返回 empty，方便部署后判断是否需要先构建索引。
def test_index_status_endpoint_reports_empty_vector_store(monkeypatch):
    class FakeVectorStore:
        # 模拟尚未构建索引的空向量库数量。
        def count(self):
            return 0

    import app.api.routes_index as routes_index

    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            chroma_persist_dir="storage/chroma",
            index_manifest_path="storage/processed/test_manifest.json",
            embedding_model_name="test-embedding-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())
    monkeypatch.setattr(routes_index, "load_manifest", lambda path: None)
    monkeypatch.setattr(routes_index, "build_index_signature", lambda **kwargs: "current-signature")
    monkeypatch.setattr(routes_index, "is_rebuild_pending", lambda path: False)
    monkeypatch.setattr(routes_index, "get_manifest_modified_at", lambda path: None)
    client = TestClient(create_app())

    response = client.get("/api/index/status")

    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["chunks"] == 0
    assert response.json()["documents"] == 0
    assert response.json()["config_matches"] is False


# 验证索引配置变化后状态会标记为 stale，提醒调用方先重建再提供问答。
def test_index_status_endpoint_reports_stale_configuration(monkeypatch):
    class FakeVectorStore:
        # 模拟仍保留旧配置向量的非空向量库。
        def count(self):
            return 12

    import app.api.routes_index as routes_index
    from app.rag.ingestion.index_manifest import IndexManifest

    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            chroma_persist_dir="storage/chroma",
            index_manifest_path="storage/processed/test_manifest.json",
            embedding_model_name="new-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())
    monkeypatch.setattr(
        routes_index,
        "load_manifest",
        lambda path: IndexManifest(documents={}, index_signature="old-signature"),
    )
    monkeypatch.setattr(routes_index, "build_index_signature", lambda **kwargs: "new-signature")
    monkeypatch.setattr(routes_index, "is_rebuild_pending", lambda path: False)
    monkeypatch.setattr(routes_index, "get_manifest_modified_at", lambda path: None)

    response = TestClient(create_app()).get("/api/index/status")

    assert response.status_code == 200
    assert response.json()["status"] == "stale"
    assert response.json()["config_matches"] is False


# 验证存在恢复标记时优先提示需要重建，避免继续使用可能不完整的向量库。
def test_index_status_endpoint_reports_rebuild_required(monkeypatch):
    class FakeVectorStore:
        # 模拟全量重建中断后残留的部分向量。
        def count(self):
            return 3

    import app.api.routes_index as routes_index
    from app.rag.ingestion.index_manifest import IndexManifest

    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            chroma_persist_dir="storage/chroma",
            index_manifest_path="storage/processed/test_manifest.json",
            embedding_model_name="test-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())
    monkeypatch.setattr(
        routes_index,
        "load_manifest",
        lambda path: IndexManifest(documents={}, index_signature="current-signature"),
    )
    monkeypatch.setattr(routes_index, "build_index_signature", lambda **kwargs: "current-signature")
    monkeypatch.setattr(routes_index, "is_rebuild_pending", lambda path: True)
    monkeypatch.setattr(routes_index, "get_manifest_modified_at", lambda path: None)

    response = TestClient(create_app()).get("/api/index/status")

    assert response.status_code == 200
    assert response.json()["status"] == "rebuild_required"
    assert response.json()["rebuild_pending"] is True


# 验证 manifest 损坏时状态接口返回可诊断信息，而不是产生未处理的 500 异常。
def test_index_status_endpoint_reports_manifest_error(monkeypatch):
    class FakeVectorStore:
        # 模拟 manifest 损坏时仍然存在的旧向量。
        def count(self):
            return 12

    import app.api.routes_index as routes_index
    from app.rag.ingestion.index_manifest import ManifestFormatError

    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            chroma_persist_dir="storage/chroma",
            index_manifest_path="storage/processed/test_manifest.json",
            embedding_model_name="test-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())

    # 模拟读取到结构损坏的索引清单。
    def fail_to_load_manifest(path):
        raise ManifestFormatError("索引清单损坏，请执行全量重建。")

    monkeypatch.setattr(routes_index, "load_manifest", fail_to_load_manifest)
    monkeypatch.setattr(routes_index, "build_index_signature", lambda **kwargs: "current-signature")
    monkeypatch.setattr(routes_index, "is_rebuild_pending", lambda path: False)
    monkeypatch.setattr(routes_index, "get_manifest_modified_at", lambda path: None)

    response = TestClient(create_app()).get("/api/index/status")

    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert response.json()["issue"] == "索引清单损坏，请执行全量重建。"


# 验证索引接口默认执行增量更新，并在成功后清理 RAG 工厂缓存。
def test_rebuild_index_defaults_to_incremental(monkeypatch):
    cache_events = []
    received = []

    class FakeResult:
        # 返回索引接口需要的统一增量统计。
        def to_dict(self):
            return {
                "mode": "incremental",
                "added_documents": 1,
                "modified_documents": 0,
                "deleted_documents": 0,
                "skipped_documents": 2,
                "written_chunks": 3,
                "total_chunks": 10,
            }

    import app.api.routes_index as routes_index

    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            data_dir="data/help",
            index_manifest_path="storage/processed/index_manifest.json",
            embedding_model_name="test-embedding-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: "vector-store")

    # 记录 API 传给统一索引服务的参数。
    def fake_update_index(**kwargs):
        received.append(kwargs)
        return FakeResult()

    monkeypatch.setattr(routes_index, "update_index", fake_update_index, raising=False)
    monkeypatch.setattr(routes_index, "clear_rag_factory_cache", lambda: cache_events.append("cleared"), raising=False)
    client = TestClient(create_app())

    response = client.post("/api/index/rebuild")

    assert response.status_code == 200
    assert response.json()["mode"] == "incremental"
    assert response.json()["written_chunks"] == 3
    assert received[0]["full"] is False
    assert received[0]["embedding_model_name"] == "test-embedding-model"
    assert received[0]["chunk_size"] == 700
    assert received[0]["chunk_overlap"] == 100
    assert cache_events == ["cleared"]


# 验证 full=true 会传给统一索引服务。
def test_rebuild_index_accepts_full_mode(monkeypatch):
    received = []

    class FakeResult:
        # 返回全量重建使用的最小测试结果。
        def to_dict(self):
            return {"mode": "full"}

    import app.api.routes_index as routes_index

    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            data_dir="data/help",
            index_manifest_path="manifest.json",
            embedding_model_name="test-embedding-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: "vector-store")

    # 记录接口收到的 full 模式并返回测试结果。
    def fake_update_index(**kwargs):
        received.append(kwargs["full"])
        return FakeResult()

    monkeypatch.setattr(routes_index, "update_index", fake_update_index, raising=False)
    monkeypatch.setattr(routes_index, "clear_rag_factory_cache", lambda: None)
    client = TestClient(create_app())

    response = client.post("/api/index/rebuild?full=true")

    assert response.status_code == 200
    assert response.json()["mode"] == "full"
    assert received == [True]


# 验证同一进程已有索引任务运行时，第二个请求会立即返回 409。
def test_rebuild_index_rejects_concurrent_request():
    import app.api.routes_index as routes_index

    routes_index.index_update_lock.acquire()
    try:
        response = TestClient(create_app()).post("/api/index/rebuild")
    finally:
        routes_index.index_update_lock.release()

    assert response.status_code == 409
    assert response.json()["detail"] == "已有索引构建任务正在运行，请稍后重试。"


# 验证手册目录异常会返回明确 503，并在异常后释放索引锁。
def test_rebuild_index_returns_service_unavailable_for_source_error(monkeypatch):
    import app.api.routes_index as routes_index
    from app.rag.ingestion.index_service import IndexSourceError

    monkeypatch.setattr(
        routes_index,
        "get_settings",
        lambda: SimpleNamespace(
            data_dir="missing",
            index_manifest_path="manifest.json",
            embedding_model_name="test-embedding-model",
            chunk_size=700,
            chunk_overlap=100,
        ),
    )
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: "vector-store")

    # 模拟部署时手册挂载目录缺失。
    def fail_update(**kwargs):
        raise IndexSourceError("手册目录不存在或不是目录: /missing")

    monkeypatch.setattr(routes_index, "update_index", fail_update)
    response = TestClient(create_app()).post("/api/index/rebuild")

    assert response.status_code == 503
    assert response.json()["detail"] == "手册目录不存在或不是目录: /missing"
    assert routes_index.index_update_lock.acquire(blocking=False) is True
    routes_index.index_update_lock.release()


def test_chat_rejects_empty_question():
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"question": "   "})

    assert response.status_code == 422


def test_chat_uses_rag_chain(monkeypatch):
    class FakeChain:
        def answer(self, question: str):
            assert question == "页面编辑器有哪些区域？"
            return ChatResponse(
                answer="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                sources=[
                    SourceSnippet(
                        title="页面编辑器/简介",
                        source_path="页面编辑器/简介.md",
                        snippet="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                        evidence_ids=["资料 1"],
                        images=["页面编辑器/1.png"],
                    )
                ],
            )

    import app.api.routes_chat as routes_chat

    monkeypatch.setattr(routes_chat, "create_rag_chain", lambda: FakeChain())
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"question": "页面编辑器有哪些区域？"})

    assert response.status_code == 200
    assert response.json()["answer"] == "页面编辑器包括菜单栏、工具栏、工具箱和配置窗。"
    assert response.json()["sources"][0]["evidence_ids"] == ["资料 1"]
    assert response.json()["sources"][0]["images"] == ["页面编辑器/1.png"]


# 验证 RAG 可预期异常会返回友好的 503，而不是把 Python 内部错误暴露给前端。
def test_chat_returns_service_unavailable_for_rag_error(monkeypatch):
    class FakeChain:
        # 模拟向量库为空时 Chain 抛出的业务异常。
        def answer(self, question: str):
            raise IndexNotReadyError()

    import app.api.routes_chat as routes_chat

    monkeypatch.setattr(routes_chat, "create_rag_chain", lambda: FakeChain())
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"question": "如何创建采集工程？"})

    assert response.status_code == 503
    assert response.json()["detail"] == "知识库索引还没有构建，请先执行索引构建。"


# 验证问答接口会记录耗时、来源数和图片数等可观测指标。
def test_chat_logs_observable_metrics(monkeypatch, caplog):
    class FakeChain:
        def answer(self, question: str):
            return ChatResponse(
                answer="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                sources=[
                    SourceSnippet(
                        title="页面编辑器/简介",
                        source_path="页面编辑器/简介.md",
                        snippet="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                        evidence_ids=["资料 1"],
                        images=["页面编辑器/1.png", "页面编辑器/2.png"],
                    )
                ],
            )

    import app.api.routes_chat as routes_chat

    monkeypatch.setattr(routes_chat, "create_rag_chain", lambda: FakeChain())
    caplog.set_level(logging.INFO, logger="app.api.routes_chat")
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"question": "页面编辑器有哪些区域？"})

    assert response.status_code == 200
    log_text = caplog.text
    assert "chat_completed" in log_text
    assert "question_length=11" in log_text
    assert "source_count=1" in log_text
    assert "image_count=2" in log_text
    assert "elapsed_ms=" in log_text
