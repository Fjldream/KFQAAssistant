from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key
from app.core.config import get_settings
from app.rag.document_loader import load_documents
from app.rag.factory import clear_rag_factory_cache, create_vector_store
from app.rag.splitter import split_documents

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


# 索引重建接口：加载手册、切块并写入本地 Chroma 向量库。
@router.post("/rebuild", dependencies=[Depends(verify_api_key)])
def rebuild_index():
    settings = get_settings()
    documents = load_documents(settings.data_dir)
    chunks = split_documents(documents)
    count = create_vector_store().rebuild(chunks)
    clear_rag_factory_cache()
    return {"status": "ok", "chunks": count}
