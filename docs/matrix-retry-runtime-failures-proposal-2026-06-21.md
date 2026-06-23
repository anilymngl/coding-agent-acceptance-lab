# Matrix Retry: Runtime-Failure-Only Resume

## Status

Proposal — not implemented.

## Problem

`ci-vibe-matrix run --resume` skips **all** stored rows regardless of outcome.
A `no_output_timeout` (harness killed the run before first output) is stored and
then skipped forever. The only ways to retry runtime failures today are:

- Manually `DELETE` failing rows from SQLite, then `--resume`
- Run without `--resume` (re-runs everything, wastes API tokens, blasts rate
  limits)
- Bump timeouts and hope

None of these preserve the "collect all attempt data" goal cleanly. The user
wants: *keep stored semantic results, retry only runtime-failure rows, don't
re-run successes*.

## Current Row Classification

Already implemented in `ci_vibe_lab/matrix.py:502-543`. Every row is classified
into one of these outcomes via `classify_row()`:

| Outcome | `exit_code` | `opencode_stdout` | Meaning |
|---|---|---|---|
| `hidden_pass` | 0 | non-empty | public=1, hidden=1 |
| `false_green` | 0 | non-empty | public=1, hidden=0 |
| `public_red` | 0 | non-empty | public=0, hidden=0 |
| `agent_timeout` | 124 | non-empty | model working, hit wall clock |
| `no_output_timeout` | 124 | empty | harness killed before first token |
| `provider_or_config_error` | non-zero | contains provider error markers | API/auth/config failure |
| `runner_error` | non-zero | empty or no patch | harness-level failure |

`is_runtime_failure_outcome()` (`matrix.py:537`) returns `True` for the bottom
four outcomes. `is_completed_outcome()` (`matrix.py:533`) returns `True` for
the top three.

## Proposed Subcommand

```
ci-vibe-matrix retry CONFIG
```

### Behavior

1. For each cell in the matrix config, load rows from the cell DB.
2. Run `classify_row()` on every row.
3. Filter rows where `is_runtime_failure_outcome(outcome) is True`.
4. `DELETE FROM runs WHERE id IN (retriable_ids)`.
5. Print a summary: "Cell X/Y: deleted N runtime-failure rows, keeping M
   completed rows."
6. Run `ci-vibe-matrix run --resume CONFIG` (same process as today's
   `--resume`, now targeting only the gaps left by deleted rows).

### Flags

- `--dry-run` — print what would be deleted, don't modify DBs.
- `--only-model MODEL` — scope to one model alias.
- `--only-pack PACK` — scope to one pack.
- `--only-prompt-mode MODE` — scope to one prompt mode.

### Safety

- Only deletes rows classified as runtime failures by the existing, tested
  `classify_row()` function.
- Semantic evidence (`hidden_pass`, `false_green`, `public_red`) is
  never touched.
- `--dry-run` shows the delete plan before execution.
- The matrix report already handles mixed-status cells; after retry it
  just sees fewer runtime failures and more completed rows.

## Why This Over Alternatives

| Approach | Keeps Semantic Data | Skips Completed | No Manual SQL |
|---|---|---|---|
| `--resume` today | yes | also skips failures | yes |
| Fresh run (no `--resume`) | yes (duplicate rows) | no | yes |
| Manual `DELETE` + `--resume` | yes | yes | no |
| **`ci-vibe-matrix retry`** | **yes** | **yes** | **yes** |

## Implementation Plan

1. Add `retry` subcommand to `ci-vibe-matrix` CLI in `ci_vibe_lab/matrix.py`.
2. Implement `_retry_cell()` using existing `classify_row()` and
   `is_runtime_failure_outcome()`.
3. After deletions, call `run_cells()` with `resume=True`.
4. Add tests in `tests/` for the new subcommand.

## Scope

- Affects: `ci_vibe_lab/matrix.py` (new subcommand, ~40 lines).
- Touches: no schema changes, no runner changes, no report changes.
- Config format: unchanged.
- DB format: unchanged (just fewer rows after `DELETE`).

## Related

- `ci_vibe_lab/matrix.py:502-543` — existing classification
- `ci_vibe_lab/matrix.py:858-884` — existing `run`/`plan` argument setup
- `ci_vibe_lab/runner.py:504-534` — existing `--resume`/`--skip-timeouts` logic
