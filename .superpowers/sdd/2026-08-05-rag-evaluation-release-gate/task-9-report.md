# Task 9 Report: Frontend Run Polling, Failure Semantics and Baseline Approval

## What I implemented

- Replaced the frontend's local per-case execution and progressive score upload with a trusted run lifecycle client: `listSuites`, `createRun`, `getRun`, `cancelRun`, `listBaselines`, `approveBaseline`, and `compareRun`.
- Added typed run statuses, gate outcomes/modes, metric results, snapshots, baseline approvals, token/cost summary fields, and comparison reasons.
- Updated `EvaluationCenter` to create one calibration Run and poll its detail every 1000 ms only while the backend status is `created`, `running`, or `scoring`. Polling stops on terminal states, cancellation, and unmount.
- Added backend-owned cancellation, approved-baseline comparison, and a modal baseline approval flow requiring an approver name with an optional note.
- Made approval unavailable unless the selected Run is completed, calibration mode, and belongs to the current Suite.
- Updated presentation to use backend outcomes, distinguish `INVALID` (shown as `无效`) from `FAILED` (shown as `质量未通过`), render null faithfulness as `未评估`, retain exactly five overview values, render metric `ERROR` distinctly, and expose snapshot/baseline identity in a collapsible section.

## Tests and results

- `PATH="$HOME/.nvm/versions/node/v22.14.0/bin:$PATH" npm test -- --run src/features/evaluation/__tests__/api.test.ts src/features/evaluation/__tests__/EvaluationCenter.test.ts`
  - `2 passed`, `8 passed`.
- `PATH="$HOME/.nvm/versions/node/v22.14.0/bin:$PATH" npm run build`
  - `vue-tsc --noEmit` and Vite production build passed.
- `git diff --check`
  - Passed.

## TDD Evidence

### RED

Command:

```bash
cd frontend
PATH="$HOME/.nvm/versions/node/v22.14.0/bin:$PATH" npm test -- --run \
  src/features/evaluation/__tests__/api.test.ts \
  src/features/evaluation/__tests__/EvaluationCenter.test.ts
```

Output: `8 failed`. API tests failed with `client.createRun is not a function`, `client.cancelRun is not a function`, and `client.getRun is not a function`. Component tests failed because the center still called `listEvaluationCases` and `saveProgressiveRun`, proving the legacy progressive flow remained active.

The default `npm` Node binary initially failed to load ICU 73 before Vitest could start. Re-running with the existing Node 22.14.0 runtime allowed the intended RED failures to execute.

### GREEN

Command:

```bash
cd frontend
PATH="$HOME/.nvm/versions/node/v22.14.0/bin:$PATH" npm test -- --run \
  src/features/evaluation/__tests__/api.test.ts \
  src/features/evaluation/__tests__/EvaluationCenter.test.ts
PATH="$HOME/.nvm/versions/node/v22.14.0/bin:$PATH" npm run build
```

Output: `2 passed`, `8 passed`; `vue-tsc --noEmit` and Vite build passed.

## Files changed

- `frontend/src/features/evaluation/types.ts`
- `frontend/src/features/evaluation/api.ts`
- `frontend/src/features/evaluation/EvaluationCenter.vue`
- `frontend/src/features/evaluation/components/EvaluationOverview.vue`
- `frontend/src/features/evaluation/components/EvaluationRunDetail.vue`
- `frontend/src/features/evaluation/components/EvaluationComparePanel.vue`
- `frontend/src/features/evaluation/components/EvaluationRunsTable.vue`
- `frontend/src/features/evaluation/__tests__/api.test.ts`
- `frontend/src/features/evaluation/__tests__/EvaluationCenter.test.ts`
- `.superpowers/sdd/2026-08-05-rag-evaluation-release-gate/task-9-report.md`

## Self-review findings

- Confirmed no production code in `frontend/src/features/evaluation` references `runEvaluationCase`, `saveProgressiveRun`, `/runs/progressive`, or a browser-calculated final pass rate/gate decision.
- Confirmed polling uses a single timeout, only schedules while active, clears on replacement/cancel, and clears during unmount.
- Confirmed the focused tests cover creation/poll completion, cancellation, INVALID versus FAILED copy, null faithfulness, approval eligibility, approval refresh behavior, approved-baseline comparison, and unmount cleanup.

## Concerns

- The current backend detail/summary schemas in this checkout do not serialize Suite/mode/snapshot fields. The frontend retains trusted Suite/mode metadata for runs created in the current browser session, but persisted historical runs remain conservatively unavailable for approval until that metadata is exposed by the backend.
- The system-default Node executable is linked to a missing ICU 73 library. Verification used the installed Node 22.14.0 runtime explicitly.
