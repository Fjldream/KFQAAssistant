import json

import httpx

from app.core.config import Settings


class JudgementError(RuntimeError):
    """裁判调用失败：HTTP 错误或返回内容不是合法 JSON。"""


class JudgeProtocol:
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


class JudgementClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=self.timeout_seconds, trust_env=False) as client:
                response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            return json.loads(content)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, AttributeError, json.JSONDecodeError, ValueError) as exc:
            raise JudgementError() from exc


def create_judgement_client(settings: Settings) -> JudgementClient:
    return JudgementClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_judge_model,
        timeout_seconds=settings.deepseek_judge_timeout_seconds,
    )
