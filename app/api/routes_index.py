from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key
from app.core.config import get_settings
from app.rag.factory import clear_rag_factory_cache, create_vector_store
from app.rag.index_service import update_index

router = APIRouter(prefix="/api/index", tags=["index"])


# 索引状态接口：快速查看向量库是否已有 chunk，不触发重建或 embedding。
@router.get("/status", dependencies=[Depends(verify_api_key)])
def index_status():
    settings = get_settings()
    chunks = create_vector_store().count()
    return {
        "status": "ready" if chunks > 0 else "empty",
        "chunks": chunks,
        "persist_dir": str(settings.chroma_persist_dir),
    }


# 索引更新接口：默认增量处理变化文档，full=true 时强制全量重建。
@router.post("/rebuild", dependencies=[Depends(verify_api_key)])
def rebuild_index(full: bool = False):
    settings = get_settings()
    result = update_index(
        root_dir=settings.data_dir,
        manifest_path=settings.index_manifest_path,
        vector_store=create_vector_store(),
        full=full,
    )
    clear_rag_factory_cache()
    return result.to_dict()
