from app.rag.chain import RagChain
from app.rag.models import DocumentChunk
from app.rag.retrieval.retriever import RetrievedChunk
from app.schemas.chat import ChatHistoryMessage


class FakeRetriever:
    def retrieve(self, query: str):
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="doc::0",
                    title="页面编辑器/简介",
                    source_path="页面编辑器/简介.md",
                    content="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                    images=["页面编辑器/1.png"],
                ),
                score=0.9,
            )
        ]


class FakeDuplicateSourceRetriever:
    def retrieve(self, query: str):
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="doc::0",
                    title="采集工程",
                    source_path="数采管理/工程开发-Windows.md",
                    content="第一段：点击新建工程。",
                    images=["数采管理/1.png"],
                ),
                score=0.9,
            ),
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="doc::1",
                    title="采集工程",
                    source_path="数采管理/工程开发-Windows.md",
                    content="第二段：填写名称。",
                    images=["数采管理/1.png", "数采管理/2.png"],
                ),
                score=0.8,
            ),
        ]


class FakeManyImagesRetriever:
    def retrieve(self, query: str):
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="doc::0",
                    title="教程",
                    source_path="教程/采集.md",
                    content="采集工程截图很多。",
                    images=[f"教程/{index}.png" for index in range(1, 9)],
                ),
                score=0.9,
            )
        ]


class FakeMultipleImageSourcesRetriever:
    def retrieve(self, query: str):
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="doc::0",
                    title="来源一",
                    source_path="来源一.md",
                    content="第一份资料。",
                    images=["来源一/1.png", "来源一/2.png", "来源一/3.png"],
                ),
                score=0.9,
            ),
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="doc::1",
                    title="来源二",
                    source_path="来源二.md",
                    content="第二份资料。",
                    images=["来源二/1.png", "来源二/2.png", "来源二/3.png"],
                ),
                score=0.8,
            ),
        ]


class FakeLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        assert "页面编辑器包括菜单栏" in contexts[0]
        return "页面编辑器主要包括菜单栏、工具栏、工具箱和配置窗。"


class FakeContextCountingLLM:
    def __init__(self) -> None:
        self.contexts: list[str] = []

    def generate(self, question: str, contexts: list[str]) -> str:
        self.contexts = contexts
        return "创建采集工程时，点击新建工程并填写名称。"


class FakeNoAnswerLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        return "手册中没有找到相关说明。"


class FakeCitedLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        return "页面编辑器主要包括菜单栏、工具栏、工具箱和配置窗。[资料 1]"


# 模拟模型输出无空格资料编号的情况。
class FakeCompactCitedLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        return "页面编辑器主要包括菜单栏、工具栏、工具箱和配置窗。[资料1]"


class CountingLLM:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, question: str, contexts: list[str]) -> str:
        self.calls += 1
        return "这里是模型回答。"


class RecordingRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def retrieve(self, query: str):
        self.queries.append(query)
        return FakeRetriever().retrieve(query)


class ConversationAwareLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def generate(self, question: str, contexts: list[str]) -> str:
        self.calls.append((question, contexts))
        if "改写成一个独立" in contexts[0]:
            return "采集工程创建完成后如何运行？"
        if "请更新 KF 产品问答会话摘要" in contexts[0]:
            return "用户正在了解采集工程创建和运行。"
        return "创建完成后，发布并启动采集工程。[资料 1]"


class RecordingConversationLLM:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate(self, question: str, contexts: list[str]) -> str:
        context = contexts[0]
        if "改写成一个独立" in context:
            self.calls.append("rewrite")
            return "采集工程创建完成后如何运行？"
        if "请更新 KF 产品问答会话摘要" in context:
            self.calls.append("summary")
            return "用户正在了解采集工程创建和运行。"
        self.calls.append("answer")
        return "创建完成后，发布并启动采集工程。[资料 1]"


