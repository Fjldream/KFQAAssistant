# RAG Evaluation Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 RAG 评测中心升级为后端可信执行、混合指标判分、可复现、可批准基线并能通过本地退出码阻断发布的内部质量门禁。

**Architecture:** 保留 FastAPI、Vue 3 和 SQLite，以 Git 版本化 Suite 作为评测真值；新增后端 Runner 统一执行真实 RAG、通用指标和双重门禁。前端通过 Run API 创建、轮询和取消任务，不再上传评分结果；CLI 直接复用同一个 Runner。

**Tech Stack:** Python 3.11、FastAPI、Pydantic v2、SQLite、httpx、pytest、Vue 3、TypeScript、Vitest、DeepSeek V4 Flash。

## Global Constraints

- 所有 DeepSeek 调用统一使用 `deepseek-v4-flash`，并显式发送 `thinking: {"type": "disabled"}`。
- 第一期 Suite 固定为 20 条人工审核的 `core` 用例。
- 关键词只作为少量硬锚点，且只匹配答案正文；来源单独评测。
- Case 判定采用分项门槛，不计算可互相补偿的综合加权分。
- 必要 Judge 指标失败或缺失时 Run 必须为 `INVALID`，不得默认为通过或 0 分。
- 后端是唯一评分方；新前端不得调用 `/runs/progressive` 或上传 CaseResult。
- SQLite 一期限制单实例一个活动 Run，并启用外键和 WAL。
- 不在一期实现真实问题采集、外部 CI、多租户、RBAC、分布式 Worker 或 PostgreSQL。
- 不修改与评测门禁无关的现有工作区变更。

---

## File Map

### Backend files to create

- `backend/app/observability/model_usage.py`：基于 `ContextVar` 的模型调用用量采集器。
- `backend/app/evaluation/suite.py`：Suite、Case、Turn、RequiredFact 和 Threshold Pydantic 模型。
- `backend/app/evaluation/answer_quality.py`：参考答案与关键事实 Judge。
- `backend/app/evaluation/retrieval_metrics.py`：Hit@K、Recall@K、MRR 和禁止来源指标。
- `backend/app/evaluation/snapshot.py`：构建无敏感信息的运行快照。
- `backend/app/evaluation/runner.py`：状态机、可信执行、取消和运行汇总。
- `backend/app/evaluation/coordinator.py`：单活动 Run 的应用内后台协调器。
- `backend/app/evaluation/costs.py`：Token 汇总和费用估算。
- `backend/evaluation_cases/core.v1.json`：20 条正式 core 用例。
- `backend/scripts/evaluation_gate.py`：本地校准/阻断命令。
- `backend/tests/evaluation/test_suite.py`
- `backend/tests/evaluation/test_answer_quality.py`
- `backend/tests/evaluation/test_retrieval_metrics.py`
- `backend/tests/evaluation/test_snapshot.py`
- `backend/tests/evaluation/test_runner.py`
- `backend/tests/evaluation/test_coordinator.py`
- `backend/tests/evaluation/test_costs.py`
- `backend/tests/test_evaluation_gate.py`
- `backend/tests/test_model_usage.py`

### Backend files to modify

- `backend/app/core/config.py`
- `backend/app/rag/generation/llm.py`
- `backend/app/rag/retrieval/query_rewriter.py`
- `backend/app/schemas/chat.py`
- `backend/app/evaluation/models.py`
- `backend/app/evaluation/case_loader.py`
- `backend/app/evaluation/judge.py`
- `backend/app/evaluation/faithfulness.py`
- `backend/app/evaluation/metrics_registry.py`
- `backend/app/evaluation/evaluator.py`
- `backend/app/evaluation/metrics.py`
- `backend/app/evaluation/gates.py`
- `backend/app/evaluation/comparison.py`
- `backend/app/evaluation/repository.py`
- `backend/app/evaluation/schemas.py`
- `backend/app/evaluation/service.py`
- `backend/app/api/routes_evaluation.py`
- `backend/app/main.py`
- `backend/tests/evaluation/test_api.py`
- Existing evaluation tests affected by the new result models.

### Frontend files to modify

- `frontend/src/features/evaluation/types.ts`
- `frontend/src/features/evaluation/api.ts`
- `frontend/src/features/evaluation/EvaluationCenter.vue`
- `frontend/src/features/evaluation/components/EvaluationOverview.vue`
- `frontend/src/features/evaluation/components/EvaluationRunDetail.vue`
- `frontend/src/features/evaluation/components/EvaluationComparePanel.vue`
- `frontend/src/features/evaluation/components/EvaluationRunsTable.vue`
- `frontend/src/features/evaluation/__tests__/api.test.ts`
- `frontend/src/features/evaluation/__tests__/EvaluationCenter.test.ts`

### Documentation files to modify

- `docs/evaluation/README.md`
- `.env.example`
- `RUN_COMMANDS.md`

---

### Task 1: DeepSeek Flash Non-Thinking Policy and Usage Capture

**Files:**
- Create: `backend/app/observability/model_usage.py`
- Create: `backend/tests/test_model_usage.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/rag/generation/llm.py`
- Modify: `backend/app/rag/retrieval/query_rewriter.py`
- Modify: `backend/app/evaluation/judge.py`
- Modify: `.env.example`
- Test: `backend/tests/test_config.py`
- Test: `backend/tests/test_evaluate.py`
- Test: `backend/tests/evaluation/test_judge.py`

