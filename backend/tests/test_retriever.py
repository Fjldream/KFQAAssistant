from app.rag.models import DocumentChunk
from app.rag.errors import IndexNotReadyError
from app.rag.retrieval.retriever import RetrievedChunk, RetrieverService
from app.rag.retrieval.vector_store import combined_score, diversify_results, keyword_score


class FakeVectorStore:
    def count(self):
        return 1

    def similarity_search(self, query: str, top_k: int):
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    id="a::0",
                    title="页面编辑器/简介",
                    source_path="页面编辑器/简介.md",
                    content="页面编辑器包括菜单栏、工具栏、工具箱和配置窗。",
                    images=["页面编辑器/1.png"],
                ),
                score=0.91,
            )
        ]


class FakeEmptyVectorStore:
    def count(self):
        return 0

    def similarity_search(self, query: str, top_k: int):
        raise AssertionError("空索引不应该继续执行相似度检索")


class FakeRewriter:
    # 返回原问题和一个运行类改写问题，模拟 Query Rewrite 输出。
    def rewrite(self, question: str):
        from app.rag.retrieval.query_rewriter import QueryAnalysis, RewriteResult

        return RewriteResult(
            original_question=question,
            queries=[question, "如何在运维中心部署并启动采集工程？"],
            analysis=QueryAnalysis(
                original_question=question,
                intent="workflow",
                entities=["采集工程"],
                needs_images=False,
                needs_steps=True,
            ),
        )


class FakeMultiQueryVectorStore:
    # 记录每次检索查询，并按查询内容返回不同片段。
    def __init__(self):
        self.queries = []

    # 返回非空索引数量，让检索继续执行。
    def count(self):
        return 10

    # 根据改写查询模拟创建片段和启动片段的多路召回。
    def similarity_search(self, query: str, top_k: int):
        self.queries.append(query)
        if "启动" in query:
            return [
                RetrievedChunk(
                    DocumentChunk(id="run::0", title="运行工程", source_path="运行工程.md", content="部署并启动。"),
                    score=0.9,
                )
            ]
        return [
            RetrievedChunk(
                DocumentChunk(id="create::0", title="创建工程", source_path="创建工程.md", content="点击新建工程。"),
                score=0.8,
            )
        ]


class FakeReranker:
    # 记录重排输入，并故意反转结果，验证 Retriever 会调用重排序器。
    def __init__(self):
        self.called_with_query = ""

    # 模拟重排序器接口，返回反转后的候选资料。
    def __call__(self, query: str, candidates: list[RetrievedChunk], limit: int):
        self.called_with_query = query
        return list(reversed(candidates))[:limit]


def test_retriever_returns_ranked_chunks():
    service = RetrieverService(vector_store=FakeVectorStore(), top_k=5)

    results = service.retrieve("页面编辑器有哪些区域？")

    assert results[0].score == 0.91
    assert results[0].chunk.images == ["页面编辑器/1.png"]


def test_retriever_uses_rewritten_queries_when_rewriter_is_enabled():
    vector_store = FakeMultiQueryVectorStore()
    service = RetrieverService(vector_store=vector_store, top_k=5, query_rewriter=FakeRewriter())

    results = service.retrieve("如何创建采集工程，如何运行它呢？")

    assert vector_store.queries == ["如何创建采集工程，如何运行它呢？", "如何在运维中心部署并启动采集工程？"]
    assert [item.chunk.id for item in results] == ["run::0", "create::0"]


def test_retriever_calls_optional_reranker():
    vector_store = FakeMultiQueryVectorStore()
    reranker = FakeReranker()
    service = RetrieverService(
        vector_store=vector_store,
        top_k=5,
        query_rewriter=FakeRewriter(),
        reranker=reranker,
    )

    results = service.retrieve("如何创建采集工程，如何运行它呢？")

    assert reranker.called_with_query == "如何创建采集工程，如何运行它呢？"
    assert [item.chunk.id for item in results] == ["create::0", "run::0"]


# 验证索引为空时检索层主动中断，避免后续返回误导性的“没有答案”。
def test_retriever_raises_when_index_is_empty():
    service = RetrieverService(vector_store=FakeEmptyVectorStore(), top_k=5)

    try:
        service.retrieve("页面编辑器有哪些区域？")
    except IndexNotReadyError as exc:
        assert exc.public_message == "知识库索引还没有构建，请先执行索引构建。"
    else:
        raise AssertionError("空索引时应该抛出 IndexNotReadyError")


def test_keyword_score_boosts_system_environment_document():
    correct = DocumentChunk(
        id="env::0",
        title="关于/系统环境要求/客户端/客户端",
        source_path="关于/系统环境要求/客户端/客户端.md",
        content="客户端参数。软件要求：Windows、Linux、Chrome 浏览器。",
    )
    wrong = DocumentChunk(
        id="window::0",
        title="页面编辑器/工具箱/UI组件/Windows窗脚本属性",
        source_path="页面编辑器/工具箱/UI组件/Windows窗脚本属性.md",
        content="描述 Windows 窗组件的位置、宽度和高度。",
    )

    query = "客户端对操作系统有什么要求？"

    assert keyword_score(query, correct) > keyword_score(query, wrong)


