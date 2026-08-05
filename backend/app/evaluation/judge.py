import json
from dataclasses import dataclass

import httpx

from app.core.config import Settings
from app.observability.model_usage import DEEPSEEK_FLASH_MODEL, ModelUsageEvent, record_model_usage


class JudgementError(RuntimeError):
    """裁判调用失败：HTTP 错误或返回内容不是合法 JSON。"""


@dataclass(frozen=True)
class JudgementCompletion:
    data: dict
    usage: ModelUsageEvent | None = None


class JudgeProtocol:
    def complete_json(self, system_prompt: str, user_prompt: str) -> JudgementCompletion:
        ...


class JudgementClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = DEEPSEEK_FLASH_MODEL
        self.timeout_seconds = timeout_seconds

    def complete_json(self, system_prompt: str, user_prompt: str) -> JudgementCompletion:
        payload = {
            "model": DEEPSEEK_FLASH_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 1600,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=self.timeout_seconds, trust_env=False) as client:
                response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            usage = record_model_usage("judge", DEEPSEEK_FLASH_MODEL, data.get("usage"))
            return JudgementCompletion(data=json.loads(content), usage=usage)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, AttributeError, json.JSONDecodeError, ValueError) as exc:
            raise JudgementError() from exc


def create_judgement_client(settings: Settings) -> JudgementClient:
    return JudgementClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_judge_model,
        timeout_seconds=settings.deepseek_judge_timeout_seconds,
    )
