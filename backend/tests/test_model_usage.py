import httpx

from app.observability.model_usage import capture_model_usage, record_model_usage
from app.rag.generation.llm import DeepSeekClient


def test_deepseek_payload_uses_flash_without_thinking(monkeypatch):
    captured: dict = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [{"message": {"content": "回答"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "prompt_cache_hit_tokens": 2},
            }

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, url: str, json: dict, headers: dict) -> FakeResponse:
            captured["payload"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    client = DeepSeekClient("key", "https://api.deepseek.com", "deepseek-v4-flash")

    with capture_model_usage() as collector:
        assert client.generate("问题", ["资料"]) == "回答"

    assert captured["payload"]["model"] == "deepseek-v4-flash"
    assert captured["payload"]["thinking"] == {"type": "disabled"}
    assert collector.events[0].operation == "answer"
    assert collector.events[0].prompt_tokens == 10
    assert collector.events[0].completion_tokens == 4
    assert collector.events[0].cache_hit_tokens == 2


def test_usage_outside_capture_context_is_ignored():
    record_model_usage(operation="judge", model="deepseek-v4-flash", usage={"prompt_tokens": 10})

    with capture_model_usage() as collector:
        pass

    assert collector.events == []


def test_streaming_answer_records_usage_from_terminal_event(monkeypatch):
    captured: dict = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_lines(self):
            return iter([
                'data: {"choices":[{"delta":{"content":"回答"}}]}',
                'data: {"choices":[],"usage":{"prompt_tokens":7,"completion_tokens":2}}',
                "data: [DONE]",
            ])

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def stream(self, method: str, url: str, json: dict, headers: dict) -> FakeResponse:
            captured["payload"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    client = DeepSeekClient("key", "https://api.deepseek.com", "deepseek-v4-flash")

    with capture_model_usage() as collector:
        assert list(client.generate_stream("问题", ["资料"])) == ["回答"]

    assert captured["payload"]["model"] == "deepseek-v4-flash"
    assert captured["payload"]["thinking"] == {"type": "disabled"}
    assert len(collector.events) == 1
    assert collector.events[0].operation == "answer_stream"
    assert collector.events[0].prompt_tokens == 7
    assert collector.events[0].completion_tokens == 2
