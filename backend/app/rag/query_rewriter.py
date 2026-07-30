from dataclasses import dataclass
import json
from typing import Protocol

import httpx


REWRITE_SYSTEM_PROMPT = """你是 KingIAsk 的 RAG 检索查询改写器。
你的任务是把用户问题改写为 3 到 5 条适合产品手册检索的短查询。
只输出 JSON，不要输出解释。"""


@dataclass(frozen=True)
class QueryAnalysis:
    original_question: str
    intent: str
    entities: list[str]
    needs_images: bool
    needs_steps: bool


@dataclass(frozen=True)
class RewriteResult:
    original_question: str
    queries: list[str]
    analysis: QueryAnalysis
    used_llm: bool = False


class QueryRewriterProtocol(Protocol):
    # 将用户问题改写成一个或多个适合检索的查询。
    def rewrite(self, question: str) -> RewriteResult:
        ...


# 保序去重并限制查询数量，确保原始问题始终排在第一位。
def _deduplicate_queries(original_question: str, queries: list[str], max_queries: int) -> list[str]:
    deduplicated: list[str] = []
    for query in [original_question, *queries]:
        normalized = query.strip()
        if normalized and normalized not in deduplicated:
            deduplicated.append(normalized)
        if len(deduplicated) >= max_queries:
            break
    return deduplicated or [original_question]


# 从用户问题中抽取当前阶段最重要的产品实体。
def _extract_entities(question: str) -> list[str]:
    candidates = ["采集工程", "数采工程", "数据组态工程", "数据源工程", "客户端工程", "运维中心", "页面编辑器"]
    return [entity for entity in candidates if entity in question]


# 分析用户问题的意图，给后续查询改写和上下文组装提供轻量信号。
def analyze_query(question: str) -> QueryAnalysis:
    workflow_terms = ["创建", "启动", "部署", "运行", "发布", "配置", "进入", "查看"]
    troubleshooting_terms = ["报错", "失败", "无法", "不能"]
    visual_terms = ["图片", "截图", "按钮", "页面", "界面"]
    if any(term in question for term in troubleshooting_terms):
        intent = "troubleshooting"
    elif "如何" in question and any(term in question for term in workflow_terms):
        intent = "workflow"
    elif any(term in question for term in visual_terms):
        intent = "visual"
    elif any(term in question for term in ["什么是", "介绍", "含义"]):
        intent = "concept"
    else:
        intent = "general"
    return QueryAnalysis(
        original_question=question,
        intent=intent,
        entities=_extract_entities(question),
        needs_images=any(term in question for term in visual_terms),
        needs_steps=intent in {"workflow", "troubleshooting"},
    )


class StaticQueryRewriter:
    # 保存最大查询数量，避免静态兜底也生成过多检索请求。
    def __init__(self, max_queries: int = 5) -> None:
        self.max_queries = max_queries

    # 根据本地意图分析生成兜底查询，不依赖任何外部大模型。
    def rewrite(self, question: str) -> RewriteResult:
        analysis = analyze_query(question)
        queries: list[str] = []
        if analysis.intent == "workflow" and any(entity in analysis.entities for entity in ["采集工程", "数采工程"]):
            queries.extend(
                [
                    "如何新建数采工程？",
                    "数采工程创建后如何发布工程？",
                    "如何在运维中心部署并启动采集工程？",
                    "数采工程运行需要配置哪些节点和端口？",
                ]
            )
        return RewriteResult(
            original_question=question,
            queries=_deduplicate_queries(question, queries, self.max_queries),
            analysis=analysis,
            used_llm=False,
        )


class DeepSeekQueryRewriter:
    # 保存 DeepSeek 改写所需配置，并准备静态降级改写器。
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: int = 60,
        max_queries: int = 5,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_queries = max_queries
        self.fallback = StaticQueryRewriter(max_queries=max_queries)

    # 调用 DeepSeek 生成检索查询，失败时返回本地静态改写结果。
    def rewrite(self, question: str) -> RewriteResult:
        analysis = analyze_query(question)
        if not self.api_key:
            return self.fallback.rewrite(question)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "请把下面的问题改写成适合检索 KF 产品手册的查询。"
                        "输出格式必须是：{\"queries\":[\"查询1\",\"查询2\"]}。\n"
                        f"问题：{question}"
                    ),
                },
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
            parsed = json.loads(content)
            queries = [str(query) for query in parsed.get("queries", []) if str(query).strip()]
            return RewriteResult(
                original_question=question,
                queries=_deduplicate_queries(question, queries, self.max_queries),
                analysis=analysis,
                used_llm=True,
            )
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
            return self.fallback.rewrite(question)