# 验证工程运行类问题会优先命中包含发布、部署、启动流程的教程片段。
def test_keyword_score_boosts_project_start_workflow_document():
    correct = DocumentChunk(
        id="tutorial::0",
        title="教程/5分钟完成KingScada数据接入KF3.6平台/实时数据采集到界面展示",
        source_path="教程/5分钟完成KingScada数据接入KF3.6平台/实时数据采集到界面展示.html",
        content=(
            "数据源名称：自定义。工程名称：KingSCADA中创建的工程的名称。"
            "选择刚才创建的工程，点击发布。2.2.2 数据组态工程的启动。"
            "打开运维中心，在运行的节点下面点击添加，添加端口，对添加好的 APP 依次执行部署、启动操作。"
        ),
    )
    wrong = DocumentChunk(
        id="intro::0",
        title="客户端APP组态/功能模块/工程配置/数据源管理/简介",
        source_path="客户端APP组态/功能模块/工程配置/数据源管理/简介.html",
        content=(
            "客户端模块的数据源是通过数据源组态中的数据源，连接到开发态的数据接口服务工程配置和管理的服务中，"
            "通过数据接口服务工程运行实例名称和对应的数据源名称，从数据接口服务中的工程库中获取数据信息。"
        ),
    )

    query = "如何启动数据组态工程？"

    assert keyword_score(query, correct) > keyword_score(query, wrong)


def test_combined_score_prefers_complete_project_start_workflow():
    workflow = DocumentChunk(
        id="workflow::0",
        title="教程/数据组态工程的创建与启动",
        source_path="教程/5分钟完成KingScada数据接入KF3.6平台/历史数据采集到界面展示.html",
        content=(
            "选择刚才创建的工程，点击发布。3.2.2 数据组态工程的启动。"
            "打开运维中心，在运行的节点下面点击添加，添加端口，对添加好的 APP 依次执行部署、启动操作。"
        ),
    )
    management = DocumentChunk(
        id="management::0",
        title="数据APP组态/工程管理",
        source_path="数据APP组态/工程管理.html",
        content="数据源工程管理包括新建、编辑、删除、导入、导出、编辑共享、发布、更新和撤销发布工程。",
    )

    query = "如何启动数据组态工程？"

    assert combined_score(query, RetrievedChunk(workflow, 0.42)) > combined_score(query, RetrievedChunk(management, 0.52))


def test_keyword_score_prefers_real_manual_start_workflow_over_management_overview():
    workflow = DocumentChunk(
        id="real-workflow::0",
        title="教程/5分钟完成KingScada数据接入KF3.6平台/3分钟完成KingScada历史数据采集到界面展示",
        source_path="教程/5分钟完成KingScada数据接入KF3.6平台/3分钟完成KingScada历史数据采集到界面展示.html",
        content=(
            "工程名称：KingSCADA中创建的工程的名称。连接名称：自定义，必填项。"
            "选择刚才创建的工程，点击发布。3.2.2 数据组态工程的启动。"
            "打开运维中心，在运行的节点下面点击添加，添加端口，点击提交。"
            "对添加好的 APP 依次执行部署、启动操作。"
        ),
    )
    management = DocumentChunk(
        id="management::0",
        title="数据APP组态/工程管理/工程管理",
        source_path="数据APP组态/工程管理/工程管理.html",
        content="数据源工程管理包括新建、编辑、删除、导入、导出、编辑共享、发布、更新和撤销发布工程。点击新建工程按钮。",
    )

    query = "如何启动数据组态工程？"

    assert keyword_score(query, workflow) > keyword_score(query, management)


def test_combined_score_adds_vector_score_and_weighted_keyword_score():
    chunk = DocumentChunk(
        id="doc::0",
        title="页面编辑器/简介",
        source_path="页面编辑器/简介.md",
        content="页面编辑器包括菜单栏。",
    )
    item = RetrievedChunk(chunk=chunk, score=0.5)

    assert combined_score("页面编辑器有哪些区域？", item) == 0.5 + keyword_score("页面编辑器有哪些区域？", chunk) * 0.08


def test_diversify_results_prefers_different_sources_before_filling_duplicates():
    results = [
        RetrievedChunk(
            chunk=DocumentChunk(id="a::0", title="A", source_path="A.md", content="高分片段"),
            score=0.95,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="a::1", title="A", source_path="A.md", content="次高分片段"),
            score=0.94,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="b::0", title="B", source_path="B.md", content="不同来源"),
            score=0.80,
        ),
    ]

    diversified = diversify_results(results, top_k=2, max_chunks_per_source=1)

    assert [item.chunk.id for item in diversified] == ["a::0", "b::0"]


def test_diversify_results_fills_remaining_slots_with_high_score_duplicates():
    results = [
        RetrievedChunk(
            chunk=DocumentChunk(id="a::0", title="A", source_path="A.md", content="高分片段"),
            score=0.95,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="a::1", title="A", source_path="A.md", content="次高分片段"),
            score=0.94,
        ),
        RetrievedChunk(
            chunk=DocumentChunk(id="b::0", title="B", source_path="B.md", content="不同来源"),
            score=0.80,
        ),
    ]

    diversified = diversify_results(results, top_k=3, max_chunks_per_source=1)

    assert [item.chunk.id for item in diversified] == ["a::0", "b::0", "a::1"]
