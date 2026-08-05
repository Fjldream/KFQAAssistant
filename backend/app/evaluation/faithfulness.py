# backend/app/evaluation/faithfulness.py
from dataclasses import dataclass, field
from time import perf_counter

from app.evaluation.judge import JudgementError, JudgeProtocol
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


def split_claims(judge: JudgeProtocol, answer: str) -> list[str]:
    data = judge.complete_json(SPLIT_SYSTEM_PROMPT, f"回答：\n{answer}")
    claims = data.get("claims", [])
    return [str(claim).strip() for claim in claims if str(claim).strip()]


def judge_claim_support(judge: JudgeProtocol, claim: str, contexts: list[str]) -> ClaimJudgement:
    context_text = "\n\n---\n\n".join(contexts)
    data = judge.complete_json(
        SUPPORT_SYSTEM_PROMPT,
        f"声明：{claim}\n\n手册片段：\n{context_text}",
    )
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
    if not answer.strip() or is_no_answer(answer) or not contexts:
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed())
    try:
        claims = split_claims(judge, answer)
    except JudgementError:
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed())
    if not claims:
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed())

    judgements: list[ClaimJudgement] = []
    for claim in claims:
        try:
            judgements.append(judge_claim_support(judge, claim, contexts))
        except JudgementError:
            continue  # 单条判定失败跳过，不计入分母

    if not judgements:
        return FaithfulnessResult(score=None, claims=[], elapsed_ms=elapsed())
    supported = sum(1 for item in judgements if item.supported)
    claims_payload = [
        {"claim": item.claim, "supported": item.supported, "evidence": item.evidence}
        for item in judgements
    ]
    return FaithfulnessResult(score=supported / len(judgements), claims=claims_payload, elapsed_ms=elapsed())
