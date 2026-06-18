from app.rag.chain import RagChain
from app.rag.models import DocumentChunk
from app.rag.retriever import RetrievedChunk


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


class CountingLLM:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, question: str, contexts: list[str]) -> str:
        self.calls += 1
        return "这里是模型回答。"


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
        "[资料 1]\n标题：采集工程\n来源：数采管理/工程开发-Windows.md\n内容：\n第一段：点击新建工程。",
        "[资料 2]\n标题：采集工程\n来源：数采管理/工程开发-Windows.md\n内容：\n第二段：填写名称。",
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
