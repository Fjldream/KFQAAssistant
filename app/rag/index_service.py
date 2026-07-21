from dataclasses import asdict, dataclass
from pathlib import Path

from app.rag.document_loader import discover_document_paths, load_document
from app.rag.index_manifest import IndexManifest, ManifestEntry, hash_file, load_manifest, save_manifest
from app.rag.models import DocumentChunk, ManualDocument
from app.rag.splitter import split_documents


# 汇总一次索引任务的模式和变更数量，供命令行与 API 统一展示。
@dataclass(frozen=True)
class IndexUpdateResult:
    mode: str
    added_documents: int
    modified_documents: int
    deleted_documents: int
    skipped_documents: int
    written_chunks: int
    total_chunks: int

    # 将构建结果转换为 FastAPI 可序列化、CLI 可遍历的字典。
    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


# 把绝对文件路径转换成以 data_dir 为根的稳定来源路径映射。
def _paths_by_source(root_dir: Path, paths: list[Path]) -> dict[str, Path]:
    return {path.relative_to(root_dir).as_posix(): path for path in paths}


# 只加载指定路径中的有效手册，空文档不会进入后续切块流程。
def _load_selected_documents(paths: list[Path], root_dir: Path) -> list[ManualDocument]:
    documents = [load_document(path, root_dir) for path in paths]
    return [document for document in documents if document is not None]


# 按来源整理本次生成的 chunk IDs，包含没有正文 chunk 的空列表来源。
def _chunk_ids_by_source(source_paths: list[str], chunks: list[DocumentChunk]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {source_path: [] for source_path in source_paths}
    for chunk in chunks:
        result[chunk.source_path].append(chunk.id)
    return result


# 根据当前文件哈希和 chunk IDs 生成可持久化的完整索引清单。
def _create_manifest(
    source_paths: list[str],
    content_hashes: dict[str, str],
    chunk_ids: dict[str, list[str]],
) -> IndexManifest:
    return IndexManifest(
        documents={
            source_path: ManifestEntry(
                content_hash=content_hashes[source_path],
                chunk_ids=chunk_ids[source_path],
            )
            for source_path in sorted(source_paths)
        }
    )


# 全量加载、切块并重建 Chroma，成功后覆盖写入完整索引清单。
def _rebuild_full(
    root_dir: Path,
    manifest_path: Path,
    paths_by_source: dict[str, Path],
    content_hashes: dict[str, str],
    vector_store,
) -> IndexUpdateResult:
    source_paths = sorted(paths_by_source)
    documents = _load_selected_documents([paths_by_source[source] for source in source_paths], root_dir)
    chunks = split_documents(documents)
    written_chunks = vector_store.rebuild(chunks)
    chunk_ids = _chunk_ids_by_source(source_paths, chunks)
    save_manifest(manifest_path, _create_manifest(source_paths, content_hashes, chunk_ids))
    return IndexUpdateResult(
        mode="full",
        added_documents=len(source_paths),
        modified_documents=0,
        deleted_documents=0,
        skipped_documents=0,
        written_chunks=written_chunks,
        total_chunks=vector_store.count(),
    )


# 比较文档清单并执行增量或全量索引构建。
def update_index(
    root_dir: Path,
    manifest_path: Path,
    vector_store,
    full: bool = False,
) -> IndexUpdateResult:
    root_dir = root_dir.resolve()
    paths = discover_document_paths(root_dir)
    paths_by_source = _paths_by_source(root_dir, paths)
    content_hashes = {source: hash_file(path) for source, path in paths_by_source.items()}

    if full:
        return _rebuild_full(root_dir, manifest_path, paths_by_source, content_hashes, vector_store)

    previous = load_manifest(manifest_path)
    if previous is None and vector_store.count() > 0:
        return _rebuild_full(root_dir, manifest_path, paths_by_source, content_hashes, vector_store)

    previous = previous or IndexManifest(documents={})
    old_sources = set(previous.documents)
    current_sources = set(paths_by_source)
    added = sorted(current_sources - old_sources)
    deleted = sorted(old_sources - current_sources)
    modified = sorted(
        source
        for source in current_sources & old_sources
        if content_hashes[source] != previous.documents[source].content_hash
    )
    skipped = sorted((current_sources & old_sources) - set(modified))
    changed_sources = added + modified

    documents = _load_selected_documents(
        [paths_by_source[source] for source in changed_sources],
        root_dir,
    )
    chunks = split_documents(documents)
    removed_sources = modified + deleted
    if removed_sources:
        vector_store.delete_sources(removed_sources)
    written_chunks = vector_store.add_chunks(chunks) if chunks else 0

    chunk_ids = _chunk_ids_by_source(changed_sources, chunks)
    next_documents = {source: previous.documents[source] for source in skipped}
    next_documents.update(
        _create_manifest(changed_sources, content_hashes, chunk_ids).documents
    )
    save_manifest(manifest_path, IndexManifest(documents=next_documents))
    return IndexUpdateResult(
        mode="incremental",
        added_documents=len(added),
        modified_documents=len(modified),
        deleted_documents=len(deleted),
        skipped_documents=len(skipped),
        written_chunks=written_chunks,
        total_chunks=vector_store.count(),
    )
