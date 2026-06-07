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


def test_rag_chain_returns_answer_sources_and_images():
    chain = RagChain(retriever=FakeRetriever(), llm=FakeLLM())

    response = chain.answer("页面编辑器有哪些区域？")

    assert "菜单栏" in response.answer
    assert response.sources[0].source_path == "页面编辑器/简介.md"
    assert response.sources[0].images == ["页面编辑器/1.png"]
