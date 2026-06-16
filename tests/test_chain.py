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


class FakeLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        assert "页面编辑器包括菜单栏" in contexts[0]
        return "页面编辑器主要包括菜单栏、工具栏、工具箱和配置窗。"


class FakeNoAnswerLLM:
    def generate(self, question: str, contexts: list[str]) -> str:
        return "手册中没有找到相关说明。"


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
    assert response.sources[0].source_path == "页面编辑器/简介.md"
    assert response.sources[0].images == ["页面编辑器/1.png"]


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
