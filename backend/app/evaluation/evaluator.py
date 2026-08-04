from time import perf_counter
from typing import Protocol

from app.evaluation.judge import JudgeProtocol
from app.evaluation.metrics_registry import get_metric
from app.evaluation.models import CaseResult, EvaluationCase, EvaluationTurn, TurnResult
from app.rag.generation.answer_policy import is_no_answer
from app.schemas.chat import ChatHistoryMessage, ChatResponse


class ChainProtocol(Protocol):
    # 执行一次 RAG 问答，评测器只依赖这个稳定接口，避免绑定具体 RagChain 实现。
    def answer(
        self,
        question: str,
        conversation_summary: str = "",
        conversation_turn_count: int = 0,
        recent_messages: list[ChatHistoryMessage] | None = None,
    ) -> ChatResponse:
        ...


# 判断某个关键词是否出现在给定文本中，当前 v1 使用确定性包含规则。
def _contains_keyword(text: str, keyword: str) -> bool:
    return keyword in text


# 把旧版必选关键词和新版同义词组统一成“每组至少命中一个”的规则。
def _build_required_groups(keywords: list[str], keyword_groups: list[list[str]]) -> list[list[str]]:
    groups = [[keyword] for keyword in keywords]
    groups.extend([group for group in keyword_groups if group])
    return groups


# 按关键词组检查文本命中情况，返回实际命中的表达和未命中的语义组。
def _match_required_groups(text: str, groups: list[list[str]]) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []
    for group in groups:
        matched_keyword = next((keyword for keyword in group if _contains_keyword(text, keyword)), "")
        if matched_keyword:
            matched.append(matched_keyword)
        else:
            missing.append(" / ".join(group))
    return matched, missing


# 把来源对象整理成可搜索文本，用于判断来源标题、路径、片段是否命中预期。
def _source_search_text(response: ChatResponse) -> str:
    parts: list[str] = []
    for source in response.sources:
        parts.extend([source.title, source.source_path, source.snippet])
    return "\n".join(parts)


# 统计回答中返回的图片数量。
def _count_images(response: ChatResponse) -> int:
    return sum(len(source.images) for source in response.sources)


# 根据单轮规则和问答响应生成 TurnResult；语义评估结果作为可选字段写入，默认保持旧行为。
def _evaluate_turn(
    turn: EvaluationTurn,
    response: ChatResponse,
    elapsed_ms: float,
    faithfulness_score: float | None = None,
    faithfulness_claims: list[dict] | None = None,
    faithfulness_elapsed_ms: float = 0.0,
) -> TurnResult:
    answer_and_sources = f"{response.answer}\n{_source_search_text(response)}"
    source_text = _source_search_text(response)
    matched_keywords, missing_keywords = _match_required_groups(
        answer_and_sources,
        _build_required_groups(turn.expected_keywords, turn.expected_keyword_groups),
    )
    matched_source_keywords, missing_source_keywords = _match_required_groups(
        source_text,
        _build_required_groups(turn.expected_source_keywords, turn.expected_source_keyword_groups),
    )
    forbidden_source_matches = [
        keyword for keyword in turn.forbidden_source_keywords if _contains_keyword(source_text, keyword)
    ]
    image_count = _count_images(response)
    source_count = len(response.sources)
    keyword_passed = not missing_keywords
    source_passed = not missing_source_keywords and not forbidden_source_matches and source_count >= turn.min_sources
    image_passed = image_count >= turn.min_images and (not turn.expect_images or image_count > 0)
    actual_no_answer = is_no_answer(response.answer) and source_count == 0
    no_answer_passed = actual_no_answer if turn.expect_no_answer else not actual_no_answer
    passed = keyword_passed and source_passed and image_passed and no_answer_passed

    return TurnResult(
        question=turn.question,
        answer=response.answer,
        standalone_question=response.standalone_question or None,
        passed=passed,
        keyword_passed=keyword_passed,
        source_passed=source_passed,
        image_passed=image_passed,
        no_answer_passed=no_answer_passed,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        matched_source_keywords=matched_source_keywords,
        missing_source_keywords=missing_source_keywords,
        forbidden_source_matches=forbidden_source_matches,
        sources=[source.model_dump() for source in response.sources],
        image_count=image_count,
        source_count=source_count,
        elapsed_ms=elapsed_ms,
        faithfulness_score=faithfulness_score,
        faithfulness_claims=faithfulness_claims or [],
        faithfulness_elapsed_ms=faithfulness_elapsed_ms,
    )


