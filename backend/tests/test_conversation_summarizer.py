from app.rag.conversation.summarizer import summarize_conversation
from app.schemas.chat import ChatHistoryMessage


class FakeSummaryLLM:
    def __init__(self, output: str) -> None:
        self.output = output
        self.question = ""
        self.contexts: list[str] = []

    def generate(self, question: str, contexts: list[str]) -> str:
        self.question = question
        self.contexts = contexts
        return self.output


class FailingSummaryLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        raise RuntimeError("summary failed")


def test_summarize_conversation_returns_trimmed_new_summary():
    llm = FakeSummaryLLM(" 用户正在了解采集工程创建和运行。 ")

    summary = summarize_conversation(
        llm=llm,
        previous_summary="用户之前询问采集工程。",
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
        question="那怎么运行？",
        answer="发布后启动工程。",
    )

    assert summary == "用户正在了解采集工程创建和运行。"
    assert "用户之前询问采集工程。" in llm.contexts[0]
    assert "本轮问题：那怎么运行？" in llm.contexts[0]
    assert "本轮回答：发布后启动工程。" in llm.contexts[0]


def test_summarize_conversation_falls_back_to_previous_summary_on_failure():
    summary = summarize_conversation(
        llm=FailingSummaryLLM(),
        previous_summary="旧摘要",
        recent_messages=[],
        question="问题",
        answer="回答",
    )

    assert summary == "旧摘要"
