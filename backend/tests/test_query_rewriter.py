import httpx

from app.rag.retrieval.query_rewriter import StaticQueryRewriter, analyze_query


def test_analyze_query_marks_workflow_question():
    analysis = analyze_query("如何创建采集工程，如何运行它呢？")

    assert analysis.intent == "workflow"
    assert analysis.needs_steps is True
    assert "采集工程" in analysis.entities


def test_static_query_rewriter_keeps_original_and_adds_workflow_queries():
    rewriter = StaticQueryRewriter()

    result = rewriter.rewrite("如何创建采集工程，如何运行它呢？")

    assert result.original_question == "如何创建采集工程，如何运行它呢？"
    assert "如何创建采集工程，如何运行它呢？" in result.queries
    assert any("启动" in query or "运行" in query for query in result.queries)
    assert len(result.queries) <= 5


def test_deepseek_query_rewriter_parses_json_response(monkeypatch):
    captured = {}

    class FakeResponse:
        # 模拟 DeepSeek 正常 HTTP 响应。
        def raise_for_status(self):
            return None

        # 返回结构化 JSON 字符串，验证改写器能解析 choices 内容。
        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"queries":["如何新建数采工程？","如何部署启动采集工程？"]}'
                        }
                    }
                ]
            }

    class FakeHttpClient:
        # 记录 httpx 参数，确认不会读取系统代理。
        def __init__(self, **kwargs):
            captured.update(kwargs)

        # 模拟上下文管理器进入。
        def __enter__(self):
            return self

        # 模拟上下文管理器退出。
        def __exit__(self, exc_type, exc, tb):
            return None

        # 记录请求体并返回假响应。
        def post(self, url, json, headers):
            captured["payload"] = json
            return FakeResponse()

    import app.rag.retrieval.query_rewriter as query_rewriter

    monkeypatch.setattr(query_rewriter.httpx, "Client", FakeHttpClient)
    rewriter = query_rewriter.DeepSeekQueryRewriter(
        api_key="test",
        base_url="https://example.com",
        model="deepseek-v4-flash",
        max_queries=4,
    )

    result = rewriter.rewrite("如何创建采集工程，如何运行它呢？")

    assert captured["trust_env"] is False
    assert result.used_llm is True
    assert result.queries[0] == "如何创建采集工程，如何运行它呢？"
    assert "如何部署启动采集工程？" in result.queries


def test_deepseek_query_rewriter_falls_back_to_static_rewriter(monkeypatch):
    class FakeHttpClient:
        # 接受 httpx 参数但不发真实请求。
        def __init__(self, **kwargs):
            pass

        # 模拟上下文管理器进入。
        def __enter__(self):
            return self

        # 模拟上下文管理器退出。
        def __exit__(self, exc_type, exc, tb):
            return None

        # 模拟 DeepSeek 超时，验证改写失败降级。
        def post(self, url, json, headers):
            raise httpx.TimeoutException("timeout")

    import app.rag.retrieval.query_rewriter as query_rewriter

    monkeypatch.setattr(query_rewriter.httpx, "Client", FakeHttpClient)
    rewriter = query_rewriter.DeepSeekQueryRewriter(
        api_key="test",
        base_url="https://example.com",
        model="deepseek-v4-flash",
        max_queries=5,
    )

    result = rewriter.rewrite("如何创建采集工程，如何运行它呢？")

    assert result.used_llm is False
    assert result.queries[0] == "如何创建采集工程，如何运行它呢？"
    assert any("启动" in query for query in result.queries)
