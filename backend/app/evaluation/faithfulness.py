# backend/app/evaluation/faithfulness.py
from dataclasses import dataclass, field
from time import perf_counter

from app.evaluation.judge import JudgementCompletion, JudgementError, JudgeProtocol
from app.evaluation.models import MetricStatus
from app.observability.model_usage import model_usage_to_dict
from app.rag.generation.answer_policy import is_no_answer


SPLIT_SYSTEM_PROMPT = """你是 RAG 回答忠实度评估助手。
你的任务是把用户回答拆成多个独立的事实声明（claim）。
要求：
1. 每个声明必须是可以独立验证真伪的陈述句。
2. 去掉"根据手册""参考""手册中"等引导语和来源引用。
3. 只输出 JSON：{"claims": ["声明1", "声明2", ...]}
4. 如果回答没有可拆的事实声明（如拒答、纯问候），输出 {"claims": []}。"""

SUPPORT_SYSTEM_PROMPT = """你是 RAG 回答忠实度评估助手。
判断一条声明能否由给定的手册片段支持。
规则：
1. 只有手册片段中明确出现或可直接推断的内容才算"支持"。
2. 手册片段没有提到、或与手册矛盾的，都算"不支持"（编造）。
3. 只输出 JSON：{"supported": true/false, "evidence": "手册中的依据原文；无依据则输出空字符串"}。"""

BATCH_SYSTEM_PROMPT = """你是 RAG 回答忠实度评估助手。
把回答拆分为可验证的事实声明，并逐条判断是否能由手册片段支持。
只输出 JSON：{"claims": [{"claim": "声明", "supported": true/false, "evidence": "依据或空字符串"}]}。
每条 claim 必须有 boolean 类型的 supported。"""


@dataclass(frozen=True)
class ClaimJudgement:
    claim: str
    supported: bool
    evidence: str


@dataclass(frozen=True)
class FaithfulnessResult:
    score: float | None
    claims: list[dict] = field(default_factory=list)
    elapsed_ms: float = 0.0
    status: MetricStatus = MetricStatus.PASSED
    error_code: str | None = None
    token_usage: object | None = None


def split_claims(judge: JudgeProtocol, answer: str) -> list[str]:
    completion = judge.complete_json(SPLIT_SYSTEM_PROMPT, f"回答：\n{answer}")
    data = completion.data if isinstance(completion, JudgementCompletion) else completion
    claims = data.get("claims", [])
    return [str(claim).strip() for claim in claims if str(claim).strip()]


def judge_claim_support(judge: JudgeProtocol, claim: str, contexts: list[str]) -> ClaimJudgement:
    context_text = "\n\n---\n\n".join(contexts)
    completion = judge.complete_json(
        SUPPORT_SYSTEM_PROMPT,
        f"声明：{claim}\n\n手册片段：\n{context_text}",
    )
    data = completion.data if isinstance(completion, JudgementCompletion) else completion
    raw = data.get("supported", False)
    if isinstance(raw, bool):
        supported = raw
    elif isinstance(raw, str):
        supported = raw.strip().lower() in ("true", "1", "yes")
    else:
        supported = bool(raw)
    return ClaimJudgement(
        claim=claim,
        supported=supported,
        evidence=str(data.get("evidence", "")),
    )


def compute_faithfulness(judge: JudgeProtocol, answer: str, contexts: list[str]) -> FaithfulnessResult:
    started = perf_counter()
    elapsed = lambda: (perf_counter() - started) * 1000
    if not answer.strip() or is_no_answer(answer):
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed(), status=MetricStatus.SKIPPED)
    if not contexts:
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed(), status=MetricStatus.ERROR, error_code="missing_contexts")
    try:
        context_text = "\n\n---\n\n".join(contexts)
        completion = judge.complete_json(
            BATCH_SYSTEM_PROMPT,
            f"回答：\n{answer}\n\n手册片段：\n{context_text}",
        )
    except JudgementError:
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed(), status=MetricStatus.ERROR, error_code="judge_http_error")
    data = completion.data if isinstance(completion, JudgementCompletion) else completion
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed(), status=MetricStatus.ERROR, error_code="judge_schema_error")
    claims_payload: list[dict] = []
    for item in data["claims"]:
        if not isinstance(item, dict) or not isinstance(item.get("claim"), str) or not isinstance(item.get("supported"), bool):
            return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed(), status=MetricStatus.ERROR, error_code="judge_schema_error")
        claims_payload.append({"claim": item["claim"].strip(), "supported": item["supported"], "evidence": str(item.get("evidence", ""))})
    if not claims_payload:
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed(), status=MetricStatus.ERROR, error_code="judge_schema_error")
    supported = sum(1 for item in claims_payload if item["supported"])
    return FaithfulnessResult(
        score=supported / len(claims_payload),
        claims=claims_payload,
        elapsed_ms=elapsed(),
        token_usage=model_usage_to_dict(completion.usage) if isinstance(completion, JudgementCompletion) else None,
    )
