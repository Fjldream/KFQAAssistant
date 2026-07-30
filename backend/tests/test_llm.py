import httpx

from app.rag.errors import LLMGenerationError
from app.rag.generation.llm import DeepSeekClient


def test_deepseek_client_does_not_use_system_proxy(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "回答"}}]}

    class FakeHttpClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, url, json, headers):
            captured["payload"] = json
            return FakeResponse()

    import app.rag.generation.llm as llm

    monkeypatch.setattr(llm.httpx, "Client", FakeHttpClient)
    client = DeepSeekClient(api_key="test", base_url="https://example.com", model="deepseek-v4-flash")

    assert client.generate("问题", ["片段"]) == "回答"
    assert captured["trust_env"] is False
    user_prompt = captured["payload"]["messages"][1]["content"]
    assert "回答要求" in user_prompt
    assert "关键步骤或结论后标注资料编号" in user_prompt


# 验证 DeepSeek 超时会被包装成业务异常，API 层可以给用户稳定提示。
def test_deepseek_client_wraps_timeout_as_llm_generation_error(monkeypatch):
    class FakeHttpClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, url, json, headers):
            raise httpx.TimeoutException("timeout")

    import app.rag.generation.llm as llm

    monkeypatch.setattr(llm.httpx, "Client", FakeHttpClient)
    client = DeepSeekClient(api_key="test", base_url="https://example.com", model="deepseek-v4-flash")

    try:
        client.generate("问题", ["片段"])
    except LLMGenerationError as exc:
        assert exc.public_message == "大模型服务暂时不可用，请稍后重试。"
    else:
        raise AssertionError("DeepSeek 超时时应该抛出 LLMGenerationError")
