from pathlib import Path

from app.rag.index_service import update_index
from app.rag.models import DocumentChunk


# 模拟向量库的增量与全量操作，并保留当前 chunk 状态供断言。
class FakeVectorStore:
    # 初始化测试向量和每种写入操作的调用记录。
    def __init__(self, initial_count: int = 0):
        self.chunks = {
            f"legacy::{index}": DocumentChunk(
                id=f"legacy::{index}",
                title="legacy",
                source_path="legacy.md",
                content="旧索引",
            )
            for index in range(initial_count)
        }
        self.rebuild_calls: list[list[DocumentChunk]] = []
        self.add_calls: list[list[DocumentChunk]] = []
        self.delete_calls: list[list[str]] = []

    # 模拟清空 collection 后写入全部 chunks。
    def rebuild(self, chunks: list[DocumentChunk]) -> int:
        self.rebuild_calls.append(chunks)
        self.chunks = {chunk.id: chunk for chunk in chunks}
        return len(chunks)

    # 模拟只写入新增或修改文档的 chunks。
    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        self.add_calls.append(chunks)
        self.chunks.update({chunk.id: chunk for chunk in chunks})
        return len(chunks)

    # 模拟按 source_path 删除旧 chunks。
    def delete_sources(self, source_paths: list[str]) -> int:
        self.delete_calls.append(source_paths)
        matched_ids = [
            chunk_id for chunk_id, chunk in self.chunks.items() if chunk.source_path in source_paths
        ]
        for chunk_id in matched_ids:
            del self.chunks[chunk_id]
        return len(matched_ids)

    # 返回 FakeVectorStore 当前保存的 chunk 数量。
    def count(self) -> int:
        return len(self.chunks)

    # 只清空调用记录，保留向量状态来模拟下一次构建。
    def reset_events(self) -> None:
        self.rebuild_calls.clear()
        self.add_calls.clear()
        self.delete_calls.clear()


# 创建测试数据目录及默认 manifest 路径。
def make_paths(tmp_path: Path) -> tuple[Path, Path]:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir, tmp_path / "processed" / "index_manifest.json"


# 验证首次构建把全部手册视为新增，但不必调用全量 reset。
def test_first_build_adds_all_documents_incrementally(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()

    result = update_index(data_dir, manifest_path, store)

    assert result.mode == "incremental"
    assert result.added_documents == 1
    assert result.written_chunks == 1
    assert len(store.add_calls) == 1
    assert store.rebuild_calls == []
    assert manifest_path.exists()


# 验证第二次无变化构建完全跳过 embedding 写入。
def test_unchanged_documents_skip_vector_writes(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()

    result = update_index(data_dir, manifest_path, store)

    assert result.skipped_documents == 1
    assert result.written_chunks == 0
    assert store.add_calls == []
    assert store.delete_calls == []


# 验证新增文档只写入新来源，不重复处理旧来源。
def test_added_document_only_writes_new_source(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "first.md").write_text("# 第一篇", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()
    (data_dir / "second.md").write_text("# 第二篇", encoding="utf-8")

    result = update_index(data_dir, manifest_path, store)

    assert result.added_documents == 1
    assert result.skipped_documents == 1
    assert {chunk.source_path for chunk in store.add_calls[0]} == {"second.md"}


# 验证修改只删除和重写变化来源。
def test_modified_document_replaces_only_its_chunks(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    path = data_dir / "guide.md"
    path.write_text("# 第一版", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()
    path.write_text("# 第二版", encoding="utf-8")

    result = update_index(data_dir, manifest_path, store)

    assert result.modified_documents == 1
    assert store.delete_calls == [["guide.md"]]
    assert len(store.add_calls) == 1
    assert {chunk.source_path for chunk in store.add_calls[0]} == {"guide.md"}


# 验证删除源文件会删除对应来源向量。
def test_deleted_document_removes_its_chunks(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    path = data_dir / "guide.md"
    path.write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()
    path.unlink()

    result = update_index(data_dir, manifest_path, store)

    assert result.deleted_documents == 1
    assert result.total_chunks == 0
    assert store.delete_calls == [["guide.md"]]
    assert store.add_calls == []


# 验证已有向量但没有清单时会执行一次迁移全量构建。
def test_existing_index_without_manifest_runs_full_baseline(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore(initial_count=3)

    result = update_index(data_dir, manifest_path, store)

    assert result.mode == "full"
    assert len(store.rebuild_calls) == 1
    assert store.add_calls == []


# 验证 full=True 始终走完整重建。
def test_full_rebuild_ignores_existing_manifest(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()

    result = update_index(data_dir, manifest_path, store, full=True)

    assert result.mode == "full"
    assert len(store.rebuild_calls) == 1
    assert store.add_calls == []


# 验证显式全量重建可以绕过损坏的旧清单并生成新清单。
def test_full_rebuild_recovers_corrupted_manifest(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text("{bad json", encoding="utf-8")
    store = FakeVectorStore()

    result = update_index(data_dir, manifest_path, store, full=True)

    assert result.mode == "full"
    assert len(store.rebuild_calls) == 1
    assert '"version": 1' in manifest_path.read_text(encoding="utf-8")
