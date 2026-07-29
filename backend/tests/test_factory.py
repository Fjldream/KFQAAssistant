from pathlib import Path

import app.rag.factory as factory


# 清理工厂函数缓存，避免不同测试之间共享上一个测试创建的对象。
def clear_factory_caches() -> None:
    if hasattr(factory.create_vector_store, "cache_clear"):
        factory.create_vector_store.cache_clear()
    if hasattr(factory.create_rag_chain, "cache_clear"):
        factory.create_rag_chain.cache_clear()


# 验证向量库只创建懒加载代理，不会提前加载真实 embedding 模型。
def test_create_vector_store_reuses_cached_instance(monkeypatch):
    calls = {"lazy_embeddings": 0, "vector_store": 0}

    class FakeLazyEmbeddings:
        # 记录轻量代理构造次数，不创建任何真实模型。
        def __init__(self, model_name: str) -> None:
            calls["lazy_embeddings"] += 1
            self.model_name = model_name

    class FakeVectorStore:
        # 记录向量库构造次数，模拟真实 ChromaVectorStore。
        def __init__(self, persist_dir: Path, embeddings) -> None:
            calls["vector_store"] += 1
            self.persist_dir = persist_dir
            self.embeddings = embeddings

    # 若工厂仍提前创建真实模型，测试应立即失败。
    def fail_create_embeddings(model_name: str):
        raise AssertionError(f"不应提前加载 embedding 模型: {model_name}")

    clear_factory_caches()
    monkeypatch.setattr(factory, "create_embeddings", fail_create_embeddings, raising=False)
    monkeypatch.setattr(factory, "LazyEmbeddings", FakeLazyEmbeddings, raising=False)
    monkeypatch.setattr(factory, "ChromaVectorStore", FakeVectorStore)

    first = factory.create_vector_store()
    second = factory.create_vector_store()

    assert first is second
    assert calls == {"lazy_embeddings": 1, "vector_store": 1}


# 验证 RAG Chain 只会组装一次，后续问答请求复用同一个 Chain。
def test_create_rag_chain_reuses_cached_instance(monkeypatch):
    calls = {"vector_store": 0, "llm": 0}

    # 模拟向量库创建，记录 create_rag_chain 是否重复调用它。
    def fake_create_vector_store():
        calls["vector_store"] += 1
        return object()

    class FakeDeepSeekClient:
        # 记录 LLM 客户端构造次数，模拟真实 DeepSeekClient。
        def __init__(self, **kwargs) -> None:
            calls["llm"] += 1
            self.kwargs = kwargs

    clear_factory_caches()
    monkeypatch.setattr(factory, "create_vector_store", fake_create_vector_store)
    monkeypatch.setattr(factory, "DeepSeekClient", FakeDeepSeekClient)

    first = factory.create_rag_chain()
    second = factory.create_rag_chain()

    assert first is second
    assert calls == {"vector_store": 1, "llm": 1}


# 验证清理函数会同时清理向量库缓存和 Chain 缓存。
def test_clear_rag_factory_cache_resets_cached_instances(monkeypatch):
    calls = {"lazy_embeddings": 0, "vector_store": 0}

    class FakeLazyEmbeddings:
        # 记录清理工厂缓存前后轻量代理的构造次数。
        def __init__(self, model_name: str) -> None:
            calls["lazy_embeddings"] += 1

    class FakeVectorStore:
        # 记录清理缓存前后是否重新构造向量库。
        def __init__(self, persist_dir: Path, embeddings) -> None:
            calls["vector_store"] += 1

    clear_factory_caches()
    monkeypatch.setattr(factory, "LazyEmbeddings", FakeLazyEmbeddings, raising=False)
    monkeypatch.setattr(factory, "ChromaVectorStore", FakeVectorStore)

    first = factory.create_vector_store()
    factory.clear_rag_factory_cache()
    second = factory.create_vector_store()

    assert first is not second
    assert calls == {"lazy_embeddings": 2, "vector_store": 2}


# 测试结束后清理缓存，避免影响后续真实工厂函数测试。
def teardown_function() -> None:
    clear_factory_caches()
