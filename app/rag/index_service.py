from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from app.rag.document_loader import discover_document_paths, load_document
from app.rag.index_manifest import IndexManifest, ManifestEntry, hash_file, load_manifest, save_manifest
from app.rag.models import DocumentChunk, ManualDocument
from app.rag.splitter import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, split_documents


INDEX_PIPELINE_VERSION = 1
DEFAULT_EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"


# 表示手册根目录缺失或类型错误，索引服务不会在此异常下修改向量库。
class IndexSourceError(ValueError):
    pass


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


# 根据会影响向量内容的配置生成稳定指纹，用于判断旧索引是否兼容。
def build_index_signature(
    embedding_model_name: str,
    chunk_size: int,
    chunk_overlap: int,
    pipeline_version: int = INDEX_PIPELINE_VERSION,
) -> str:
    payload = json.dumps(
        {
            "pipeline_version": pipeline_version,
            "embedding_model_name": embedding_model_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# 校验分块参数，避免 overlap 大于等于 chunk_size 时切块循环无法前进。
def _validate_chunk_settings(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须大于等于 0 且小于 chunk_size")


# 根据当前文件哈希和 chunk IDs 生成可持久化的完整索引清单。
def _create_manifest(
    source_paths: list[str],
    content_hashes: dict[str, str],
    chunk_ids: dict[str, list[str]],
    index_signature: str,
) -> IndexManifest:
    return IndexManifest(
        documents={
            source_path: ManifestEntry(
                content_hash=content_hashes[source_path],
                chunk_ids=chunk_ids[source_path],
            )
            for source_path in sorted(source_paths)
        },
        index_signature=index_signature,
    )


# 返回全量重建恢复标记路径；标记存在时下一次构建必须再次走全量流程。
def _rebuild_marker_path(manifest_path: Path) -> Path:
    return manifest_path.with_name(f"{manifest_path.name}.rebuild_pending")


# 在破坏性全量操作前写入恢复标记，防止失败后被旧 manifest 误判为无需更新。
def _mark_rebuild_pending(manifest_path: Path) -> None:
    marker_path = _rebuild_marker_path(manifest_path)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("full rebuild pending\n", encoding="utf-8")


# 仅在向量和 manifest 都成功写入后清除全量重建恢复标记。
def _clear_rebuild_pending(manifest_path: Path) -> None:
    _rebuild_marker_path(manifest_path).unlink(missing_ok=True)


# 全量加载、切块并重建 Chroma，成功后覆盖写入完整索引清单。
def _rebuild_full(
    root_dir: Path,
    manifest_path: Path,
    paths_by_source: dict[str, Path],
    content_hashes: dict[str, str],
    vector_store,
    index_signature: str,
    chunk_size: int,
    chunk_overlap: int,
) -> IndexUpdateResult:
    source_paths = sorted(paths_by_source)
    documents = _load_selected_documents([paths_by_source[source] for source in source_paths], root_dir)
    chunks = split_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    _mark_rebuild_pending(manifest_path)
    written_chunks = vector_store.rebuild(chunks)
    chunk_ids = _chunk_ids_by_source(source_paths, chunks)
    save_manifest(
        manifest_path,
        _create_manifest(source_paths, content_hashes, chunk_ids, index_signature),
    )
    _clear_rebuild_pending(manifest_path)
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
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL_NAME,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    pipeline_version: int = INDEX_PIPELINE_VERSION,
) -> IndexUpdateResult:
    _validate_chunk_settings(chunk_size, chunk_overlap)
    root_dir = Path(root_dir).resolve()
    manifest_path = Path(manifest_path)
    if not root_dir.is_dir():
        raise IndexSourceError(f"手册目录不存在或不是目录: {root_dir}")
    paths = discover_document_paths(root_dir)
    if not paths:
        raise IndexSourceError(f"手册目录中没有可索引的 Markdown 或 HTML 文档: {root_dir}")
    paths_by_source = _paths_by_source(root_dir, paths)
    content_hashes = {source: hash_file(path) for source, path in paths_by_source.items()}
    index_signature = build_index_signature(
        embedding_model_name=embedding_model_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        pipeline_version=pipeline_version,
    )

    if full or _rebuild_marker_path(manifest_path).exists():
        return _rebuild_full(
            root_dir,
            manifest_path,
            paths_by_source,
            content_hashes,
            vector_store,
            index_signature,
            chunk_size,
            chunk_overlap,
        )

    previous = load_manifest(manifest_path)
    if previous is None and vector_store.count() > 0:
        return _rebuild_full(
            root_dir,
            manifest_path,
            paths_by_source,
            content_hashes,
            vector_store,
            index_signature,
            chunk_size,
            chunk_overlap,
        )
    if previous is not None and previous.index_signature != index_signature:
        return _rebuild_full(
            root_dir,
            manifest_path,
            paths_by_source,
            content_hashes,
            vector_store,
            index_signature,
            chunk_size,
            chunk_overlap,
        )

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
    chunks = split_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    removed_sources = changed_sources + deleted
    if removed_sources:
        vector_store.delete_sources(removed_sources)
    written_chunks = vector_store.add_chunks(chunks) if chunks else 0

    chunk_ids = _chunk_ids_by_source(changed_sources, chunks)
    next_documents = {source: previous.documents[source] for source in skipped}
    next_documents.update(
        _create_manifest(changed_sources, content_hashes, chunk_ids, index_signature).documents
    )
    save_manifest(
        manifest_path,
        IndexManifest(documents=next_documents, index_signature=index_signature),
    )
    return IndexUpdateResult(
        mode="incremental",
        added_documents=len(added),
        modified_documents=len(modified),
        deleted_documents=len(deleted),
        skipped_documents=len(skipped),
        written_chunks=written_chunks,
        total_chunks=vector_store.count(),
    )