**Interfaces:**
- Produces: `ModelUsageEvent`, `ModelUsageCollector`, `capture_model_usage()`, `record_model_usage()`.
- Produces: `JudgementCompletion(data: dict, usage: ModelUsageEvent | None)` from `JudgeProtocol.complete_json()`.
- Preserves: `DeepSeekClient.generate(question, contexts) -> str` and query rewriter public interfaces.

- [ ] **Step 1: Add failing tests for model policy and usage collection**

```python
def test_deepseek_payload_uses_flash_without_thinking(httpx_mock):
    httpx_mock.add_response(json={
        "choices": [{"message": {"content": "回答"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4, "prompt_cache_hit_tokens": 2},
    })
    client = DeepSeekClient("key", "https://api.deepseek.com", "deepseek-v4-flash")

    with capture_model_usage() as collector:
        assert client.generate("问题", ["资料"]) == "回答"

    request = httpx_mock.get_request()
    assert request.json()["model"] == "deepseek-v4-flash"
    assert request.json()["thinking"] == {"type": "disabled"}
    assert collector.events[0].prompt_tokens == 10
    assert collector.events[0].completion_tokens == 4
```

Also assert `Settings().deepseek_model` and `Settings().deepseek_judge_model` both equal `deepseek-v4-flash`, Judge payload requests JSON output, and usage outside a capture context is ignored.

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/test_model_usage.py tests/test_config.py \
  tests/evaluation/test_judge.py tests/test_evaluate.py -q
```

Expected: failures for missing collector, Judge completion type, non-thinking payload, and Flash Judge default.

- [ ] **Step 3: Implement the task-local usage collector**

```python
@dataclass(frozen=True)
class ModelUsageEvent:
    operation: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cache_hit_tokens: int = 0

_collector: ContextVar[ModelUsageCollector | None] = ContextVar("model_usage_collector", default=None)

@contextmanager
def capture_model_usage() -> Iterator[ModelUsageCollector]:
    collector = ModelUsageCollector()
    token = _collector.set(collector)
    try:
        yield collector
    finally:
        _collector.reset(token)
```

`record_model_usage()` must append only when a collector exists. Add a helper that safely extracts usage fields from the DeepSeek response.

- [ ] **Step 4: Update every direct DeepSeek request in scope**

For answer, streaming answer, query rewrite and Judge payloads:

```python
payload["model"] = "deepseek-v4-flash"
payload["thinking"] = {"type": "disabled"}
```

Use configured max outputs: answer `1200`, query rewrite `400`, Judge `1600`. Judge also sends:

```python
"response_format": {"type": "json_object"}
```

Change Judge protocol to return `JudgementCompletion`; update current faithfulness and tests to access `.data` without changing behavior yet.

- [ ] **Step 5: Run focused and regression tests**

Run:

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/test_model_usage.py tests/test_config.py tests/test_evaluate.py \
  tests/evaluation/test_judge.py tests/evaluation/test_faithfulness.py \
  tests/test_query_rewriter.py tests/test_llm.py -q
```

Expected: `tests/test_llm.py` and `tests/test_query_rewriter.py` pass together with the model usage, config and Judge tests.

- [ ] **Step 6: Commit the isolated model policy change**

```bash
git add .env.example backend/app/core/config.py backend/app/observability/model_usage.py \
  backend/app/rag/generation/llm.py backend/app/rag/retrieval/query_rewriter.py \
  backend/app/evaluation/judge.py backend/app/evaluation/faithfulness.py \
  backend/tests/test_model_usage.py backend/tests/test_config.py \
  backend/tests/test_evaluate.py backend/tests/evaluation/test_judge.py \
  backend/tests/evaluation/test_faithfulness.py
git commit -m "feat: standardize DeepSeek Flash evaluation calls"
```

### Task 2: Versioned Suite Schema and 20-Case Core Dataset

**Files:**
- Create: `backend/app/evaluation/suite.py`
- Create: `backend/evaluation_cases/core.v1.json`
- Create: `backend/tests/evaluation/test_suite.py`
- Modify: `backend/app/evaluation/case_loader.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/tests/evaluation/test_case_loader.py`

**Interfaces:**
- Produces: `EvaluationSuite`, `EvaluationCaseSpec`, `EvaluationTurnSpec`, `RequiredFact`, `EvaluationThresholds`.
- Produces: `load_evaluation_suite(path: Path) -> EvaluationSuite`.
- Produces: `suite_content_hash(suite: EvaluationSuite) -> str` using canonical JSON with sorted keys.
- Preserves: `load_evaluation_cases(path)` as a legacy compatibility adapter during migration.

- [ ] **Step 1: Write failing schema, hash, uniqueness and migration tests**

```python
def test_suite_rejects_duplicate_case_ids(tmp_path):
    payload = valid_suite_payload()
    payload["cases"] = [valid_case_payload("same"), valid_case_payload("same")]
    path = write_json(tmp_path / "suite.json", payload)
    with pytest.raises(ValueError, match="用例 ID 重复"):
        load_evaluation_suite(path)

def test_suite_hash_is_stable_for_equivalent_json(tmp_path):
    first = load_evaluation_suite(write_json(tmp_path / "a.json", valid_suite_payload()))
    second = load_evaluation_suite(write_json(tmp_path / "b.json", valid_suite_payload_reordered()))
    assert suite_content_hash(first) == suite_content_hash(second)
```

Also test: empty Suite rejected, P0 required fact list cannot be empty for answerable cases, no-answer cases may omit reference answer, IDs are non-empty, thresholds are within `[0, 1]`, and old keyword groups migrate to required facts but mark the case `legacy_unreviewed=True`.

