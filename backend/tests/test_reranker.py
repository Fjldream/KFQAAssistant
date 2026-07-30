from app.rag.models import DocumentChunk
from app.rag.reranker import explain_rerank, rerank
from app.rag.retriever import RetrievedChunk


def test_rerank_prefers_workflow_steps_over_management_overview():
    overview = RetrievedChunk(
        DocumentChunk(
            id="overview::0",
            title="数据APP组态/工程管理",
            source_path="数据APP组态/工程管理.html",
            content="工程管理包括新建、编辑、删除、发布和撤销发布工程。",
        ),
        score=0.9,
    )
    workflow = RetrievedChunk(
        DocumentChunk(
            id="workflow::0",
            title="教程/数据组态工程的启动",
            source_path="教程/KingScada数据接入.html",
            content="选择工程点击发布，打开运维中心，添加端口，对 APP 执行部署、启动操作。",
        ),
        score=0.7,
    )

    ranked = rerank("如何启动数据组态工程？", [overview, workflow], limit=2)

    assert ranked[0].chunk.id == "workflow::0"


def test_explain_rerank_returns_human_readable_reasons():
    candidate = RetrievedChunk(
        DocumentChunk(
            id="workflow::0",
            title="教程/数据组态工程的启动",
            source_path="教程/KingScada数据接入.html",
            content="打开运维中心，添加端口，部署并启动。",
        ),
        score=0.7,
    )

    reasons = explain_rerank("如何启动数据组态工程？", candidate)

    assert "包含操作流程信号" in reasons
