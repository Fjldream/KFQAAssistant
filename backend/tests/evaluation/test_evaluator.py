from app.evaluation.evaluator import evaluate_case
from app.evaluation.models import EvaluationCase, EvaluationTurn
from app.schemas.chat import ChatResponse, SourceSnippet


class FakeChain:
    def __init__(self, responses: list[ChatResponse]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    # 记录评测器传给问答链路的上下文参数，避免连续对话退化成单轮调用。
    def answer(self, question: str, conversation_summary="", conversation_turn_count=0, recent_messages=None):
        self.calls.append(
            {
                "question": question,
                "conversation_summary": conversation_summary,
                "conversation_turn_count": conversation_turn_count,
                "recent_messages": recent_messages or [],
            }
        )
        return self.responses.pop(0)


# 验证单轮评测会检查答案关键词、来源关键词、图片数量和来源数量。
def test_evaluate_single_turn_case_checks_rules():
    chain = FakeChain(
        [
            ChatResponse(
                answer="点击新建工程，填写名称后保存。[资料 1]",
                sources=[
                    SourceSnippet(
                        title="数采管理/工程开发-Windows",
                        source_path="html/数采管理/工程开发-Windows/index.html",
                        snippet="新建工程并填写名称。",
                        images=["工程开发/step1.png"],
                    )
                ],
                standalone_question="如何创建采集工程？",
            )
        ]
    )
    case = EvaluationCase(
        id="single.collect.create",
        category="数采管理",
        turns=[
            EvaluationTurn(
                question="如何创建采集工程？",
                expected_keywords=["新建工程", "名称"],
                expected_source_keywords=["数采管理"],
                expect_images=True,
                min_sources=1,
                min_images=1,
            )
        ],
    )

    result = evaluate_case(chain, case)

    assert result.passed is True
    assert result.turn_results[0].matched_keywords == ["新建工程", "名称"]
    assert result.turn_results[0].matched_source_keywords == ["数采管理"]
    assert result.turn_results[0].image_count == 1
    assert result.turn_results[0].source_count == 1


# 验证同义关键词组支持“组内任一表达命中”，避免答案正确但措辞不同被误判。
def test_evaluate_turn_accepts_keyword_groups():
    chain = FakeChain(
        [
            ChatResponse(
                answer="点击数采工程列表中的新建按钮，填写名称后保存。[资料 1]",
                sources=[
                    SourceSnippet(
                        title="数采管理",
                        source_path="helperFront/详细教程/2_KF开发中心/6_数采管理/1_基础配置介绍/数采管理.md",
                        snippet="通过新建按钮创建数采工程。",
                    )
                ],
                standalone_question="如何创建采集工程？",
            )
        ]
    )
    case = EvaluationCase(
        id="single.collect.create",
        category="数采管理",
        turns=[
            EvaluationTurn(
                question="如何创建采集工程？",
                expected_keyword_groups=[["新建工程", "新建数采工程", "新建按钮"], ["名称"]],
                expected_source_keyword_groups=[["数采管理/工程开发-Windows", "数采管理"]],
            )
        ],
    )

    result = evaluate_case(chain, case)

    assert result.passed is True
    assert result.turn_results[0].matched_keywords == ["新建按钮", "名称"]
    assert result.turn_results[0].matched_source_keywords == ["数采管理"]


# 验证不应回答的问题必须拒答，并且不能返回资料来源。
def test_evaluate_no_answer_case_requires_refusal_without_sources():
    chain = FakeChain(
        [
            ChatResponse(
                answer="手册中没有找到相关说明。",
                sources=[],
                standalone_question="手册里有没有微信登录说明？",
            )
        ]
    )
    case = EvaluationCase(
        id="single.wechat.no_answer",
        category="边界问题",
        turns=[
            EvaluationTurn(
                question="手册里有没有微信登录说明？",
                expected_keywords=["手册中没有找到相关说明"],
                expect_no_answer=True,
            )
        ],
    )

    result = evaluate_case(chain, case)

    assert result.passed is True
    assert result.turn_results[0].no_answer_passed is True
    assert result.turn_results[0].source_count == 0


# 验证连续对话第二轮会携带摘要、最近消息和对话轮次。
def test_evaluate_dialogue_case_passes_conversation_context_to_next_turn():
    chain = FakeChain(
        [
            ChatResponse(
                answer="点击新建工程，填写名称。[资料 1]",
                sources=[
                    SourceSnippet(
                        title="数采管理/工程开发-Windows",
                        source_path="html/数采管理/工程开发-Windows/index.html",
                        snippet="新建工程并填写名称。",
                    )
                ],
                conversation_summary="用户正在了解采集工程创建。",
                standalone_question="如何创建采集工程？",
            ),
            ChatResponse(
                answer="创建完成后发布到运维中心，然后部署并启动。[资料 1]",
                sources=[
                    SourceSnippet(
                        title="教程/5分钟完成KingScada数据接入KF3.6平台",
                        source_path="html/教程/5分钟完成KingScada数据接入KF3.6平台/index.html",
                        snippet="发布、部署并启动工程。",
                    )
                ],
                conversation_summary="用户正在了解采集工程创建和运行。",
                standalone_question="采集工程创建完成后怎么运行？",
            ),
        ]
    )
    case = EvaluationCase(
        id="dialog.collect.run",
        category="数采管理",
        turns=[
            EvaluationTurn(question="如何创建采集工程？", expected_keywords=["新建工程"]),
            EvaluationTurn(question="那怎么运行？", expected_keywords=["启动"]),
        ],
        priority="P0",
    )

    result = evaluate_case(chain, case)

    assert result.passed is True
    assert chain.calls[1]["conversation_summary"] == "用户正在了解采集工程创建。"
    assert chain.calls[1]["conversation_turn_count"] == 1
    assert [message.role for message in chain.calls[1]["recent_messages"]] == ["user", "assistant"]
    assert result.turn_results[1].standalone_question == "采集工程创建完成后怎么运行？"
