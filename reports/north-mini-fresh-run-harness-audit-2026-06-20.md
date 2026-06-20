# North Mini Fresh Run Harness Audit

Date: 2026-06-20

## Executive State

This is not the final North Mini capability report. It is the fresh-run harness audit that explains why the full two-lane run should not be interpreted yet.

The harness itself found a real issue in the run environment: after an initial burst of normal OpenCode executions, later OpenCode calls began producing no stdout/stderr and timing out. I added two harness controls before continuing:

- Immediate progress flushing, so the runner no longer appears silent while work is happening.
- `--first-output-timeout`, so a no-stream OpenCode/model stall is recorded quickly and explicitly.
- `--delay-seconds`, so future batches can avoid unpaced provider/CLI bursts.

The useful capability signal from the fresh sparse maintenance run is the subset with `opencode_exit_code=0`. On those completed attempts, North Mini produced public-green patches every time, but missed two visible semantic contracts.

## Data Sources

Fresh DBs:

- `data/fresh-2026-06-20-north-mini-sparse.sqlite`
- `data/fresh-2026-06-20-north-mini-contract.sqlite`

Fresh artifact roots:

- `runs/fresh-2026-06-20/north-mini/sparse/artifacts/`
- `runs/fresh-2026-06-20/north-mini/contract-visible/artifacts/`

Code/harness commits in this slice:

- `7c232ac fix: flush eval runner progress`
- `34ad44b feat: pace eval runner attempts`
- `cfd38ee fix: fail stalled opencode attempts early`

Verification:

- `uv run python -m py_compile ci_vibe_lab/runner.py tests/test_harness.py`
- `uv run python -m unittest discover -s tests -v`
- Result: 29 tests passed.

## Fresh Sparse Run Ledger

Experiment:

- `20260620T035543Z-maintenance_value-a35f272d`

Raw attempt counts:

| Bucket | Count | Interpretation |
|---|---:|---|
| Total stored attempts | 20 | Includes completed model runs and timeout rows. |
| Completed OpenCode attempts, exit `0` | 14 | Valid capability evidence. |
| Full-cap timeout rows | 4 | Runtime/environment evidence, not false-greens. |
| First-output timeout rows | 2 | Runtime/environment evidence, not false-greens. |

Completed-attempt score, excluding runtime stalls:

| Metric | Value |
|---|---:|
| Public pass | 14/14 (100.0%) |
| Hidden pass | 10/14 (71.4%) |
| Trust gap | 28.6% |
| False-green rate | 4/14 (28.6%) |

All stored rows, including runtime stalls:

| Metric | Value |
|---|---:|
| Public pass | 14/20 (70.0%) |
| Hidden pass | 10/20 (50.0%) |
| Timeout/stall rows | 6/20 (30.0%) |

The all-row score is useful for operational reliability. It should not be used as a pure model capability score because six rows are OpenCode/model invocation failures, not completed patches.

## Real False-Greens

These are legitimate failures. They are not artifacts of the stall problem.

### `adapter_field_rename`

Rows:

- `20260620T035543Z-adapter_field_rename-49a6b2c0`
- `20260620T035734Z-adapter_field_rename-388367c0`

Visible contract:

- `normalize_user` docstring says old and new API shapes are supported.
- It also says optional email is preserved when present and omitted when absent.

Observed patch pattern:

- Attempt 1 added support for `user_id` / `display_name` but dropped `email`.
- Attempt 2 used fallback field names but still dropped `email`.

Hidden failure:

- `KeyError: 'email'` in `test_optional_email_is_preserved_when_present`.

Verdict:

- Fair semantic-contract miss.
- The model fixed the visible new-field assertion but failed to preserve the full DTO contract already stated in the source.

### `batch_splitter_utility`

Rows:

- `20260620T035553Z-batch_splitter_utility-4554a0d2`
- `20260620T035746Z-batch_splitter_utility-3db1f512`

Visible contract:

- `split_batches` docstring says `batch_size` must be positive.
- It also states order preservation, no empty batches, and empty input behavior.

Observed patch pattern:

- Both attempts implemented chunking and empty input.
- Neither attempt validated `batch_size > 0`.