def test_rag_chain_returns_answer_sources_and_images():
    chain = RagChain(retriever=FakeRetriever(), llm=FakeLLM())

    response = chain.answer("页面编辑器有哪些区域？")

    assert "菜单栏" in response.answer
    assert "参考：[资料 1]" in response.answer
    assert response.sources[0].source_path == "页面编辑器/简介.md"
    assert response.sources[0].evidence_ids == ["资料 1"]
    assert response.sources[0].images == ["页面编辑器/1.png"]


def test_rag_chain_does_not_duplicate_existing_citations():
    chain = RagChain(retriever=FakeRetriever(), llm=FakeCitedLLM())

    response = chain.answer("页面编辑器有哪些区域？")

    assert response.answer == "页面编辑器主要包括菜单栏、工具栏、工具箱和配置窗。[资料 1]"


# 验证模型输出“[资料1]”时不会被误判成缺少引用。
def test_rag_chain_accepts_compact_existing_citations():
    chain = RagChain(retriever=FakeRetriever(), llm=FakeCompactCitedLLM())

    response = chain.answer("页面编辑器有哪些区域？")

    assert response.answer == "页面编辑器主要包括菜单栏、工具栏、工具箱和配置窗。[资料1]"


def test_rag_chain_hides_sources_when_model_refuses_to_answer():
    chain = RagChain(retriever=FakeRetriever(), llm=FakeNoAnswerLLM())

    response = chain.answer("手册里有没有微信登录说明？")

    assert response.answer == "手册中没有找到相关说明。"
    assert response.sources == []


def test_rag_chain_refuses_when_required_query_term_is_missing_from_context():
    llm = CountingLLM()
    chain = RagChain(retriever=FakeRetriever(), llm=llm)

    response = chain.answer("手册里有没有微信登录说明？")

    assert response.answer == "手册中没有找到相关说明。"
    assert response.sources == []
    assert llm.calls == 0


def test_rag_chain_deduplicates_sources_without_dropping_llm_contexts():
    llm = FakeContextCountingLLM()
    chain = RagChain(retriever=FakeDuplicateSourceRetriever(), llm=llm)

    response = chain.answer("如何创建采集工程？")

    assert llm.contexts == [
        "[资料 1]\n标题：采集工程\n来源：数采管理/工程开发-Windows.md\n相关分数：0.90\n相关图片：数采管理/1.png\n内容：\n第一段：点击新建工程。",
        "[资料 2]\n标题：采集工程\n来源：数采管理/工程开发-Windows.md\n相关分数：0.80\n相关图片：数采管理/1.png, 数采管理/2.png\n内容：\n第二段：填写名称。",
    ]
    assert len(response.sources) == 1
    assert response.sources[0].source_path == "数采管理/工程开发-Windows.md"
    assert response.sources[0].evidence_ids == ["资料 1", "资料 2"]
    assert response.sources[0].images == ["数采管理/1.png", "数采管理/2.png"]


def test_rag_chain_limits_images_per_source():
    chain = RagChain(retriever=FakeManyImagesRetriever(), llm=FakeContextCountingLLM(), max_images_per_source=5)

    response = chain.answer("如何创建采集工程？")

    assert response.sources[0].images == ["教程/1.png", "教程/2.png", "教程/3.png", "教程/4.png", "教程/5.png"]


def test_rag_chain_limits_total_images_per_answer_without_dropping_sources():
    chain = RagChain(
        retriever=FakeMultipleImageSourcesRetriever(),
        llm=FakeContextCountingLLM(),
        max_images_per_source=2,
        max_images_per_answer=3,
    )

    response = chain.answer("如何查看资料图片？")

    assert [source.source_path for source in response.sources] == ["来源一.md", "来源二.md"]
    assert response.sources[0].images == ["来源一/1.png", "来源一/2.png"]
    assert response.sources[1].images == ["来源二/1.png"]


