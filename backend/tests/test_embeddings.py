from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import time

import app.rag.retrieval.embeddings as embeddings_module
from app.rag.retrieval.embeddings import LazyEmbeddings


# 提供可记录文档和问题调用的真实 embedding 测试替身。
class FakeEmbeddings:
    # 初始化调用记录。
    def __init__(self):
        self.document_calls: list[list[str]] = []
        self.query_calls: list[str] = []

    # 模拟批量文档向量化。
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_calls.append(texts)
        return [[float(len(text))] for text in texts]

    # 模拟单个问题向量化。
    def embed_query(self, text: str) -> list[float]:
        self.query_calls.append(text)
        return [float(len(text))]


# 验证构造懒加载代理时不会创建真实 embedding 模型。
def test_lazy_embeddings_does_not_load_model_during_construction():
    load_calls: list[str] = []

    # 记录真实模型工厂是否被调用。
    def factory(model_name: str):
        load_calls.append(model_name)
        return FakeEmbeddings()

    LazyEmbeddings("test-model", factory=factory)

    assert load_calls == []


# 验证文档和问题第一次向量化时加载一次，后续调用复用同一模型。
def test_lazy_embeddings_loads_once_on_first_use():
    load_calls: list[str] = []
    fake_embeddings = FakeEmbeddings()

    # 返回同一个测试模型并记录加载次数。
    def factory(model_name: str):
        load_calls.append(model_name)
        return fake_embeddings

    lazy = LazyEmbeddings("test-model", factory=factory)

    assert lazy.embed_documents(["文档"]) == [[2.0]]
    assert lazy.embed_query("问题") == [2.0]

    assert load_calls == ["test-model"]
    assert fake_embeddings.document_calls == [["文档"]]
    assert fake_embeddings.query_calls == ["问题"]


# 验证多个线程首次使用同一个代理时只会初始化一次真实模型。
def test_lazy_embeddings_is_thread_safe_on_first_use():
    load_calls: list[str] = []
    calls_lock = Lock()

    # 放大并发窗口并安全记录真实模型加载次数。
    def factory(model_name: str):
        time.sleep(0.02)
        with calls_lock:
            load_calls.append(model_name)
        return FakeEmbeddings()

    lazy = LazyEmbeddings("test-model", factory=factory)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lazy.embed_query, ["问题"] * 8))

    assert results == [[2.0]] * 8
    assert load_calls == ["test-model"]


# 验证同一进程中相同模型名称会复用已经创建的真实实例。
def test_create_embeddings_caches_model_by_name(monkeypatch):
    created: list[str] = []

    # 替换重量级 HuggingFace 模型，记录底层构造次数。
    def fake_huggingface_embeddings(*, model_name: str, encode_kwargs: dict):
        created.append(model_name)
        return FakeEmbeddings()

    monkeypatch.setattr(embeddings_module, "HuggingFaceEmbeddings", fake_huggingface_embeddings)
    embeddings_module.clear_embeddings_cache()

    first = embeddings_module.create_embeddings("cached-model")
    second = embeddings_module.create_embeddings("cached-model")

    assert first is second
    assert created == ["cached-model"]
    embeddings_module.clear_embeddings_cache()


# 验证不同懒加载代理并发请求同一模型时，进程级缓存只构造一个实例。
def test_create_embeddings_is_thread_safe_across_proxies(monkeypatch):
    created: list[str] = []
    calls_lock = Lock()

    # 放大底层模型并发构造窗口，验证缓存具备 single-flight 行为。
    def fake_huggingface_embeddings(*, model_name: str, encode_kwargs: dict):
        time.sleep(0.02)
        with calls_lock:
            created.append(model_name)
        return FakeEmbeddings()

    monkeypatch.setattr(embeddings_module, "HuggingFaceEmbeddings", fake_huggingface_embeddings)
    embeddings_module.clear_embeddings_cache()

    with ThreadPoolExecutor(max_workers=8) as executor:
        instances = list(executor.map(embeddings_module.create_embeddings, ["shared-model"] * 8))

    assert all(instance is instances[0] for instance in instances)
    assert created == ["shared-model"]
    embeddings_module.clear_embeddings_cache()
