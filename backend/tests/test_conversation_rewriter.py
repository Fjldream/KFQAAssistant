from app.rag.conversation.rewriter import rewrite_standalone_question
from app.schemas.chat import ChatHistoryMessage


class FakeRewriteLLM:
    def __init__(self, output: str) -> None:
        self.output = output
        self.question = ""
        self.contexts: list[str] = []

    def generate(self, question: str, contexts: list[str]) -> str:
        self.question = question
        self.contexts = contexts
        return self.output


class FailingRewriteLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        raise RuntimeError("llm failed")


def test_rewrite_standalone_question_uses_summary_and_recent_messages():
    llm = FakeRewriteLLM("采集工程创建完成后如何运行？")

    rewritten = rewrite_standalone_question(
        llm=llm,
        question="那创建完成后怎么运行？",
        conversation_summary="用户正在了解采集工程创建流程。",
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
    )

    assert rewritten == "采集工程创建完成后如何运行？"
    assert "用户正在了解采集工程创建流程。" in llm.contexts[0]
    assert "用户：如何创建采集工程？" in llm.contexts[0]


def test_rewrite_standalone_question_returns_original_without_context():
    llm = FakeRewriteLLM("不应该调用")

    rewritten = rewrite_standalone_question(llm=llm, question="如何创建采集工程？")

    assert rewritten == "如何创建采集工程？"
    assert llm.question == ""


def test_rewrite_standalone_question_falls_back_to_original_on_failure():
    rewritten = rewrite_standalone_question(
        llm=FailingRewriteLLM(),
        question="那怎么运行？",
        conversation_summary="用户正在了解采集工程。",
    )

    assert rewritten == "那怎么运行？"
