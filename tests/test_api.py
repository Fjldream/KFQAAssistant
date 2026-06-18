import logging

from fastapi.testclient import TestClient

from app.schemas.chat import ChatResponse, SourceSnippet
from app.main import create_app


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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
