from collections.abc import Sequence

from app.rag.conversation.history import format_recent_messages, trim_conversation_summary, trim_recent_messages
from app.rag.conversation.rewriter import ConversationLLMProtocol
from app.schemas.chat import ChatHistoryMessage


SUMMARY_PROMPT = """请更新 KF 产品问答会话摘要。
要求：
1. 只保留和产品使用问题相关的信息。
2. 保留用户正在询问的模块、对象、流程和已确认结论。
3. 不要记录无关闲聊。
4. 控制在 500 字以内。
只输出更新后的摘要。"""


# 根据旧摘要、最近消息和本轮问答，生成下一轮可复用的会话摘要。
def summarize_conversation(
    llm: ConversationLLMProtocol,
    previous_summary: str,
    recent_messages: Sequence[ChatHistoryMessage],
    question: str,
    answer: str,
) -> str:
    summary = trim_conversation_summary(previous_summary)
    messages = trim_recent_messages(recent_messages)
    context = (
        f"{SUMMARY_PROMPT}\n\n"
        f"旧摘要：{summary or '无'}\n\n"
        f"最近对话：\n{format_recent_messages(messages) or '无'}\n\n"
        f"本轮问题：{question}\n\n"
        f"本轮回答：{answer}"
    )
    try:
        updated = llm.generate(question="请更新会话摘要。", contexts=[context]).strip()
    except Exception:
        return summary
    return trim_conversation_summary(updated or summary)
