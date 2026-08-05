from collections.abc import Sequence
from typing import Protocol

from app.rag.conversation.history import format_recent_messages, trim_conversation_summary, trim_recent_messages
from app.schemas.chat import ChatHistoryMessage


class ConversationLLMProtocol(Protocol):
    # 使用现有 LLM generate 接口完成对话辅助任务。
    def generate(self, question: str, contexts: list[str]) -> str:
        ...


REWRITE_PROMPT = """你需要把用户当前问题改写成一个独立、完整的 KF 产品使用问题。
只输出改写后的问题，不要解释。
如果当前问题已经完整，保持原意并直接输出。"""

FOLLOW_UP_TERMS = (
    "那",
    "这个",
    "这些",
    "它",
    "他们",
    "上面",
    "前面",
    "刚才",
    "继续",
    "然后",
    "里面",
    "其中",
    "这里",
    "那里",
    "当前",
    "该页面",
    "这个页面",
    "该模块",
    "这个模块",
    "上述",
    "前述",
    "创建完成后",
    "下一步",
)


# 判断当前问题是否像追问，只有追问才需要额外调用模型改写。
def should_rewrite_standalone_question(
    question: str,
    conversation_summary: str = "",
    recent_messages: Sequence[ChatHistoryMessage] | None = None,
    enabled: bool = True,
) -> bool:
    if not enabled:
        return False

    summary = trim_conversation_summary(conversation_summary)
    messages = trim_recent_messages(recent_messages or [])
    if not summary and not messages:
        return False

    normalized = question.strip()
    if not normalized:
        return False

    if any(term in normalized for term in FOLLOW_UP_TERMS):
        return True
    return len(normalized) <= 6


# 根据会话摘要和最近消息，把追问改写成可独立检索的问题。
def rewrite_standalone_question(
    llm: ConversationLLMProtocol,
    question: str,
    conversation_summary: str = "",
    recent_messages: Sequence[ChatHistoryMessage] | None = None,
    enabled: bool = True,
) -> str:
    if not should_rewrite_standalone_question(
        question=question,
        conversation_summary=conversation_summary,
        recent_messages=recent_messages,
        enabled=enabled,
    ):
        return question

    summary = trim_conversation_summary(conversation_summary)
    messages = trim_recent_messages(recent_messages or [])

    context = (
        f"{REWRITE_PROMPT}\n\n"
        f"会话摘要：{summary or '无'}\n\n"
        f"最近对话：\n{format_recent_messages(messages) or '无'}"
    )
    try:
        rewritten = llm.generate(question=question, contexts=[context]).strip()
    except Exception:
        return question
    return rewritten or question
