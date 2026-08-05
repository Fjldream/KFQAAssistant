import httpx
import pytest
from app.evaluation.judge import JudgementClient, JudgementCompletion, JudgementError, create_judgement_client
from app.observability.model_usage import capture_model_usage
from app.core.config import Settings


class FakeResponse:
    def __init__(self, json_data: dict | str, raise_error: bool = False):
        self._json_data = json_data
        self._raise_error = raise_error

    def raise_for_status(self) -> None:
        if self._raise_error:
            request = httpx.Request("POST", "https://api.deepseek.com/chat/completions")
            response = httpx.Response(500, request=request)
            raise httpx.HTTPStatusError("500 Server Error", request=request, response=response)

    def json(self):
        if isinstance(self._json_data, str):
            raise ValueError("bad json")
        return self._json_data


class FakeClient:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = responses
        self.calls: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url: str, json: dict, headers: dict):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.responses.pop(0)


def test_complete_json_parses_llm_content(monkeypatch):
    fake = FakeClient([
        FakeResponse({
            "choices": [{"message": {"content": '{"claims": ["a", "b"]}'}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 5, "prompt_cache_hit_tokens": 3},
        })
    ])
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: fake)
    judge = JudgementClient(api_key="k", base_url="https://api.deepseek.com", model="deepseek-v4-flash")
    with capture_model_usage():
        result = judge.complete_json(system_prompt="sys", user_prompt="user")
    assert isinstance(result, JudgementCompletion)
    assert result.data == {"claims": ["a", "b"]}
    assert result.usage is not None
    assert result.usage.prompt_tokens == 11
    assert fake.calls[0]["json"]["model"] == "deepseek-v4-flash"
    assert fake.calls[0]["headers"]["Authorization"] == "Bearer k"
    assert fake.calls[0]["url"].endswith("/chat/completions")
    assert fake.calls[0]["json"]["temperature"] == 0.0
    assert fake.calls[0]["json"]["max_tokens"] == 1600
    assert fake.calls[0]["json"]["thinking"] == {"type": "disabled"}
    assert fake.calls[0]["json"]["response_format"] == {"type": "json_object"}


def test_complete_json_ignores_usage_outside_capture_context(monkeypatch):
    fake = FakeClient([
        FakeResponse({
            "choices": [{"message": {"content": '{"claims": ["a"]}'}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 5},
        })
    ])
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: fake)
    judge = JudgementClient(api_key="k", base_url="https://api.deepseek.com", model="deepseek-v4-flash")

    result = judge.complete_json(system_prompt="sys", user_prompt="user")

    assert result.usage is None


def test_complete_json_raises_on_http_error(monkeypatch):
    fake = FakeClient([FakeResponse({}, raise_error=True)])
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: fake)
    judge = JudgementClient(api_key="k", base_url="https://api.deepseek.com", model="m")
    with pytest.raises(JudgementError):
        judge.complete_json("sys", "user")


def test_complete_json_raises_on_bad_json(monkeypatch):
    fake = FakeClient([FakeResponse("not json")])
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: fake)
    judge = JudgementClient(api_key="k", base_url="https://api.deepseek.com", model="m")
    with pytest.raises(JudgementError):
        judge.complete_json("sys", "user")


def test_create_judgement_client_uses_judge_model(monkeypatch):
    settings = Settings(deepseek_api_key="k", deepseek_judge_model="deepseek-v4-flash")
    client = create_judgement_client(settings)
    assert client.model == "deepseek-v4-flash"
