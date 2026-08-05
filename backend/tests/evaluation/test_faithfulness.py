from app.evaluation.faithfulness import (
    ClaimJudgement,
    FaithfulnessResult,
    compute_faithfulness,
    judge_claim_support,
    split_claims,
)
from app.evaluation.judge import JudgementError


class FakeJudge:
    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        if self.responses.get("raise"):
            raise JudgementError()
        if "拆分" in user_prompt or "声明" in system_prompt and "拆" in system_prompt:
            return self.responses.get("split", {"claims": []})
        return self.responses["support"].pop(0)


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
        "split": {"claims": ["句1", "句2", "句3"]},
        "support": [
            {"supported": True, "evidence": "依据一"},
            {"supported": False, "evidence": ""},
            {"supported": True, "evidence": "依据二"},
        ],
    })
    result = compute_faithfulness(judge, "回答", ["上下文"])
    assert isinstance(result, FaithfulnessResult)
    assert result.score == 2 / 3
    assert len(result.claims) == 3
    assert result.claims[1] == {"claim": "句2", "supported": False, "evidence": ""}


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


def test_compute_faithfulness_returns_none_for_empty_contexts():
    judge = FakeJudge({})
    result = compute_faithfulness(judge, "回答内容", [])
    assert result.score is None
    assert result.claims == []


def test_compute_faithfulness_returns_none_when_split_returns_empty_claims():
    judge = FakeJudge({"split": {"claims": []}})
    result = compute_faithfulness(judge, "回答内容", ["上下文"])
    assert result.score is None
    assert result.claims == []


def test_compute_faithfulness_returns_none_when_all_judgements_fail():
    class AllSupportFailJudge(FakeJudge):
        def complete_json(self, system_prompt, user_prompt):
            if "判" in system_prompt:
                raise JudgementError()
            return super().complete_json(system_prompt, user_prompt)

    judge = AllSupportFailJudge({
        "split": {"claims": ["句1", "句2"]},
        "support": [{"supported": True, "evidence": "依据"}],
    })
    result = compute_faithfulness(judge, "回答内容", ["上下文"])
    assert result.score is None
    assert result.claims == []


def test_compute_faithfulness_returns_none_on_judge_failure():
    judge = FakeJudge({"raise": True})
    result = compute_faithfulness(judge, "回答内容", ["上下文"])
    assert result.score is None
    assert result.claims == []


def test_compute_faithfulness_skips_claim_on_single_failure():
    judge = FakeJudge({
        "split": {"claims": ["句1", "句2"]},
        "support": [{"supported": True, "evidence": "依据"}],
    })

    class FlakyJudge(FakeJudge):
        def complete_json(self, system_prompt, user_prompt):
            if "判" in system_prompt and len(self.calls) % 2 == 0:
                raise JudgementError()
            return super().complete_json(system_prompt, user_prompt)

    flaky = FlakyJudge({"split": {"claims": ["句1", "句2"]}, "support": [{"supported": True, "evidence": "依据"}]})
    result = compute_faithfulness(flaky, "回答", ["上下文"])
    # 句1 判定失败被跳过，句2 成功 → 1/1
    assert result.score == 1.0
    assert len(result.claims) == 1
