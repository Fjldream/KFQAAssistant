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


def test_rerank_prefers_system_requirement_document_for_environment_question():
    tutorial = RetrievedChunk(
        DocumentChunk(
            id="tutorial::0",
            title="登录开发系统客户端",
            source_path="计算APP组态/产品教程/登录开发系统客户端.html",
            content="在浏览器地址中输入应用中心所在 IP 即可打开登录页面。",
        ),
        score=0.55,
    )
    requirement = RetrievedChunk(
        DocumentChunk(
            id="requirement::0",
            title="关于/系统环境要求/客户端/客户端",
            source_path="关于/系统环境要求/客户端/客户端.md",
            content="软件要求：Windows2012以上，Win7、Win10；Linux；Chrome浏览器。",
        ),
        score=0.5,
    )

    ranked = rerank("客户端对操作系统有什么要求？", [tutorial, requirement], limit=2)

    assert ranked[0].chunk.id == "requirement::0"
