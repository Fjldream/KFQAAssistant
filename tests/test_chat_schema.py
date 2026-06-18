from app.schemas.chat import ChatRequest, ChatResponse, SourceSnippet


def test_chat_request_strips_question():
    request = ChatRequest(question="  页面编辑器是什么？  ")
    assert request.question == "页面编辑器是什么？"


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
