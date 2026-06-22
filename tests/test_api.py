import logging

from fastapi.testclient import TestClient

from app.schemas.chat import ChatResponse, SourceSnippet
from app.main import create_app
from app.rag.errors import IndexNotReadyError


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# 验证索引状态接口会返回向量库 chunk 数量和持久化目录。
def test_index_status_endpoint_reports_vector_store_count(monkeypatch):
    class FakeVectorStore:
        # 模拟已构建索引的向量库数量。
        def count(self):
            return 12

    import app.api.routes_index as routes_index

    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())
    client = TestClient(create_app())

    response = client.get("/api/index/status")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["chunks"] == 12
    assert response.json()["persist_dir"] == "storage/chroma"


# 验证索引为空时状态接口会返回 empty，方便部署后判断是否需要先构建索引。
def test_index_status_endpoint_reports_empty_vector_store(monkeypatch):
    class FakeVectorStore:
        # 模拟尚未构建索引的空向量库数量。
        def count(self):
            return 0

    import app.api.routes_index as routes_index

    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())
    client = TestClient(create_app())

    response = client.get("/api/index/status")

    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["chunks"] == 0


# 验证重建索引成功后会清理 RAG 工厂缓存，避免后续请求继续复用旧对象。
def test_rebuild_index_clears_rag_factory_cache(monkeypatch):
    cache_events = []

    class FakeVectorStore:
        # 模拟重建索引并返回写入的 chunk 数量。
        def rebuild(self, chunks):
            return len(chunks)

    import app.api.routes_index as routes_index

    monkeypatch.setattr(routes_index, "load_documents", lambda data_dir: ["doc"])
    monkeypatch.setattr(routes_index, "split_documents", lambda documents: ["chunk"])
    monkeypatch.setattr(routes_index, "create_vector_store", lambda: FakeVectorStore())
    monkeypatch.setattr(routes_index, "clear_rag_factory_cache", lambda: cache_events.append("cleared"), raising=False)
    client = TestClient(create_app())

    response = client.post("/api/index/rebuild")

    assert response.status_code == 200
    assert response.json()["chunks"] == 1
    assert cache_events == ["cleared"]


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
