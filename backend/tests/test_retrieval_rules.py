from app.rag.retrieval_rules import expand_terms_with_rules, workflow_intent_score


def test_expand_terms_with_rules_loads_project_start_terms():
    terms = expand_terms_with_rules("如何启动数据组态工程？")

    assert "发布" in terms
    assert "部署" in terms
    assert "运维中心" in terms
    assert "数据组态工程的启动" in terms


def test_workflow_intent_score_boosts_complete_workflow_text():
    score = workflow_intent_score(
        "如何启动数据组态工程？",
        "选择工程点击发布，打开运维中心，在运行的节点下面添加端口，然后部署并启动。",
    )

    assert score > 0


def test_workflow_intent_score_ignores_management_overview():
    score = workflow_intent_score(
        "如何启动数据组态工程？",
        "数据源工程管理包括新建、编辑、删除、导入、导出、发布和撤销发布工程。",
    )

    assert score == 0
