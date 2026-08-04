from collections.abc import Sequence

from app.schemas.chat import ChatHistoryMessage


# 裁剪会话摘要，避免摘要无限增长占用模型上下文。
def trim_conversation_summary(summary: str, max_chars: int = 2000) -> str:
    return summary.strip()[:max_chars]


# 裁剪最近消息，只保留最新几条并限制单条长度。
def trim_recent_messages(
    messages: Sequence[ChatHistoryMessage],
    max_messages: int = 8,
    max_content_chars: int = 1200,
) -> list[ChatHistoryMessage]:
    latest = list(messages)[-max_messages:]
    return [
        ChatHistoryMessage(role=message.role, content=message.content.strip()[:max_content_chars])
        for message in latest
        if message.content.strip()
    ]


# 将最近消息格式化成大模型容易理解的中文对话记录。
def format_recent_messages(messages: Sequence[ChatHistoryMessage]) -> str:
    role_names = {"user": "用户", "assistant": "助手"}
    return "\n".join(f"{role_names[message.role]}：{message.content}" for message in messages)
