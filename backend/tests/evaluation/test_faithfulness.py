from app.evaluation.faithfulness import (
    ClaimJudgement,
    FaithfulnessResult,
    compute_faithfulness,
    judge_claim_support,
    split_claims,
)
from app.evaluation.judge import JudgementCompletion, JudgementError
from app.evaluation.models import MetricStatus


class FakeJudge:
    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        if self.responses.get("raise"):
            raise JudgementError()
        if "逐条判断" in system_prompt:
            return JudgementCompletion(self.responses)
        if "拆分" in user_prompt or "声明" in system_prompt and "拆" in system_prompt:
            return JudgementCompletion(self.responses.get("split", {"claims": []}))
        return JudgementCompletion(self.responses["support"].pop(0))


def test_split_claims_returns_claim_list():
    judge = FakeJudge({"split": {"claims": ["按钮 A 可配置颜色", "按钮 B 不存在"]}})
    claims = split_claims(judge, "回答内容")
    assert claims == ["按钮 A 可配置颜色", "按钮 B 不存在"]
    assert judge.calls[0][0].startswith("你是 RAG 回答忠实度评估助手")


def test_judge_claim_support_parses_verdict():
    judge = FakeJudge({"support": [{"supported": False, "evidence": ""}]})
    judgement = judge_claim_support(judge, "按钮 B 不存在", ["手册片段"])
    assert judgement == ClaimJudgement(claim="按钮 B 不存在", supported=False, evidence="")


def test_judge_claim_support_coerces_string_supported_flags():
    judge = FakeJudge({"support": [{"supported": "false", "evidence": ""}]})
    judgement = judge_claim_support(judge, "编造的声明", ["手册片段"])
    assert judgement == ClaimJudgement(claim="编造的声明", supported=False, evidence="")

    judge = FakeJudge({"support": [{"supported": "true", "evidence": "依据"}]})
    judgement = judge_claim_support(judge, "有依据的声明", ["手册片段"])
    assert judgement == ClaimJudgement(claim="有依据的声明", supported=True, evidence="依据")


def test_compute_faithfulness_scores_supported_ratio():
    judge = FakeJudge({
        "claims": [
            {"claim": "工程需要名称", "supported": True, "evidence": "填写名称"},
            {"claim": "工程自动运行", "supported": False, "evidence": ""},
        ],
    })
    result = compute_faithfulness(judge, "回答", ["上下文"])
    assert isinstance(result, FaithfulnessResult)
    assert result.score == 0.5
    assert len(judge.calls) == 1
    assert result.claims[1] == {"claim": "工程自动运行", "supported": False, "evidence": ""}


def test_compute_faithfulness_returns_error_for_missing_supported_boolean():
    judge = FakeJudge({"claims": [{"claim": "工程需要名称", "evidence": "填写名称"}]})

    result = compute_faithfulness(judge, "回答", ["上下文"])

    assert result.status == MetricStatus.ERROR
    assert result.error_code == "judge_schema_error"


def test_compute_faithfulness_returns_none_for_no_answer():
    judge = FakeJudge({})
    result = compute_faithfulness(judge, "手册中没有找到相关说明。", ["上下文"])
    assert result.score is None
    assert result.claims == []


def test_compute_faithfulness_returns_none_for_empty_answer():
    judge = FakeJudge({})
    result = compute_faithfulness(judge, "", ["上下文"])
    assert result.score is None
    assert result.claims == []


def test_compute_faithfulness_returns_error_for_empty_contexts():
    judge = FakeJudge({})
    result = compute_faithfulness(judge, "回答内容", [])
    assert result.status == MetricStatus.ERROR
    assert result.claims == []

def test_compute_faithfulness_returns_error_when_batch_returns_empty_claims():
    judge = FakeJudge({"claims": []})
    result = compute_faithfulness(judge, "回答内容", ["上下文"])
    assert result.status == MetricStatus.ERROR
    assert result.claims == []


def test_compute_faithfulness_returns_none_on_judge_failure():
    judge = FakeJudge({"raise": True})
    result = compute_faithfulness(judge, "回答内容", ["上下文"])
    assert result.status == MetricStatus.ERROR
    assert result.claims == []
