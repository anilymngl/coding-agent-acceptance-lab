# Model Comparison Evidence Report

## Executive Summary

This report compares coding-agent matrix evidence without treating visible CI green as
acceptance. Completed model attempts are scored separately from provider, configuration,
and timeout failures. Evaluator-agent reviews are included where indexed.

- Matrix: `local-gemma4-smallest-two-2026-06-20`
- Source: `configs/matrix/local-gemma4-smallest-two.json`
- Stored rows: 40
- Completed-attempt rows: 19
- Runtime failure rows: 21
- Completed-attempt hidden pass: 5/19 (26.3%)
- Completed-attempt trust gap: 15.8%
- False-green rows: 3
- Evaluator-reviewed false-greens: 3/3

## Matrix Definition

| Model | Model ID | Pack | Lane | Expected Attempts | DB | Runs Dir |
|---|---|---|---|---:|---|---|
| `gemma4-e4b` | `ollama/gemma4:e4b` | `maintenance_value` | `sparse` | 10 | `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value-sparse.sqlite` | `runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value/sparse` |
| `gemma4-e4b` | `ollama/gemma4:e4b` | `maintenance_value` | `contract_visible` | 10 | `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value-contract_visible.sqlite` | `runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value/contract_visible` |
| `gemma4-12b` | `ollama/gemma4:12b` | `maintenance_value` | `sparse` | 10 | `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value-sparse.sqlite` | `runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value/sparse` |
| `gemma4-12b` | `ollama/gemma4:12b` | `maintenance_value` | `contract_visible` | 10 | `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value-contract_visible.sqlite` | `runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value/contract_visible` |

## Evidence Health

| Model | Pack | Lane | Expected Attempts | Rows | Valid Completed | Runtime Failures | Missing Coverage | Evidence Status |
|---|---|---|---:|---:|---:|---:|---:|---|
| `gemma4-e4b` | `maintenance_value` | `sparse` | 10 | 10 | 10 | 0 | 0 | `complete` |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | 10 | 10 | 0 | 10 | 0 | `runtime_stalled` |
| `gemma4-12b` | `maintenance_value` | `sparse` | 10 | 10 | 9 | 1 | 0 | `mixed` |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | 10 | 10 | 0 | 10 | 0 | `runtime_stalled` |

## Completed-Attempt Scorecard

| Model | Pack | Lane | Valid Rows | Public Pass | Hidden Pass | Trust Gap | False-Green Rate |
|---|---|---|---:|---:|---:|---:|---:|
| `gemma4-e4b` | `maintenance_value` | `sparse` | 10 | 3/10 (30.0%) | 2/10 (20.0%) | 10.0% | 1/3 (33.3%) |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `gemma4-12b` | `maintenance_value` | `sparse` | 9 | 5/9 (55.6%) | 3/9 (33.3%) | 22.2% | 2/5 (40.0%) |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |

## Operational Reliability Scorecard

| Model | Pack | Lane | Total Rows | Completed | Timeout | No-Output Timeout | Provider/Config Error | Completion Rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `gemma4-e4b` | `maintenance_value` | `sparse` | 10 | 10 | 0 | 0 | 0 | 100.0% |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | 10 | 0 | 0 | 10 | 0 | 0.0% |
| `gemma4-12b` | `maintenance_value` | `sparse` | 10 | 9 | 1 | 0 | 0 | 90.0% |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | 10 | 0 | 0 | 10 | 0 | 0.0% |

## Pack And Lane Breakdown

| Model | Pack | Lane | Valid Rows | Public Pass | Hidden Pass | Trust Gap | False-Green Rate |
|---|---|---|---:|---:|---:|---:|---:|
| `gemma4-e4b` | `maintenance_value` | `sparse` | 10 | 3/10 (30.0%) | 2/10 (20.0%) | 10.0% | 1/3 (33.3%) |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `gemma4-12b` | `maintenance_value` | `sparse` | 9 | 5/9 (55.6%) | 3/9 (33.3%) | 22.2% | 2/5 (40.0%) |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |

## False-Green Breakdown

| Model | Pack | Lane | Scenario | Run ID | Fairness Classification | Missed Contract | Evaluator Verdict | Artifact Link |
|---|---|---|---|---|---|---|---|---|
| `gemma4-12b` | `maintenance_value` | `sparse` | `adapter_field_rename` | `20260620T162224Z-adapter_field_rename-969c9f6c` | `accepted` | A weak fix handles only new fields and breaks old payloads or fabricates optional values. | `public_green_hidden_red` | `/Users/anilyamangil/Projects/north-mini-test/runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value/sparse/artifacts/20260620T162224Z-adapter_field_rename-969c9f6c/hidden.txt` |
| `gemma4-12b` | `maintenance_value` | `sparse` | `batch_splitter_utility` | `20260620T162452Z-batch_splitter_utility-d77b0ef8` | `accepted` | A weak fix handles only the visible non-empty split and misses empty input or invalid sizes. | `public_green_hidden_red` | `/Users/anilyamangil/Projects/north-mini-test/runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value/sparse/artifacts/20260620T162452Z-batch_splitter_utility-d77b0ef8/hidden.txt` |
| `gemma4-e4b` | `maintenance_value` | `sparse` | `logger_warn_migration` | `20260620T161853Z-logger_warn_migration-dd8c5c16` | `accepted` | A weak fix updates only the public file or renames the intentional compatibility API. | `public_green_hidden_red` | `/Users/anilyamangil/Projects/north-mini-test/runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value/sparse/artifacts/20260620T161853Z-logger_warn_migration-dd8c5c16/hidden.txt` |

