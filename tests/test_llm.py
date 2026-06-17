from app.rag.llm import DeepSeekClient


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

    import app.rag.llm as llm

    monkeypatch.setattr(llm.httpx, "Client", FakeHttpClient)
    client = DeepSeekClient(api_key="test", base_url="https://example.com", model="deepseek-v4-flash")

    assert client.generate("问题", ["片段"]) == "回答"
    assert captured["trust_env"] is False
    user_prompt = captured["payload"]["messages"][1]["content"]
    assert "回答要求" in user_prompt
    assert "关键步骤或结论后标注资料编号" in user_prompt
