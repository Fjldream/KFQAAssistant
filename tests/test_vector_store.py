from app.rag.models import DocumentChunk
from app.rag.vector_store import ChromaVectorStore


# 提供不调用真实 Chroma 和 embedding 模型的轻量测试替身。
class FakeStore:
    # 初始化测试记录和按来源预置的 chunk IDs。
    def __init__(self, ids_by_source: dict[str, list[str]] | None = None):
        self.ids_by_source = ids_by_source or {}
        self.added_documents = []
        self.added_ids: list[str] = []
        self.deleted_ids: list[str] = []
        self.queries: list[dict[str, str]] = []

    # 记录新增文档及其 ID，模拟 Chroma 的 add_documents。
    def add_documents(self, documents, ids):
        self.added_documents = documents
        self.added_ids = ids

    # 根据 metadata 来源返回已有 IDs，模拟 Chroma 的 get。
    def get(self, where):
        self.queries.append(where)
        return {"ids": self.ids_by_source.get(where["source_path"], [])}

    # 记录被删除的 IDs，模拟 Chroma 的 delete。
    def delete(self, ids):
        self.deleted_ids.extend(ids)


# 创建绕过真实 Chroma 初始化的向量库实例。
def make_vector_store(fake_store: FakeStore) -> ChromaVectorStore:
    vector_store = ChromaVectorStore.__new__(ChromaVectorStore)
    vector_store.store = fake_store
    return vector_store


# 验证 add_chunks 会保留业务 metadata 并返回写入数量。
def test_add_chunks_writes_documents():
    fake_store = FakeStore()
    vector_store = make_vector_store(fake_store)
    chunks = [
        DocumentChunk(
            id="guide.md::0",
            title="guide",
            source_path="guide.md",
            content="正文",
            images=["guide/1.png"],
        )
    ]

    count = vector_store.add_chunks(chunks)

    assert count == 1
    assert fake_store.added_ids == ["guide.md::0"]
    assert fake_store.added_documents[0].page_content == "正文"
    assert fake_store.added_documents[0].metadata["source_path"] == "guide.md"
    assert fake_store.added_documents[0].metadata["images"] == "guide/1.png"


# 验证空 chunk 列表不会调用 Chroma 写入方法。
def test_add_chunks_skips_empty_input():
    fake_store = FakeStore()
    vector_store = make_vector_store(fake_store)

    count = vector_store.add_chunks([])

    assert count == 0
    assert fake_store.added_documents == []
    assert fake_store.added_ids == []


# 验证按 source_path 删除该文档所有已有 chunks。
def test_delete_sources_removes_matching_ids():
    fake_store = FakeStore(
        ids_by_source={
            "guide.md": ["guide.md::0", "guide.md::1"],
            "other.md": ["other.md::0"],
        }
    )
    vector_store = make_vector_store(fake_store)

    count = vector_store.delete_sources(["guide.md"])

    assert count == 2
    assert fake_store.queries == [{"source_path": "guide.md"}]
    assert fake_store.deleted_ids == ["guide.md::0", "guide.md::1"]


# 验证删除不存在的来源保持幂等，不向 Chroma 发送空删除。
def test_delete_sources_ignores_missing_sources():
    fake_store = FakeStore()
    vector_store = make_vector_store(fake_store)

    count = vector_store.delete_sources(["missing.md"])

    assert count == 0
    assert fake_store.deleted_ids == []
