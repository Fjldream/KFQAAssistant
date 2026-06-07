import httpx


SYSTEM_PROMPT = """你是 KF 产品手册问答助手。
你只能根据提供的手册片段回答。
如果手册片段中没有答案，请回答：手册中没有找到相关说明。
不要编造菜单、按钮、版本号或配置路径。
优先用简洁步骤回答产品使用问题。"""


# DeepSeek API 客户端，负责把检索上下文发送给大模型生成回答。
class DeepSeekClient:
    # 保存 API 地址、模型名、密钥和超时配置，密钥只来自环境变量。
    def __init__(self, api_key: str, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    # 根据用户问题和检索片段构造严格 prompt，并调用 DeepSeek chat completions 接口。
    def generate(self, question: str, contexts: list[str]) -> str:
        context_text = "\n\n---\n\n".join(contexts)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"问题：{question}\n\n手册片段：\n{context_text}"},
            ],
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=self.timeout_seconds, trust_env=False) as client:
            response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()
