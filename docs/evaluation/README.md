# KingIAsk RAG Trusted Evaluation Gate

The evaluation center is the local release gate for KingIAsk RAG. A trusted Run executes the versioned `core` Suite on the backend, records its configuration and index snapshot, scores returned answers, and persists an auditable result. Browser clients create and inspect Runs; they never submit scores.

## What the gate evaluates

`backend/evaluation_cases/core.v1.json` is the versioned `core` Suite. It contains 20 manually reviewed Cases, including P0 workflows, multi-turn context, refusal boundaries, source expectations, and retrieval checks.

Each trusted Run stores its Suite hash, index/configuration snapshot, Case results, Judge coverage, token usage, and estimated cost in `storage/evaluation/kingiask_eval.db`. CLI JSON reports are written under `storage/reports/`; do not commit reports, databases, or `.env` files.

## Local calibration

From the repository root, configure `DEEPSEEK_API_KEY` in the untracked `.env`, ensure the intended index is present, then run exactly:

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m scripts.evaluation_gate \
  --suite core \
  --mode calibration \
  --output ../storage/reports/core-calibration.json
```

After the Run is successfully created and finalized, calibration executes the full Suite and writes the report. It returns `0` when execution is valid even if quality thresholds are not met; use it to collect comparable samples and investigate failures. It returns `2` for an invalid execution, such as incomplete Case completion, Judge errors or missing Judge metrics, incomplete Judge coverage, cancellation, or an unavailable/misconfigured dependency. If startup or finalization fails before report creation, capture the Run ID, timestamp, and exception type in safe local diagnostic logging; never log prompts, API keys, or authorization headers.

Run the same command three to five times with no code, index, or configuration changes. Review Case outcomes and semantic scores together. Do not approve a baseline when a Run is `INVALID`, when any P0 judgment is disputed, or when score variation crosses thresholds unpredictably. Record disputed Case IDs, correct the rubric or Judge prompt in a focused change, and rerun calibration before approval.

## Baseline approval and blocking

In the evaluation center, select a valid completed calibration Run, choose **批准基准**, enter the approver name and an optional review note, and confirm. The recorded baseline is immutable; the latest approved baseline for the Suite is used for comparisons. Approval is an operator decision after manual review, not a shortcut around the gate.

After a valid baseline is approved, run the release check:

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m scripts.evaluation_gate \
  --suite core \
  --mode blocking \
  --output ../storage/reports/core-blocking.json
echo $?
```

Blocking mode requires an approved baseline. Its exit codes are:

| Exit code | Meaning | Operator action |
| --- | --- | --- |
| `0` | The Run is valid and passes absolute and baseline-regression gates. | The release check passed. Preserve the report with release evidence outside Git if required. |
| `1` | A valid Run has a real quality failure. | Inspect failed Cases and gate reasons; do not release until resolved or deliberately recalibrated. |
| `2` | Execution is invalid or cannot be evaluated reliably. | Fix the operational/configuration issue and rerun. A missing approved baseline also returns `2`. |

`INVALID` is not a quality failure: it means the system lacks enough valid evidence to make a quality decision. It can result from cancellation, an interrupted Run, incomplete `completed_count/case_total`, Judge coverage below 100%, missing Judge metrics, or metric errors. Treat it as an execution/reliability problem and rerun only after resolving the cause.

## Current thresholds

For the `core` Suite, absolute blocking checks require:

- Pass rate at least `85%`.
- Every P0 Case passes.
- Average answer-correctness score at least `80%`.
- Average required-fact coverage at least `80%`.
- Average faithfulness score at least `90%`.
- P95 latency no greater than `30000ms`.

Compared with the approved baseline, blocking also rejects a newly regressed P0 Case, a newly introduced severe hallucination, pass-rate decline greater than `5` percentage points, or P95 latency above the lower of `125%` of baseline P95 and `30000ms`.

## Run status semantics

| Status | Meaning |
| --- | --- |
| `created` | The Run was persisted and is waiting for backend execution. |
| `running` | Cases are executing. The UI polls this Run. |
| `scoring` | Case execution finished and metrics/Judge results are being finalized. |
| `completed` | The Run reached a terminal state with results. It can still be a blocking quality failure; inspect the gate outcome. |
| `INVALID` | The Run is terminal but insufficiently valid for a quality verdict. |
| `cancelled` | The operator requested cancellation while it was active. It is terminal and not a baseline candidate. |

`PASSED`, `FAILED`, and `INVALID` are gate outcomes. `FAILED` means a valid Run missed an absolute or regression threshold; it is distinct from the `INVALID` Run status.

## Inspecting failures safely

Select a Run in the UI and inspect its Case-level failure reasons, metric statuses, gate reasons, comparison, snapshot, token count, and estimated cost. Judge failures appear as metric status `ERROR` with an error code such as `judge_unavailable`; use that code, the Run ID, status, and timestamp to correlate server-side logs.

Do not copy or expose Judge system/user prompts, answer payloads containing sensitive content, `DEEPSEEK_API_KEY`, `Authorization` headers, or `.env` values into tickets, reports, or commits. The CLI JSON report contains only the release decision, failed Case IDs, token count, cost, and snapshot metadata, not credentials.

## Troubleshooting

- `2` before execution in blocking mode: approve a valid completed calibration Run for the same Suite, then rerun blocking mode.
- `INVALID` with Judge errors or incomplete coverage: verify the DeepSeek key, network reachability, Flash configuration, and service logs; do not treat it as a score regression.
- `0/0`, missing Cases, or an unexpected Suite: confirm `EVALUATION_CASES_PATH=backend/evaluation_cases/core.v1.json`, rebuild the intended index, and rerun from `backend` with the command above.
- A Run remains active after a backend restart: refresh the evaluation center. Interrupted active Runs are invalidated during repository initialization; create a fresh Run rather than approving it.
- Baseline comparison is unavailable: verify that the current Run and approved baseline use the same Suite, then inspect the baseline list.

## Manual smoke checklist

Start the backend and frontend in separate terminals:

```bash
cd backend
conda run -n kf-rag --no-capture-output \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm run dev
```

In the browser, create a calibration Run, confirm status polling, cancel a separate active test Run, let one Run complete, inspect the `INVALID`/`FAILED` copy and Judge errors, approve only a manually accepted valid calibration Run, then compare a later Run against it.

## Required release command

For every future local release check, use the blocking command in this document after an approved valid baseline exists. Do not claim release readiness solely from unit tests, a calibration `0`, or a `completed` status; readiness requires a valid approved baseline and a blocking Run returning `0`.