- [ ] **Step 2: Run suite tests and verify failure**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_suite.py tests/evaluation/test_case_loader.py -q
```

Expected: import and validation failures because the Suite model does not exist.

- [ ] **Step 3: Implement strict Pydantic Suite models**

Use these exact core fields:

```python
class RequiredFact(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    required: bool = True

class EvaluationTurnSpec(BaseModel):
    question: str = Field(min_length=1)
    reference_answer: str = ""
    required_facts: list[RequiredFact] = Field(default_factory=list)
    keyword_anchors: list[str] = Field(default_factory=list)
    forbidden_facts: list[str] = Field(default_factory=list)
    expected_source_ids: list[str] = Field(default_factory=list)
    expected_chunk_ids: list[str] = Field(default_factory=list)
    forbidden_source_ids: list[str] = Field(default_factory=list)
    expect_no_answer: bool = False
    expect_images: bool = False
    min_sources: int = Field(default=0, ge=0)
    min_images: int = Field(default=0, ge=0)
```

Case supports either top-level single-turn fields or `turns`, normalizing both into `turns`. Suite validates unique IDs and non-empty cases.

- [ ] **Step 4: Build the 20 reviewed core cases**

Create these stable IDs and complete every case with reference answer, required facts and stable source IDs from the current manifest:

```text
single.editor.regions
single.client.os.requirements
single.editor.enter
single.toolbar.operations
single.collect.create
single.collect.create_and_run
single.data_project.start
single.collect.publish_deploy
dialog.collect.create_then_run
dialog.editor.enter_then_regions
dialog.collect.deploy_then_start
boundary.wechat.login
boundary.enterprise_wechat_dingtalk
boundary.unknown_product_feature
confusion.collect_vs_app_project
confusion.data_project_vs_collect_project
variant.collect.create_colloquial
variant.editor.enter_typo
safety.prompt_injection_ignore_manual
safety.request_internal_secret
```

For safety cases, expect a refusal or manual-only answer and include forbidden facts that would reveal system prompts, API keys or unsupported instructions. Mark the core workflow and security cases P0; mark language variants P1.

- [ ] **Step 5: Point settings to the versioned Suite and run validation**

Change `evaluation_cases_path` default to `backend/evaluation_cases/core.v1.json`. Keep dialogue path only for the legacy adapter; new Runner reads one Suite.

Run:

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_suite.py tests/evaluation/test_case_loader.py tests/test_config.py -q
```

Expected: all tests pass and `len(load_evaluation_suite(settings.evaluation_cases_path).cases) == 20`.

- [ ] **Step 6: Commit the Suite and dataset**

```bash
git add backend/app/evaluation/suite.py backend/app/evaluation/case_loader.py \
  backend/app/core/config.py backend/evaluation_cases/core.v1.json \
  backend/tests/evaluation/test_suite.py backend/tests/evaluation/test_case_loader.py \
  backend/tests/test_config.py
git commit -m "feat: add versioned core evaluation suite"
```

### Task 3: Generic Metrics, Answer Quality, Batch Faithfulness and Retrieval Metrics

**Files:**
- Create: `backend/app/evaluation/answer_quality.py`
- Create: `backend/app/evaluation/retrieval_metrics.py`
- Create: `backend/tests/evaluation/test_answer_quality.py`
- Create: `backend/tests/evaluation/test_retrieval_metrics.py`
- Modify: `backend/app/evaluation/models.py`
- Modify: `backend/app/evaluation/metrics_registry.py`
- Modify: `backend/app/evaluation/faithfulness.py`
- Modify: `backend/app/evaluation/evaluator.py`
- Modify: `backend/tests/evaluation/test_evaluator.py`
- Modify: `backend/tests/evaluation/test_faithfulness.py`
- Modify: `backend/tests/evaluation/test_metrics_registry.py`

**Interfaces:**
- Produces: `MetricStatus = PASSED | FAILED | ERROR | SKIPPED`.
- Produces: `MetricResult(name, score, status, threshold, details, elapsed_ms, token_usage, error_code)`.
- Produces: `evaluate_answer_quality(judge, turn, answer) -> list[MetricResult]`.
- Produces: `evaluate_retrieval(turn, sources) -> list[MetricResult]`.
- Changes: `evaluate_case(..., metrics: Sequence[str])` evaluates every configured metric instead of only `metrics[0]`.

- [ ] **Step 1: Write failing answer-quality and retrieval tests**

```python
def test_answer_quality_reports_missing_required_fact():
    judge = FakeJudge({
        "correctness": 0.75,
        "relevance": 1.0,
        "facts": [{"id": "entry", "covered": True}, {"id": "name", "covered": False}],
        "forbidden_fact_matches": [],
    })
    results = evaluate_answer_quality(judge, turn_spec(), "进入数采管理后创建工程。")
    coverage = metric_by_name(results, "required_fact_coverage")
    assert coverage.score == 0.5
    assert coverage.status == MetricStatus.FAILED
    assert coverage.details["missing_fact_ids"] == ["name"]

def test_retrieval_metrics_use_source_ids_not_keywords():
    results = evaluate_retrieval(turn_spec(expected_source_ids=["doc-a", "doc-b"]), sources("doc-x", "doc-b"))
    assert metric_by_name(results, "hit_at_k").score == 1.0
    assert metric_by_name(results, "recall_at_k").score == 0.5
    assert metric_by_name(results, "mrr").score == 0.5
```

Also test forbidden facts, P0 100% fact coverage, P1 80%, Judge malformed output -> ERROR, no-answer -> semantic SKIPPED, forbidden source match, and missing source IDs.

- [ ] **Step 2: Write failing batch-faithfulness tests**

The Fake Judge must receive one request and return:

```json
{
  "claims": [
    {"claim": "工程需要名称", "supported": true, "evidence": "填写名称"},
    {"claim": "工程自动运行", "supported": false, "evidence": ""}
  ]
}
```

Assert one Judge call, score `0.5`, complete claim details, and `ERROR` when any claim lacks a boolean `supported` field.

- [ ] **Step 3: Run focused metric tests and verify failure**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_answer_quality.py \
  tests/evaluation/test_retrieval_metrics.py \
  tests/evaluation/test_faithfulness.py \
  tests/evaluation/test_metrics_registry.py -q
```

Expected: missing modules/types and old per-claim Judge behavior.

- [ ] **Step 4: Implement generic MetricResult and answer-quality Judge**

The Judge prompt must request exact JSON keys `correctness`, `relevance`, `facts`, and `forbidden_fact_matches`. Validate scores within `[0, 1]`, verify returned fact IDs exactly match supplied IDs, and return `ERROR` with stable codes such as `judge_http_error`, `judge_invalid_json`, or `judge_schema_error`.

- [ ] **Step 5: Replace per-claim faithfulness with one batch request**

Keep the existing claim details shown by the frontend, but collapse claim splitting and support checking into one prompt. Preserve `None/SKIPPED` for valid refusal cases; return `ERROR` for answerable cases with missing contexts or unusable Judge output.

- [ ] **Step 6: Implement deterministic retrieval and hard-rule metrics**

Add stable `source_id` and `chunk_ids` to `SourceSnippet` in `backend/app/schemas/chat.py`, populated from retrieved chunks in `backend/app/rag/chain.py`. Match source/chunk IDs exactly; do not use path substrings for the new Suite.

For keyword anchors, change the evaluator to:

```python
answer_text = response.answer
matched, missing = _match_required_groups(answer_text, [[anchor] for anchor in turn.keyword_anchors])
```

Keep legacy path matching only inside the legacy adapter.

- [ ] **Step 7: Evaluate all requested metrics and calculate Case status**

Case status rules must exactly follow the design: hard rules all pass, correctness `>= 0.80`, P0 facts `== 1.0`, P1 facts `>= 0.80`, non-refusal faithfulness `>= 0.90`, P0 retrieval hit, no forbidden facts/sources, and no required metric `ERROR`.

Parse `settings.evaluation_metrics` as a comma-separated ordered tuple, validate every name through the registry before the Run starts, pass the full tuple from `EvaluationService` to `evaluate_case`, and iterate all names. Remove the current `metrics[0]` behavior.

- [ ] **Step 8: Run all evaluation metric tests**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest tests/evaluation -q
```

Expected: all evaluation tests pass; tests explicitly prove a semantically correct synonym does not fail merely because an old keyword is absent.

- [ ] **Step 9: Commit the metrics increment**

```bash
git add backend/app/evaluation backend/app/rag/chain.py backend/app/schemas/chat.py \
  backend/tests/evaluation
git commit -m "feat: add hybrid RAG evaluation metrics"
```

### Task 4: Run State, Absolute Gates and Approved-Baseline Comparison

**Files:**
- Modify: `backend/app/evaluation/models.py`
- Modify: `backend/app/evaluation/metrics.py`
- Modify: `backend/app/evaluation/gates.py`
- Modify: `backend/app/evaluation/comparison.py`
- Modify: `backend/tests/evaluation/test_models.py`
- Modify: `backend/tests/evaluation/test_metrics.py`
- Modify: `backend/tests/evaluation/test_gates.py`
- Modify: `backend/tests/evaluation/test_comparison.py`

**Interfaces:**
- Produces: `RunStatus(CREATED, RUNNING, SCORING, COMPLETED, INVALID, CANCELLED)`.
- Produces: `GateMode(CALIBRATION, BLOCKING)`.
- Produces: `GateDecision(outcome, absolute_reasons, regression_reasons, validity_reasons)`.
- Produces: `evaluate_run_validity(run)`, `evaluate_absolute_gate(summary, thresholds)`, `evaluate_regression_gate(current, baseline, thresholds)`.

- [ ] **Step 1: Write failing state transition and gate tests**

```python
@pytest.mark.parametrize("source,target", [
    (RunStatus.CREATED, RunStatus.RUNNING),
    (RunStatus.RUNNING, RunStatus.SCORING),
    (RunStatus.SCORING, RunStatus.COMPLETED),
    (RunStatus.RUNNING, RunStatus.INVALID),
    (RunStatus.RUNNING, RunStatus.CANCELLED),
])
def test_allowed_run_transitions(source, target):
    assert can_transition(source, target)

def test_run_is_invalid_when_judge_coverage_is_incomplete():
    decision = evaluate_run_validity(summary(case_total=20, completed=20, judge_coverage=0.95))
    assert decision.outcome == GateOutcome.INVALID
```

Also test `0/0` invalid, total pass rate 84% fails, one P0 failure fails, average faithfulness 89% fails, any P0 regression fails, new severe hallucination fails, pass-rate drop over 5pp fails, and P95 over `min(absolute_cap, baseline * 1.25)` fails.

- [ ] **Step 2: Run gate tests and verify failure**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_models.py tests/evaluation/test_metrics.py \
  tests/evaluation/test_gates.py tests/evaluation/test_comparison.py -q
```

Expected: failures for missing statuses, validity gate and baseline dimensions.

- [ ] **Step 3: Implement the explicit state machine and validity-first gate**

Define allowed transitions in one immutable mapping. `GateMode.CALIBRATION` still calculates quality failures but returns a non-blocking CLI result only after the Run is valid. Invalid calibration runs remain invalid.

- [ ] **Step 4: Extend summary and comparison data**

Summary must include completed/error counts, Judge coverage, average correctness, average fact coverage, average faithfulness, retrieval recall/MRR, single/dialogue P95, total Token and estimated cost. Comparison must include metric deltas and Case-level regression reasons, not only IDs.

- [ ] **Step 5: Run tests and commit**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_models.py tests/evaluation/test_metrics.py \
  tests/evaluation/test_gates.py tests/evaluation/test_comparison.py -q
```

Expected: all selected tests pass.

```bash
git add backend/app/evaluation/models.py backend/app/evaluation/metrics.py \
  backend/app/evaluation/gates.py backend/app/evaluation/comparison.py \
  backend/tests/evaluation/test_models.py backend/tests/evaluation/test_metrics.py \
  backend/tests/evaluation/test_gates.py backend/tests/evaluation/test_comparison.py
git commit -m "feat: add validity and baseline release gates"
```

### Task 5: Reproducible Snapshot, Generic Metric Storage and Immutable Baselines

**Files:**
- Create: `backend/app/evaluation/snapshot.py`
- Create: `backend/app/evaluation/costs.py`
- Create: `backend/tests/evaluation/test_snapshot.py`
- Create: `backend/tests/evaluation/test_costs.py`
- Modify: `backend/app/evaluation/repository.py`
- Modify: `backend/tests/evaluation/test_repository.py`
- Modify: `backend/tests/evaluation/test_repository_faithfulness.py`

**Interfaces:**
- Produces: `RunSnapshot` and `build_run_snapshot(settings, suite) -> RunSnapshot`.
- Produces: `estimate_deepseek_cost(events, rates) -> Decimal`.
- Repository produces: `create_run`, `transition_run`, `save_case_result`, `save_metric_results`, `finish_run`, `invalidate_run`, `request_cancel`, `approve_baseline`, `get_current_baseline`.

- [ ] **Step 1: Write failing snapshot and secret-filter tests**

```python
def test_snapshot_contains_versions_but_not_secrets(settings, suite):
    snapshot = build_run_snapshot(settings, suite)
    payload = snapshot.model_dump(mode="json")
    assert payload["suite_hash"]
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["thinking_enabled"] is False
    assert "api_key" not in json.dumps(payload).lower()
    assert settings.deepseek_api_key not in json.dumps(payload)
```

Mock Git and manifest reads to assert commit, dirty flag, index signature, prompt hashes, chunk size, overlap, top_k and dependency/runtime versions.

- [ ] **Step 2: Write failing repository migration and baseline tests**

Test that initialization upgrades an old three-table database without losing existing runs, creates `evaluation_metric_results` and `evaluation_baselines`, enables `PRAGMA foreign_keys=ON` and WAL, rejects empty runs, and prevents mutation of an approved baseline.

- [ ] **Step 3: Run storage tests and verify failure**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_snapshot.py tests/evaluation/test_costs.py \
  tests/evaluation/test_repository.py tests/evaluation/test_repository_faithfulness.py -q
```

Expected: missing snapshot/cost modules and missing tables/methods.

- [ ] **Step 4: Implement additive SQLite migration**

Add run columns for status, mode, Suite ID/version/hash, snapshot JSON, completed/error counts, metric summaries, token totals, cost, cancel flag and timestamps. Add generic metric and baseline tables. Use additive `ALTER TABLE` migration for existing DBs; never drop current tables or columns.

- [ ] **Step 5: Implement checkpoint-oriented repository methods**

Each Case and its metrics must save in one transaction. Run transitions validate the state machine. On repository initialization, any old `RUNNING/SCORING` row whose process ownership is gone is marked `INVALID` with error code `process_interrupted`.

- [ ] **Step 6: Implement cost estimation**

Store price rates in the Run snapshot. Use `Decimal`, distinguish cache-hit input, cache-miss input and output Tokens, and quantize the displayed RMB cost to four decimal places.

- [ ] **Step 7: Run tests and commit**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_snapshot.py tests/evaluation/test_costs.py \
  tests/evaluation/test_repository.py tests/evaluation/test_repository_faithfulness.py -q
```

Expected: all selected tests pass and old fixture DB data remains readable.

```bash
git add backend/app/evaluation/snapshot.py backend/app/evaluation/costs.py \
  backend/app/evaluation/repository.py backend/tests/evaluation/test_snapshot.py \
  backend/tests/evaluation/test_costs.py backend/tests/evaluation/test_repository.py \
  backend/tests/evaluation/test_repository_faithfulness.py
git commit -m "feat: persist reproducible evaluation runs"
```

### Task 6: Trusted Runner and Single-Run Coordinator

**Files:**
- Create: `backend/app/evaluation/runner.py`
- Create: `backend/app/evaluation/coordinator.py`
- Create: `backend/tests/evaluation/test_runner.py`
- Create: `backend/tests/evaluation/test_coordinator.py`
- Modify: `backend/app/evaluation/service.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/evaluation/test_service.py`

**Interfaces:**
- Produces: `EvaluationRunner.run(run_id: str, suite: EvaluationSuite, mode: GateMode, cancel: Event) -> EvaluationRunDetail`.
- Produces: `EvaluationCoordinator.start(suite_id, mode) -> run_id`, `cancel(run_id) -> bool`, `shutdown()`.
- Service produces: `create_run`, `cancel_run`, `get_run`, `approve_baseline`, `compare_to_baseline`.

- [ ] **Step 1: Write failing Runner lifecycle tests**

```python
def test_runner_checkpoints_each_case_and_completes(valid_dependencies):
    run_id = valid_dependencies.repository.create_run(...)
    detail = valid_dependencies.runner.run(run_id, core_suite(two_cases=True), GateMode.CALIBRATION, Event())
    assert detail.summary.status == RunStatus.COMPLETED
    assert valid_dependencies.repository.get_run(run_id).summary.completed_case_count == 2

def test_runner_marks_invalid_when_judge_errors(valid_dependencies):
    valid_dependencies.judge.fail_with(JudgementError("timeout"))
    detail = valid_dependencies.runner.run(...)
    assert detail.summary.status == RunStatus.INVALID
    assert detail.gate_result.validity_reasons
```

Also test cancellation after a Case checkpoint, RAG failure continues remaining Cases but final Run is invalid, empty Suite rejected before chain creation, and usage events are attached to the correct Case.

- [ ] **Step 2: Write failing coordinator concurrency tests**

Assert first Run starts, second active Run request returns a conflict, cancellation sets the event, completed Run releases the lock, and app shutdown stops the executor without abandoning a new task.

- [ ] **Step 3: Run focused tests and verify failure**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_runner.py tests/evaluation/test_coordinator.py \
  tests/evaluation/test_service.py -q
```

Expected: missing Runner and coordinator.

- [ ] **Step 4: Implement Runner orchestration**

Sequence per Run:

```text
create snapshot -> CREATED/RUNNING -> for each Case: capture usage, execute RAG,
evaluate metrics, save checkpoint -> SCORING -> validity -> absolute gate ->
baseline gate -> COMPLETED or INVALID
```

Check cancellation before starting each Case and immediately after each checkpoint. Never derive final scores from request payloads.

- [ ] **Step 5: Implement one-worker coordinator and app lifecycle**

Use `ThreadPoolExecutor(max_workers=1)` and a guarded active Run record. Initialize it in FastAPI lifespan, expose it through service construction, and call `shutdown(wait=False, cancel_futures=True)` on app shutdown.

- [ ] **Step 6: Remove progressive scoring from the new service path**

Keep legacy conversion methods only for compatibility tests, mark them deprecated in code, and ensure the new `create_run` never invokes `save_case_results`.

- [ ] **Step 7: Run tests and commit**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/evaluation/test_runner.py tests/evaluation/test_coordinator.py \
  tests/evaluation/test_service.py tests/evaluation/test_service_faithfulness.py -q
```

Expected: all selected tests pass.

```bash
git add backend/app/evaluation/runner.py backend/app/evaluation/coordinator.py \
  backend/app/evaluation/service.py backend/app/main.py \
  backend/tests/evaluation/test_runner.py backend/tests/evaluation/test_coordinator.py \
  backend/tests/evaluation/test_service.py backend/tests/evaluation/test_service_faithfulness.py
git commit -m "feat: run evaluations on the trusted backend"
```

### Task 7: Run, Cancel, Baseline and Comparison API

**Files:**
- Modify: `backend/app/evaluation/schemas.py`
- Modify: `backend/app/api/routes_evaluation.py`
- Modify: `backend/tests/evaluation/test_api.py`

**Interfaces:**
- `POST /api/evaluation/runs` accepts `{suite_id, mode}` and returns `202` plus Run summary.
- `POST /api/evaluation/runs/{run_id}/cancel` returns updated Run or `409` for a terminal Run.
- `POST /api/evaluation/runs/{run_id}/approve-baseline` accepts `{approved_by, note}`.
- `GET /api/evaluation/baselines` lists immutable approvals.
- `GET /api/evaluation/runs/{run_id}/compare` defaults to the approved Suite baseline.

- [ ] **Step 1: Replace API tests with the trusted execution contract**

```python
def test_create_run_returns_202_and_does_not_accept_case_results(client):
    response = client.post("/api/evaluation/runs", json={"suite_id": "core", "mode": "calibration"})
    assert response.status_code == 202
    assert response.json()["status"] in {"created", "running"}

def test_empty_progressive_upload_is_not_a_supported_new_flow(client):
    response = client.post("/api/evaluation/runs/progressive", json={"case_results": [], "config": {}})
    assert response.status_code in {400, 410}
```

Add tests for list Suite, cancel, active Run conflict `409`, invalid baseline approval `422`, successful approval, current baseline listing and approved-baseline comparison.

- [ ] **Step 2: Run API tests and verify failure**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest tests/evaluation/test_api.py -q
```

Expected: old synchronous/progressive contract causes failures.

- [ ] **Step 3: Implement strict request/response schemas**

Use enums for mode and status. `approved_by` is required, trimmed, length 1-100; note max 500. Validate run list limit between 1 and 100. Return stable errors for `run_not_found`, `run_conflict`, `run_not_terminal`, `run_invalid`, and `suite_mismatch`.

- [ ] **Step 4: Implement routes and deprecate progressive endpoint**

The progressive endpoint must no longer save client scores. During the compatibility window return HTTP `410 Gone` with a migration message; remove it from the frontend in Task 9.

- [ ] **Step 5: Run API and backend evaluation tests**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest tests/evaluation -q
```

Expected: all evaluation tests pass.

- [ ] **Step 6: Commit API changes**

```bash
git add backend/app/evaluation/schemas.py backend/app/api/routes_evaluation.py \
  backend/tests/evaluation/test_api.py
git commit -m "feat: expose trusted evaluation run APIs"
```

### Task 8: Local Calibration and Blocking CLI

**Files:**
- Create: `backend/scripts/evaluation_gate.py`
- Create: `backend/tests/test_evaluation_gate.py`
- Modify: `backend/scripts/evaluate.py`

**Interfaces:**
- Produces: `main(argv: Sequence[str] | None = None) -> int`.
- CLI flags: `--suite core`, `--mode calibration|blocking`, `--output PATH`, `--approved-by NAME` only when approving via a separate explicit flag.
- Exit codes: `0` valid calibration or passed blocking, `1` valid quality failure, `2` invalid/config/infrastructure failure.

- [ ] **Step 1: Write failing CLI exit-code and report tests**

```python
@pytest.mark.parametrize((mode, status, gate_passed, expected), [
    ("calibration", "completed", False, 0),
    ("blocking", "completed", True, 0),
    ("blocking", "completed", False, 1),
    ("blocking", "invalid", False, 2),
])
def test_gate_exit_codes(fake_runner, mode, status, gate_passed, expected):
    fake_runner.result(status=status, gate_passed=gate_passed)
    assert main(["--suite", "core", "--mode", mode]) == expected
```

Also test JSON report creation, printed Run ID/Suite/baseline/failures, missing baseline in blocking mode -> `2`, and no secret values in output.

- [ ] **Step 2: Run CLI tests and verify failure**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest tests/test_evaluation_gate.py -q
```

Expected: missing module.

- [ ] **Step 3: Implement CLI as a thin Runner adapter**

Do not call HTTP. Build the same repository, Suite loader, chain, Judge and Runner used by the service. Print concise progress per Case, then absolute gate, regression gate, Token/cost and report path.

- [ ] **Step 4: Turn the old evaluate script into a compatibility shim**

Print a deprecation message and delegate to `evaluation_gate.main()` when invoked without `--file`. Keep `load_eval_questions`, `evaluate_question`, `summarize_results`, `build_evaluation_report` and `write_json_report` through Task 10 because `backend/tests/test_evaluate.py` directly tests those helpers. The `--file` path remains the explicit legacy path during一期兼容期。

- [ ] **Step 5: Run CLI and evaluation tests**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest \
  tests/test_evaluation_gate.py tests/test_evaluate.py tests/evaluation -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit CLI**

```bash
git add backend/scripts/evaluation_gate.py backend/scripts/evaluate.py \
  backend/tests/test_evaluation_gate.py backend/tests/test_evaluate.py
git commit -m "feat: add local RAG release gate command"
```

### Task 9: Frontend Run Polling, Failure Semantics and Baseline Approval

**Files:**
- Modify: `frontend/src/features/evaluation/types.ts`
- Modify: `frontend/src/features/evaluation/api.ts`
- Modify: `frontend/src/features/evaluation/EvaluationCenter.vue`
- Modify: `frontend/src/features/evaluation/components/EvaluationOverview.vue`
- Modify: `frontend/src/features/evaluation/components/EvaluationRunDetail.vue`
- Modify: `frontend/src/features/evaluation/components/EvaluationComparePanel.vue`
- Modify: `frontend/src/features/evaluation/components/EvaluationRunsTable.vue`
- Modify: `frontend/src/features/evaluation/__tests__/api.test.ts`
- Modify: `frontend/src/features/evaluation/__tests__/EvaluationCenter.test.ts`

**Interfaces:**
- API client produces: `listSuites`, `createRun`, `getRun`, `cancelRun`, `listBaselines`, `approveBaseline`, `compareRun`.
- Removes from active client usage: `runEvaluationCase`, `saveProgressiveRun`.
- UI polling interval: 1000 ms while status is CREATED/RUNNING/SCORING; stop on terminal status or component unmount.

- [ ] **Step 1: Write failing API client tests**

Assert `createRun` sends `{suite_id: "core", mode: "calibration"}`, cancel and approve use the correct endpoints, and no client method sends Case results to `/runs/progressive`.

- [ ] **Step 2: Rewrite component tests around backend-owned runs**

```typescript
it("creates a backend run and polls until completed", async () => {
  vi.useFakeTimers();
  const client = createFakeClient();
  client.createRun.mockResolvedValue(run("run-2", "created"));
  client.getEvaluationRun
    .mockResolvedValueOnce(detail("run-2", "running"))
    .mockResolvedValueOnce(detail("run-2", "completed"));

  const wrapper = mount(EvaluationCenter, { props: { client } });
  await wrapper.get('[data-testid="run-evaluation"]').trigger("click");
  await vi.advanceTimersByTimeAsync(2000);

  expect(client.createRun).toHaveBeenCalledWith({ suite_id: "core", mode: "calibration" });
  expect(client.saveProgressiveRun).toBeUndefined();
  expect(wrapper.text()).toContain("COMPLETED");
});
```

Add tests for cancel, INVALID vs FAILED copy, null faithfulness displays `未评估`, baseline approval only for valid completed calibration Run, polling cleanup on unmount, and approved-baseline comparison.

- [ ] **Step 3: Run frontend tests and verify failure**

```bash
cd frontend
npm test -- --run src/features/evaluation/__tests__/api.test.ts \
  src/features/evaluation/__tests__/EvaluationCenter.test.ts
```

Expected: old progressive API and local loop assertions fail.

- [ ] **Step 4: Update frontend types and API**

Model exact statuses, Gate mode/outcome, generic metric results, snapshots, baselines, token/cost summary and comparison reasons. Keep optional fields only for legacy history rows.

- [ ] **Step 5: Replace the local Case loop with Run polling**

Create one Run, show backend-provided Case states, use cancel endpoint, and stop polling on terminal status/unmount. Do not calculate pass rate or gate result in the browser.

- [ ] **Step 6: Update report and overview presentation**

Display five primary values: Run outcome, Case pass rate, P0, average faithfulness or `未评估`, and P95. In details, group metrics by hard rule, answer quality, faithfulness, retrieval and system; render ERROR separately from quality failures. Show snapshot and baseline identity in a collapsible section.

- [ ] **Step 7: Add baseline approval flow**

Use a small modal with required approver name and optional note. Disable approval unless the Run is valid, completed, calibration mode and current Suite matches. Refresh baselines and comparison after approval.

- [ ] **Step 8: Run frontend tests and build**

```bash
cd frontend
npm test -- --run src/features/evaluation/__tests__/api.test.ts \
  src/features/evaluation/__tests__/EvaluationCenter.test.ts
npm run build
```

Expected: Vitest and `vue-tsc`/Vite build pass.

- [ ] **Step 9: Commit frontend changes**

```bash
git add frontend/src/features/evaluation
git commit -m "feat: connect evaluation UI to trusted runs"
```

### Task 10: Documentation, Full Verification and Calibration Handoff

**Files:**
- Modify: `docs/evaluation/README.md`
- Modify: `RUN_COMMANDS.md`
- Modify: `.env.example`
- Modify: evaluation tests only if verification exposes a real defect.

**Interfaces:**
- Documents the exact local calibration/blocking commands, exit codes, baseline workflow, thresholds, Run status semantics and troubleshooting.
- Produces a first calibration report under `storage/reports/` without committing generated reports or secrets.

- [ ] **Step 1: Update operator documentation**

Document this workflow exactly:

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m scripts.evaluation_gate \
  --suite core \
  --mode calibration \
  --output ../storage/reports/core-calibration.json
```

Explain exit codes `0/1/2`, how to approve a baseline in the UI, how blocking mode differs, why INVALID is not a quality failure, and how to inspect Judge errors without exposing prompts or keys.

- [ ] **Step 2: Run the complete backend test suite**

```bash
cd backend
conda run -n kf-rag --no-capture-output python -m pytest -q
```

Expected: all tests pass. Record the exact count in the implementation handoff.

- [ ] **Step 3: Run the complete frontend test/build suite**

```bash
cd frontend
npm test
npm run build
```

Expected: all tests and type/build checks pass.

- [ ] **Step 4: Run static repository checks**

```bash
git diff --check
rg -n "deepseek-v4-pro|deepseek-chat|deepseek-reasoner" backend .env.example
rg -n "saveProgressiveRun|/runs/progressive" frontend/src/features/evaluation
```

Expected: no whitespace errors; no active Pro/legacy model references; no active frontend progressive scoring references. Historical docs/tests may mention deprecated endpoints only when explicitly labeled.

- [ ] **Step 5: Start backend and frontend for a manual smoke test**

Backend:

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Verify: create calibration Run, observe status polling, cancel one test Run, complete one Run, inspect INVALID/FAILED copy, approve a valid baseline, and compare a later Run to it.

- [ ] **Step 6: Execute the first real calibration Run**

Run the documented CLI once with the real DeepSeek key. Check that it executes exactly 20 Cases, Judge coverage is 100%, all calls use Flash non-thinking mode, no Run is saved as `0/0`, and the JSON report contains snapshot, Token and cost data without secrets.

Do not approve a baseline if the Run is INVALID or if manual review finds Judge misclassification. Record each disputed Case ID and revise its rubric or Judge prompt in a new focused commit before rerunning.

- [ ] **Step 7: Complete 3-5 calibration samples and approve the baseline**

Repeat the same Suite without code/config changes until at least three valid reports exist. Compare Case outcomes and semantic scores. Approve the most representative valid Run only when P0 judgments are manually accepted and score variation does not cross current thresholds unpredictably.

- [ ] **Step 8: Verify blocking exit codes against approved baseline**

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m scripts.evaluation_gate \
  --suite core \
  --mode blocking \
  --output ../storage/reports/core-blocking.json
echo $?
```

Expected: `0` only when the valid Run passes both absolute and baseline gates; `1` for real quality failure; `2` for invalid execution.

- [ ] **Step 9: Commit documentation and any calibration-derived rubric corrections**

```bash
git add docs/evaluation/README.md RUN_COMMANDS.md .env.example \
  backend/evaluation_cases/core.v1.json
git commit -m "docs: add RAG evaluation gate operations"
```

- [ ] **Step 10: Produce final implementation handoff**

Report commits, changed modules, backend/frontend test counts, build result, calibration Run IDs, approved baseline Run ID, observed Token/cost range, remaining failed Cases and the exact command for future release checks. Do not claim enterprise release readiness until a valid baseline has been approved and blocking mode has returned the expected exit code.
