import json
from pathlib import Path

import pytest

import app.rag.ingestion.index_service as index_service
from app.rag.ingestion.index_service import update_index
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
        self.fail_rebuild = False

    # 模拟清空 collection 后写入全部 chunks。
    def rebuild(self, chunks: list[DocumentChunk]) -> int:
        self.rebuild_calls.append(chunks)
        if self.fail_rebuild:
            self.chunks.clear()
            raise RuntimeError("模拟全量写入失败")
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
def test_unchanged_documents_skip_vector_writes(tmp_path: Path, monkeypatch):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()

    # 无变化时不应重写 manifest，文件时间才能代表最后一次真实更新。
    def fail_manifest_save(path, manifest):
        raise AssertionError("无变化索引不应保存 manifest")

    monkeypatch.setattr(index_service, "save_manifest", fail_manifest_save)

    result = update_index(data_dir, manifest_path, store)

    assert result.skipped_documents == 1
    assert result.written_chunks == 0
    assert store.add_calls == []
    assert store.delete_calls == []


# 验证 embedding 模型或分块参数变化时自动执行全量重建。
@pytest.mark.parametrize(
    "changed_options",
    [
        {"embedding_model_name": "new-embedding-model"},
        {"chunk_size": 350},
        {"chunk_overlap": 50},
        {"pipeline_version": 2},
    ],
)
def test_index_configuration_change_forces_full_rebuild(tmp_path: Path, changed_options: dict):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()

    result = update_index(data_dir, manifest_path, store, **changed_options)

    assert result.mode == "full"
    assert len(store.rebuild_calls) == 1
    assert store.add_calls == []


# 验证旧 manifest 缺少配置指纹时自动执行一次全量升级。
def test_legacy_manifest_without_signature_forces_full_upgrade(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload.pop("index_signature")
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    store.reset_events()

    result = update_index(data_dir, manifest_path, store)

    assert result.mode == "full"
    assert len(store.rebuild_calls) == 1
    upgraded = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert upgraded["index_signature"]


# 验证非法分块参数会在任何向量操作前被拒绝。
@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [(0, 0), (700, -1), (700, 700), (700, 800)],
)
def test_invalid_chunk_settings_do_not_touch_index(
    tmp_path: Path,
    chunk_size: int,
    chunk_overlap: int,
):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore(initial_count=1)

    with pytest.raises(ValueError, match="chunk_"):
        update_index(
            data_dir,
            manifest_path,
            store,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    assert store.count() == 1
    assert store.rebuild_calls == []
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
    (data_dir / "keep.md").write_text("# 保留文档", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.reset_events()
    path.unlink()

    result = update_index(data_dir, manifest_path, store)

    assert result.deleted_documents == 1
    assert result.total_chunks == 1
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


# 验证全量写入失败后会留下恢复标记，使下次默认构建自动再次全量处理。
def test_failed_full_rebuild_forces_next_run_to_recover(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "guide.md").write_text("# 指南", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    store.fail_rebuild = True

    with pytest.raises(RuntimeError, match="模拟全量写入失败"):
        update_index(data_dir, manifest_path, store, full=True)

    assert store.count() == 0
    store.fail_rebuild = False
    store.reset_events()

    result = update_index(data_dir, manifest_path, store)

    assert result.mode == "full"
    assert len(store.rebuild_calls) == 1
    assert store.count() == 1


# 验证新增来源在清单保存失败后重试，会先删除可能残留的旧 chunks。
def test_retrying_failed_addition_cleans_source_residue(tmp_path: Path, monkeypatch):
    data_dir, manifest_path = make_paths(tmp_path)
    (data_dir / "existing.md").write_text("# 已有文档", encoding="utf-8")
    store = FakeVectorStore()
    update_index(data_dir, manifest_path, store)
    added_path = data_dir / "added.md"
    added_path.write_text("# 新文档\n" + "A" * 900, encoding="utf-8")
    real_save_manifest = index_service.save_manifest

    # 模拟向量写入完成后，manifest 原子保存发生磁盘异常。
    def fail_manifest_save(path, manifest):
        raise OSError("模拟清单保存失败")

    monkeypatch.setattr(index_service, "save_manifest", fail_manifest_save)
    with pytest.raises(OSError, match="模拟清单保存失败"):
        update_index(data_dir, manifest_path, store)
    assert "added.md::1" in store.chunks

    added_path.write_text("# 新文档\n短内容", encoding="utf-8")
    monkeypatch.setattr(index_service, "save_manifest", real_save_manifest)
    store.reset_events()

    update_index(data_dir, manifest_path, store)

    assert store.delete_calls == [["added.md"]]
    assert "added.md::1" not in store.chunks


# 验证手册根目录不存在时直接终止，不删除已有向量或改写 manifest。
def test_missing_document_root_does_not_touch_existing_index(tmp_path: Path):
    missing_root = tmp_path / "missing-help"
    manifest_path = tmp_path / "processed" / "index_manifest.json"
    store = FakeVectorStore(initial_count=2)

    with pytest.raises(index_service.IndexSourceError, match="手册目录不存在"):
        update_index(missing_root, manifest_path, store)

    assert store.count() == 2
    assert store.rebuild_calls == []
    assert store.add_calls == []
    assert store.delete_calls == []
    assert not manifest_path.exists()


# 验证手册目录为空时拒绝清空已有索引，防止空目录挂载事故。
def test_empty_document_root_does_not_clear_existing_index(tmp_path: Path):
    data_dir, manifest_path = make_paths(tmp_path)
    store = FakeVectorStore(initial_count=2)

    with pytest.raises(index_service.IndexSourceError, match="没有可索引"):
        update_index(data_dir, manifest_path, store, full=True)

    assert store.count() == 2
    assert store.rebuild_calls == []
    assert not manifest_path.exists()
