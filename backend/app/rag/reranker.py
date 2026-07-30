from dataclasses import dataclass
import re

from app.rag.retriever import RetrievedChunk


WORKFLOW_QUERY_TERMS = ("如何", "怎么", "步骤", "启动", "运行", "创建", "新建", "部署", "发布")
WORKFLOW_EVIDENCE_TERMS = ("发布", "运维中心", "运行的节点", "添加端口", "部署", "启动")
PATH_BONUS_TERMS = ("教程", "工程开发", "操作流程", "新手指引")
VISUAL_QUERY_TERMS = ("图片", "截图", "界面", "按钮", "页面", "在哪里", "在哪")


@dataclass(frozen=True)
class RerankReason:
    label: str
    score: float


# 判断用户问题是否更像操作流程类问题。
def _is_workflow_query(query: str) -> bool:
    return any(term in query for term in WORKFLOW_QUERY_TERMS) and "工程" in query


# 从中文问题中抽取短实体词，用于判断候选资料是否覆盖用户问到的对象。
def _extract_query_terms(query: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9_.+-]+|[\u4e00-\u9fff]+", query)
    expanded: list[str] = []
    for term in terms:
        if len(term) >= 2:
            expanded.append(term)
        if re.fullmatch(r"[\u4e00-\u9fff]+", term) and len(term) >= 4:
            expanded.extend(term[index : index + 4] for index in range(len(term) - 3))
    return list(dict.fromkeys(expanded))


# 计算候选资料的重排原因和加分项，方便调试脚本解释为什么某段资料靠前。
def _score_reasons(query: str, candidate: RetrievedChunk) -> list[RerankReason]:
    chunk = candidate.chunk
    title_source = f"{chunk.title}\n{chunk.source_path}"
    text = f"{title_source}\n{chunk.content}"
    reasons: list[RerankReason] = []

    workflow_matches = [term for term in WORKFLOW_EVIDENCE_TERMS if term in text]
    if _is_workflow_query(query) and len(workflow_matches) >= 3:
        reasons.append(RerankReason("包含操作流程信号", 0.45))

    if any(term in title_source for term in PATH_BONUS_TERMS):
        reasons.append(RerankReason("来源属于教程或工程开发章节", 0.18))

    query_terms = _extract_query_terms(query)
    if query_terms and any(term in text for term in query_terms):
        reasons.append(RerankReason("覆盖问题中的关键对象", 0.12))

    if chunk.images and (any(term in query for term in VISUAL_QUERY_TERMS) or _is_workflow_query(query)):
        reasons.append(RerankReason("包含可查看的相关图片", 0.06))

    return reasons


# 计算单个候选资料的最终重排分，基础分来自前置检索，规则分只做轻量修正。
def rerank_score(query: str, candidate: RetrievedChunk) -> float:
    base_score = candidate.score or 0.0
    return base_score + sum(reason.score for reason in _score_reasons(query, candidate))


# 返回候选资料的中文重排原因，用于 inspect_retrieval 调试输出。
def explain_rerank(query: str, candidate: RetrievedChunk) -> list[str]:
    return [reason.label for reason in _score_reasons(query, candidate)]


# 对候选资料做轻量重排序，让流程完整、章节更贴近的问题资料排在前面。
def rerank(query: str, candidates: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
    return sorted(candidates, key=lambda item: rerank_score(query, item), reverse=True)[:limit]