# 根据轮次评测结果生成面向报告展示的失败原因。
def _build_failure_reasons(turn_results: list[TurnResult]) -> list[str]:
    reasons: list[str] = []
    for index, result in enumerate(turn_results, start=1):
        if result.passed:
            continue
        if result.missing_keywords:
            reasons.append(f"第 {index} 轮缺少答案关键词：{', '.join(result.missing_keywords)}")
        if result.missing_source_keywords:
            reasons.append(f"第 {index} 轮缺少来源关键词：{', '.join(result.missing_source_keywords)}")
        if result.forbidden_source_matches:
            reasons.append(f"第 {index} 轮命中禁止来源：{', '.join(result.forbidden_source_matches)}")
        if not result.image_passed:
            reasons.append(f"第 {index} 轮图片数量不满足要求")
        if not result.no_answer_passed:
            reasons.append(f"第 {index} 轮拒答行为不符合预期")
    return reasons


# 执行一个完整评测用例，连续对话会把上一轮摘要和最近消息传给下一轮；
# 语义评估开启时对非拒答轮次运行第一个已注册指标并写入 TurnResult。
def evaluate_case(
    chain: ChainProtocol,
    case: EvaluationCase,
    judge: JudgeProtocol | None = None,
    semantic_enabled: bool = True,
    metrics: tuple[str, ...] = ("faithfulness",),
) -> CaseResult:
    conversation_summary = ""
    recent_messages: list[ChatHistoryMessage] = []
    turn_results: list[TurnResult] = []
    case_started = perf_counter()

    for turn_index, turn in enumerate(case.turns):
        turn_started = perf_counter()
        response = chain.answer(
            turn.question,
            conversation_summary=conversation_summary,
            conversation_turn_count=turn_index,
            recent_messages=recent_messages,
        )
        elapsed_ms = (perf_counter() - turn_started) * 1000
        faithfulness_score = None
        faithfulness_claims: list[dict] = []
        faithfulness_elapsed_ms = 0.0
        is_refusal = is_no_answer(response.answer) or not response.sources
        if judge is not None and semantic_enabled and not is_refusal and metrics:
            metric = get_metric(metrics[0])
            result = metric.evaluate(
                response.answer,
                [source.snippet for source in response.sources],
                judge,
            )
            faithfulness_score = result.score
            faithfulness_claims = result.details.get("claims", [])
            faithfulness_elapsed_ms = result.details.get("elapsed_ms", 0.0)
        turn_result = _evaluate_turn(
            turn,
            response,
            elapsed_ms,
            faithfulness_score,
            faithfulness_claims,
            faithfulness_elapsed_ms,
        )
        turn_results.append(turn_result)

        recent_messages = [
            *recent_messages,
            ChatHistoryMessage(role="user", content=turn.question),
            ChatHistoryMessage(role="assistant", content=response.answer),
        ][-8:]
        conversation_summary = response.conversation_summary

    passed = all(result.passed for result in turn_results)
    return CaseResult(
        case_id=case.id,
        category=case.category,
        priority=case.priority,
        case_type=case.case_type,
        passed=passed,
        turn_results=turn_results,
        failure_reasons=_build_failure_reasons(turn_results),
        elapsed_ms=(perf_counter() - case_started) * 1000,
    )