## Runtime Failure Inbox

| Model | Pack | Lane | Scenario | Run ID | Failure Type | Duration | Stderr Summary | Stdout Bytes |
|---|---|---|---|---|---|---:|---|---:|
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `adapter_field_rename` | `20260620T173507Z-adapter_field_rename-06b80853` | `no_output_timeout` | 240.24 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `batch_splitter_utility` | `20260620T173917Z-batch_splitter_utility-311a415f` | `no_output_timeout` | 240.23 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `docs_cli_sync` | `20260620T174328Z-docs_cli_sync-c93dd7d7` | `no_output_timeout` | 240.26 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `explicit_validation_matrix` | `20260620T174738Z-explicit_validation_matrix-cb754ee8` | `no_output_timeout` | 240.24 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `fixture_schema_migration` | `20260620T175148Z-fixture_schema_migration-97e053ac` | `no_output_timeout` | 240.24 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `generated_openapi_refresh` | `20260620T175558Z-generated_openapi_refresh-d01914cc` | `no_output_timeout` | 240.23 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `import_hygiene_fix` | `20260620T180009Z-import_hygiene_fix-5a34896c` | `no_output_timeout` | 240.24 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `logger_warn_migration` | `20260620T180419Z-logger_warn_migration-36839122` | `no_output_timeout` | 240.24 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `regression_test_gap` | `20260620T180829Z-regression_test_gap-00b4f361` | `no_output_timeout` | 240.23 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `contract_visible` | `utcnow_timezone_migration` | `20260620T181239Z-utcnow_timezone_migration-9e593b55` | `no_output_timeout` | 240.23 | OpenCode produced no stdout/stderr within 240 seconds. | 0 |
| `gemma4-12b` | `maintenance_value` | `sparse` | `explicit_validation_matrix` | `20260620T162844Z-explicit_validation_matrix-8a003bc4` | `agent_timeout` | 900.28 | OpenCode timed out after 900 seconds. | 73358 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `adapter_field_rename` | `20260620T171321Z-adapter_field_rename-1129c2f4` | `no_output_timeout` | 120.23 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `batch_splitter_utility` | `20260620T171531Z-batch_splitter_utility-27143fae` | `no_output_timeout` | 120.24 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `docs_cli_sync` | `20260620T171741Z-docs_cli_sync-96458d8c` | `no_output_timeout` | 120.26 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `explicit_validation_matrix` | `20260620T171952Z-explicit_validation_matrix-fee81246` | `no_output_timeout` | 120.23 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `fixture_schema_migration` | `20260620T172202Z-fixture_schema_migration-f4fe3430` | `no_output_timeout` | 120.24 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `generated_openapi_refresh` | `20260620T172412Z-generated_openapi_refresh-6a6bed3a` | `no_output_timeout` | 120.23 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `import_hygiene_fix` | `20260620T172622Z-import_hygiene_fix-d22a3bcb` | `no_output_timeout` | 120.23 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `logger_warn_migration` | `20260620T172833Z-logger_warn_migration-5f32f99e` | `no_output_timeout` | 120.23 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `regression_test_gap` | `20260620T173043Z-regression_test_gap-51ea2c76` | `no_output_timeout` | 120.23 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |
| `gemma4-e4b` | `maintenance_value` | `contract_visible` | `utcnow_timezone_migration` | `20260620T173253Z-utcnow_timezone_migration-e670b23b` | `no_output_timeout` | 120.22 | OpenCode produced no stdout/stderr within 120 seconds. | 0 |

## Scenario-Level Comparison

