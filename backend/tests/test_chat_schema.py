import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ChatResponse, SourceSnippet


def test_chat_request_strips_question():
    request = ChatRequest(question="  页面编辑器是什么？  ")
    assert request.question == "页面编辑器是什么？"


def test_chat_request_accepts_optional_conversation_context():
    request = ChatRequest(
        question="那怎么运行？",
        conversation_summary="用户正在了解采集工程创建流程。",
        conversation_turn_count=2,
        recent_messages=[
            {"role": "user", "content": "如何创建采集工程？"},
            {"role": "assistant", "content": "进入数采管理后点击新建工程。"},
        ],
    )

    assert request.conversation_summary == "用户正在了解采集工程创建流程。"
    assert request.conversation_turn_count == 2
    assert request.recent_messages[0].role == "user"
    assert request.recent_messages[1].content == "进入数采管理后点击新建工程。"


def test_chat_request_rejects_invalid_history_role():
    with pytest.raises(ValidationError):
        ChatRequest(
            question="那怎么运行？",
            recent_messages=[{"role": "system", "content": "内部提示"}],
        )


def test_chat_response_defaults_conversation_fields_for_old_flow():
    response = ChatResponse(answer="回答", sources=[])

    assert response.conversation_summary == ""
    assert response.standalone_question == ""


def test_chat_response_contains_sources_and_images():
    response = ChatResponse(
        answer="页面编辑器用于编辑页面。",
        sources=[
            SourceSnippet(
                title="页面编辑器/简介",
                source_path="data/help/html/功能模块/页面编辑器/简介/简介.md",
                snippet="页面编辑主要是对页面内容进行编辑。",
                evidence_ids=["资料 1"],
                images=["data/help/html/功能模块/页面编辑器/简介/页面编辑器.png"],
            )
        ],
    )

    assert response.sources[0].evidence_ids == ["资料 1"]
    assert response.sources[0].images[0].endswith("页面编辑器.png")
