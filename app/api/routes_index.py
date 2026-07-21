from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import verify_api_key
from app.core.config import get_settings
from app.rag.factory import clear_rag_factory_cache, create_vector_store
from app.rag.index_manifest import ManifestFormatError, load_manifest
from app.rag.index_service import (
    IndexSourceError,
    build_index_signature,
    is_rebuild_pending,
    update_index,
)

router = APIRouter(prefix="/api/index", tags=["index"])
index_update_lock = Lock()


# 读取 manifest 修改时间，作为最近一次真正写入索引清单的时间。
def get_manifest_modified_at(manifest_path: Path) -> str | None:
    try:
        modified_at = manifest_path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(modified_at, tz=timezone.utc).isoformat()


# 索引状态接口：检查向量、manifest 和当前配置是否一致，不触发重建或 embedding。
@router.get("/status", dependencies=[Depends(verify_api_key)])
def index_status():
    settings = get_settings()
    manifest_path = Path(settings.index_manifest_path)
    chunks = create_vector_store().count()
    current_signature = build_index_signature(
        embedding_model_name=settings.embedding_model_name,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    rebuild_pending = is_rebuild_pending(manifest_path)
    manifest = None
    issue = None
    try:
        manifest = load_manifest(manifest_path)
    except ManifestFormatError as exc:
        issue = str(exc)

    index_signature = manifest.index_signature if manifest is not None else None
    config_matches = manifest is not None and index_signature == current_signature
    documents = len(manifest.documents) if manifest is not None else 0
    if issue is not None:
        status = "error"
    elif rebuild_pending:
        status = "rebuild_required"
        issue = "检测到未完成的全量重建，请重新执行索引构建。"
    elif chunks == 0:
        status = "empty"
        issue = "知识库索引为空，请先执行索引构建。"
    elif not config_matches:
        status = "stale"
        issue = "当前索引与 embedding 或分块配置不一致，请重新构建索引。"
    else:
        status = "ready"

    return {
        "status": status,
        "chunks": chunks,
        "documents": documents,
        "last_built_at": get_manifest_modified_at(manifest_path),
        "index_signature": index_signature,
        "current_signature": current_signature,
        "config_matches": config_matches,
        "rebuild_pending": rebuild_pending,
        "persist_dir": str(settings.chroma_persist_dir),
        "manifest_path": str(manifest_path),
        "issue": issue,
    }


# 索引更新接口：默认增量处理变化文档，full=true 时强制全量重建。
@router.post("/rebuild", dependencies=[Depends(verify_api_key)])
def rebuild_index(full: bool = False):
    if not index_update_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="已有索引构建任务正在运行，请稍后重试。")
    try:
        settings = get_settings()
        result = update_index(
            root_dir=settings.data_dir,
            manifest_path=settings.index_manifest_path,
            vector_store=create_vector_store(),
            full=full,
            embedding_model_name=settings.embedding_model_name,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        clear_rag_factory_cache()
        return result.to_dict()
    except IndexSourceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        index_update_lock.release()