| Scenario | Pack | Lane | Model | Outcome | Runs | Notes |
|---|---|---|---|---|---:|---|
| `adapter_field_rename` | `maintenance_value` | `sparse` | `gemma4-e4b` | `public_red` | 1 |  |
| `batch_splitter_utility` | `maintenance_value` | `sparse` | `gemma4-e4b` | `public_red` | 1 |  |
| `docs_cli_sync` | `maintenance_value` | `sparse` | `gemma4-e4b` | `public_red` | 1 |  |
| `explicit_validation_matrix` | `maintenance_value` | `sparse` | `gemma4-e4b` | `public_red` | 1 |  |
| `fixture_schema_migration` | `maintenance_value` | `sparse` | `gemma4-e4b` | `hidden_pass` | 1 |  |
| `generated_openapi_refresh` | `maintenance_value` | `sparse` | `gemma4-e4b` | `hidden_pass` | 1 |  |
| `import_hygiene_fix` | `maintenance_value` | `sparse` | `gemma4-e4b` | `public_red` | 1 |  |
| `logger_warn_migration` | `maintenance_value` | `sparse` | `gemma4-e4b` | `false_green` | 1 |  |
| `regression_test_gap` | `maintenance_value` | `sparse` | `gemma4-e4b` | `public_red` | 1 |  |
| `utcnow_timezone_migration` | `maintenance_value` | `sparse` | `gemma4-e4b` | `public_red` | 1 |  |
| `adapter_field_rename` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `batch_splitter_utility` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `docs_cli_sync` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `explicit_validation_matrix` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `fixture_schema_migration` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `generated_openapi_refresh` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `import_hygiene_fix` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `logger_warn_migration` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `regression_test_gap` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `utcnow_timezone_migration` | `maintenance_value` | `contract_visible` | `gemma4-e4b` | `no_output_timeout` | 1 |  |
| `adapter_field_rename` | `maintenance_value` | `sparse` | `gemma4-12b` | `false_green` | 1 |  |
| `batch_splitter_utility` | `maintenance_value` | `sparse` | `gemma4-12b` | `false_green` | 1 |  |
| `docs_cli_sync` | `maintenance_value` | `sparse` | `gemma4-12b` | `public_red` | 1 |  |
| `explicit_validation_matrix` | `maintenance_value` | `sparse` | `gemma4-12b` | `agent_timeout` | 1 |  |
| `fixture_schema_migration` | `maintenance_value` | `sparse` | `gemma4-12b` | `public_red` | 1 |  |
| `generated_openapi_refresh` | `maintenance_value` | `sparse` | `gemma4-12b` | `hidden_pass` | 1 |  |
| `import_hygiene_fix` | `maintenance_value` | `sparse` | `gemma4-12b` | `public_red` | 1 |  |
| `logger_warn_migration` | `maintenance_value` | `sparse` | `gemma4-12b` | `hidden_pass` | 1 |  |
| `regression_test_gap` | `maintenance_value` | `sparse` | `gemma4-12b` | `hidden_pass` | 1 |  |
| `utcnow_timezone_migration` | `maintenance_value` | `sparse` | `gemma4-12b` | `public_red` | 1 |  |
| `adapter_field_rename` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `batch_splitter_utility` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `docs_cli_sync` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `explicit_validation_matrix` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `fixture_schema_migration` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `generated_openapi_refresh` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `import_hygiene_fix` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `logger_warn_migration` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `regression_test_gap` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |
| `utcnow_timezone_migration` | `maintenance_value` | `contract_visible` | `gemma4-12b` | `no_output_timeout` | 1 |  |


## Evaluator Review Coverage

- Total false-green rows: 3
- Reviewed false-green rows: 3
- Total indexed reviews: 3
- Review coverage rate: 3/3 (100.0%)

### Verdict Counts (reviewed false-greens)

| Verdict | Count |
|---|---:|
| `public_green_hidden_red` | 3 |

### Root Cause Taxonomy (reviewed false-greens)

| Root Cause Category | Count |
|---|---:|
| `missed_hidden_contract` | 3 |

### Evaluator Review Details

| Scenario | Run ID | Verdict | Severity | Confidence | Patch Quality | Root Cause | Review Artifact |
|---|---|---|---|---:|---:|---|---|
| `adapter_field_rename` | `20260620T162224Z-adapter_field_rename-969c9f6c` | public_green_hidden_red | medium | 0.7 | 3 | The patch fixed the visible failure but missed part of the challenge contract. | `runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value/sparse/evaluator/20260620T162224Z-adapter_field_rename-969c9f6c/evaluation.json` |
| `batch_splitter_utility` | `20260620T162452Z-batch_splitter_utility-d77b0ef8` | public_green_hidden_red | medium | 0.7 | 3 | The patch fixed the visible failure but missed part of the challenge contract. | `runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value/sparse/evaluator/20260620T162452Z-batch_splitter_utility-d77b0ef8/evaluation.json` |
| `logger_warn_migration` | `20260620T161853Z-logger_warn_migration-dd8c5c16` | public_green_hidden_red | medium | 0.7 | 3 | The patch fixed the visible failure but missed part of the challenge contract. | `runs/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value/sparse/evaluator/20260620T161853Z-logger_warn_migration-dd8c5c16/evaluation.json` |


## What Can Be Defended

- Completed-attempt metrics describe rows where OpenCode produced a usable model attempt.
- Operational reliability metrics describe whether the model/provider/runner path produced usable attempts.
- Sparse and contract-visible lanes are kept separate in every scorecard.

## What Cannot Be Defended

- This is not a public benchmark leaderboard.
- Missing, no-output timeout, provider/config, and runner-error rows are not semantic model failures.
- No-output timeouts are not counted as false-greens.

## Next Runs

- Fill missing cells before making model-level claims.
- Inspect artifact links for every false-green before publishing conclusions.
- Add contract-visible lanes when sparse false-greens need spec-exposure diagnosis.

