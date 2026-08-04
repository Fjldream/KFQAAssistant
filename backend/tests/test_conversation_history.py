from app.rag.conversation.history import format_recent_messages, trim_conversation_summary, trim_recent_messages
from app.schemas.chat import ChatHistoryMessage


def test_trim_conversation_summary_strips_and_limits_text():
    summary = "  " + "采集工程" * 500

    trimmed = trim_conversation_summary(summary, max_chars=20)

    assert trimmed == ("采集工程" * 500).strip()[:20]


def test_trim_recent_messages_keeps_latest_messages_and_limits_content():
    messages = [ChatHistoryMessage(role="user", content=f"问题{index}" + "x" * 20) for index in range(10)]

    trimmed = trim_recent_messages(messages, max_messages=3, max_content_chars=4)

    assert [message.content for message in trimmed] == ["问题7x", "问题8x", "问题9x"]


def test_format_recent_messages_uses_chinese_roles():
    messages = [
        ChatHistoryMessage(role="user", content="如何创建采集工程？"),
        ChatHistoryMessage(role="assistant", content="点击新建工程。"),
    ]

    formatted = format_recent_messages(messages)

    assert formatted == "用户：如何创建采集工程？\n助手：点击新建工程。"