Hidden failure:

- `AssertionError: ValueError not raised` in `test_batch_size_must_be_positive`.

Verdict:

- Fair semantic-contract miss.
- The model implemented the happy path but skipped explicit defensive validation.

## Runtime/Stall Findings

The run environment became unstable after the first 14 completed OpenCode calls.

Timeout rows:

| Run ID | Scenario | Duration | Stdout | Stderr Classification |
|---|---|---:|---:|---|
| `20260620T035820Z-fixture_schema_migration-2c621b2d` | `fixture_schema_migration` | 900.3s | 17,879 bytes | Full-cap agent loop timeout |
| `20260620T041647Z-generated_openapi_refresh-6c0fcce4` | `generated_openapi_refresh` | 900.2s | 0 bytes | Full-cap no-output timeout |
| `20260620T043147Z-import_hygiene_fix-75e351af` | `import_hygiene_fix` | 900.2s | 0 bytes | Full-cap no-output timeout |
| `20260620T044647Z-logger_warn_migration-166f0de7` | `logger_warn_migration` | 900.2s | 0 bytes | Full-cap no-output timeout |
| `20260620T051215Z-regression_test_gap-51a86c35` | `regression_test_gap` | 120.3s | 0 bytes | First-output no-output timeout |
| `20260620T051515Z-utcnow_timezone_migration-c709d861` | `utcnow_timezone_migration` | 120.3s | 0 bytes | First-output no-output timeout |

The `fixture_schema_migration` timeout is different from the empty-stream failures. It had a real OpenCode stream and repeated wrong absolute-path reads, including paths where the timestamp component was malformed. That is agent-loop evidence.

The remaining five timeout rows are not capability evidence. They are invocation-path evidence: OpenCode/model produced no stream at all.

## Contract-Visible Lane Status

Experiment:

- `20260620T051739Z-maintenance_value-41bacd72`

Rows:

- `20260620T051739Z-adapter_field_rename-905f4c9a`
- `20260620T052040Z-batch_splitter_utility-db427589`

Both rows are first-output no-output timeouts after 120.3s.

Verdict:

- Do not interpret the contract-visible lane yet.
- It is currently an environment/provider availability sample, not a North Mini capability sample.
- The lane should be rerun only after a smoke prompt confirms OpenCode emits a stream normally again.

## Harness Verdict

Facts:

- The hidden tests for the two sparse false-greens are defensible because the missed behavior was visible in source docstrings.
- The harness correctly separates `public_pass=1, hidden_pass=0` false-greens from `opencode_exit_code=124` runtime failures.
- The original long-run behavior made no-output provider stalls too expensive to observe.
- The new first-output timeout makes those stalls explicit and bounded.

Recommendations:

- Report completed-attempt capability and operational reliability separately.
- Do not fold no-output timeouts into false-green rates.
- Keep timeout rows in the DB because they matter for agent reliability, cost, and eval reproducibility.
- Rerun contract-visible and control lanes only after a small OpenCode smoke test proves the model path is currently producing stdout/stderr.

## Next Run Conditions

Use these conditions before continuing the full evidence pack:

1. Run a single OpenCode smoke on a tiny task with `--first-output-timeout 120`.
2. If it emits normally, run contract-visible `maintenance_value` with `--runs 1`, `--delay-seconds 60`, and `--first-output-timeout 120`.
3. If contract-visible is healthy, run the DeepSeek control lane under the same pacing and first-output policy.
4. Generate the final report only after all compared lanes have healthy non-stall coverage.

Suggested command pattern:

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack maintenance_value \
  --model opencode/north-mini-code-free \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 120 \
  --runs 1 \
  --prompt-mode contract_visible \
  --db data/fresh-2026-06-20-north-mini-contract-rerun.sqlite \
  --runs-dir runs/fresh-2026-06-20/north-mini/contract-visible-rerun \
  --delay-seconds 60
```

## Current Defensible Claim

North Mini remains operationally credible on completed sparse maintenance attempts, but the fresh run exposed two separate risks: real semantic misses on explicit local contracts, and a run-environment/OpenCode no-output stall mode that must be controlled before making broader model-comparison claims.
