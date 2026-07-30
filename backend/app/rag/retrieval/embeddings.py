from threading import Lock
from typing import Callable

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings


_embeddings_cache: dict[str, Embeddings] = {}
_embeddings_cache_lock = Lock()


# 创建并按模型名称缓存本地 HuggingFace embedding 模型。
def create_embeddings(model_name: str) -> Embeddings:
    with _embeddings_cache_lock:
        embeddings = _embeddings_cache.get(model_name)
        if embeddings is None:
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                encode_kwargs={"normalize_embeddings": True},
            )
            _embeddings_cache[model_name] = embeddings
        return embeddings


# 清理进程级真实模型缓存，仅供测试或显式释放模型资源时使用。
def clear_embeddings_cache() -> None:
    with _embeddings_cache_lock:
        _embeddings_cache.clear()


# 延迟创建真实 embedding 模型，避免只检查索引状态时加载重量级模型。
class LazyEmbeddings(Embeddings):
    # 保存模型名称和模型工厂，构造阶段不执行真实加载。
    def __init__(
        self,
        model_name: str,
        factory: Callable[[str], Embeddings] = create_embeddings,
    ) -> None:
        self.model_name = model_name
        self.factory = factory
        self._embeddings: Embeddings | None = None
        self._load_lock = Lock()

    # 线程安全地获取真实模型，加载失败时保留空状态供下次重试。
    def _get_embeddings(self) -> Embeddings:
        if self._embeddings is None:
            with self._load_lock:
                if self._embeddings is None:
                    self._embeddings = self.factory(self.model_name)
        return self._embeddings

    # 首次写入向量时加载模型，并代理批量文档 embedding。
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._get_embeddings().embed_documents(texts)

    # 首次检索时加载模型，并代理问题 embedding。
    def embed_query(self, text: str) -> list[float]:
        return self._get_embeddings().embed_query(text)