def test_rag_chain_rewrites_contextual_question_before_retrieval():
    retriever = RecordingRetriever()
    llm = ConversationAwareLLM()
    chain = RagChain(retriever=retriever, llm=llm)

    response = chain.answer(
        "那创建完成后怎么运行？",
        conversation_summary="用户正在了解采集工程创建流程。",
        conversation_turn_count=3,
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
    )

    assert retriever.queries == ["采集工程创建完成后如何运行？"]
    assert response.standalone_question == "采集工程创建完成后如何运行？"
    assert response.conversation_summary == "用户正在了解采集工程创建和运行。"
    assert "发布并启动采集工程" in response.answer


def test_rag_chain_skips_rewrite_for_complete_question_with_history():
    retriever = RecordingRetriever()
    llm = RecordingConversationLLM()
    chain = RagChain(retriever=retriever, llm=llm)

    response = chain.answer(
        "如何创建采集工程？",
        conversation_summary="用户正在了解采集工程创建流程。",
        recent_messages=[ChatHistoryMessage(role="user", content="页面编辑器有哪些区域？")],
    )

    assert retriever.queries == ["如何创建采集工程？"]
    assert response.standalone_question == "如何创建采集工程？"
    assert "rewrite" not in llm.calls


def test_rag_chain_can_disable_conversation_rewrite():
    retriever = RecordingRetriever()
    llm = RecordingConversationLLM()
    chain = RagChain(retriever=retriever, llm=llm, enable_conversation_rewrite=False)

    response = chain.answer(
        "那创建完成后怎么运行？",
        conversation_summary="用户正在了解采集工程创建流程。",
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
    )

    assert retriever.queries == ["那创建完成后怎么运行？"]
    assert response.standalone_question == "那创建完成后怎么运行？"
    assert "rewrite" not in llm.calls


def test_rag_chain_updates_summary_on_configured_turn_interval():
    llm = RecordingConversationLLM()
    chain = RagChain(
        retriever=RecordingRetriever(),
        llm=llm,
        conversation_summary_every_n_turns=3,
    )

    response = chain.answer(
        "那怎么运行？",
        conversation_summary="旧摘要",
        conversation_turn_count=3,
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
    )

    assert "summary" in llm.calls
    assert response.conversation_summary == "用户正在了解采集工程创建和运行。"


def test_rag_chain_reuses_summary_between_configured_turn_intervals():
    llm = RecordingConversationLLM()
    chain = RagChain(
        retriever=RecordingRetriever(),
        llm=llm,
        conversation_summary_every_n_turns=3,
    )

    response = chain.answer(
        "那怎么运行？",
        conversation_summary="旧摘要",
        conversation_turn_count=2,
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
    )

    assert "summary" not in llm.calls
    assert response.conversation_summary == "旧摘要"


def test_rag_chain_creates_summary_when_current_summary_is_empty():
    llm = RecordingConversationLLM()
    chain = RagChain(
        retriever=RecordingRetriever(),
        llm=llm,
        conversation_summary_every_n_turns=3,
    )

    response = chain.answer(
        "那怎么运行？",
        conversation_summary="",
        conversation_turn_count=2,
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
    )

    assert "summary" in llm.calls
    assert response.conversation_summary == "用户正在了解采集工程创建和运行。"


def test_rag_chain_can_disable_conversation_summary():
    llm = RecordingConversationLLM()
    chain = RagChain(retriever=RecordingRetriever(), llm=llm, enable_conversation_summary=False)

    response = chain.answer(
        "那怎么运行？",
        conversation_summary="旧摘要",
        conversation_turn_count=3,
        recent_messages=[ChatHistoryMessage(role="user", content="如何创建采集工程？")],
    )

    assert "summary" not in llm.calls
    assert response.conversation_summary == "旧摘要"


def test_rag_chain_keeps_single_turn_behavior_without_history():
    retriever = RecordingRetriever()
    llm = FakeCitedLLM()
    chain = RagChain(retriever=retriever, llm=llm)

    response = chain.answer("页面编辑器有哪些区域？")

    assert retriever.queries == ["页面编辑器有哪些区域？"]
    assert response.standalone_question == "页面编辑器有哪些区域？"
    assert response.conversation_summary == ""
