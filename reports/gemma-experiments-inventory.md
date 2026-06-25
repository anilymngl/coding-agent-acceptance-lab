# Gemma Experiment Inventory — Provenance-Aware

> **Frozen snapshot.** Generated from local SQLite sources under `data/`
> that are not committed to the repository. This report is not independently
> reproducible from a clean checkout.

Generated: 2026-06-25 01:03:31 UTC

## Database Scan

| | Count |
|---|---|
| Discovered paths | 63 |
| Read successfully | 57 |
| No runs table | 1 |
| Query error | 5 |
| Raw rows discovered (pre-dedup) | 164 |
| Exact duplicate run_ids removed | 0 |
| Conflicting duplicate run_ids | 0 |
| Unique run_ids retained | 164 |
| Excluded gemma3 rows | 1 |

### Scan Errors

- `data/maintenance-value-north-mini.sqlite`: OperationalError('no such column: prompt_mode')
- `data/maintenance-value-v2.sqlite`: OperationalError('no such column: prompt_mode')
- `data/north-mini-code-eval.sqlite`: OperationalError('no such column: prompt_mode')
- `data/product-workflows-v2.sqlite`: OperationalError('no such column: prompt_mode')
- `data/results.sqlite`: OperationalError('no such column: prompt_mode')

Unique experiment_ids: 21

---

## 1. Controlled Evidence

Each subsection is a single matrix config with uniform run policy,
scenario coverage, and prompt lanes. Rows are not pooled across experiments.

### local-gemma4-smallest-two-2026-06-20

- **Config:** `configs/matrix/local-gemma4-smallest-two.json`
- **Description:** e4b vs 12b, maintenance_value sparse + contract_visible, pass@1
- **Cells (model+pack+mode combos):** 4
- **Total rows:** 40

#### `ollama/gemma4:12b` — `maintenance_value` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 0 |
| Hidden pass | 0 |
| False-green (public=pass, hidden=fail) | 0 |
| False-green / public-green rate | — |
| Public-red (no public pass) | 10 |
| Avg duration | 240.2s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; public-red |
| `batch_splitter_utility` | Fail | Fail | &#x274C;&#x274C; public-red |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; public-red |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; public-red |
| `generated_openapi_refresh` | Fail | Fail | &#x274C;&#x274C; public-red |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `logger_warn_migration` | Fail | Fail | &#x274C;&#x274C; public-red |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; public-red |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; public-red |

#### `ollama/gemma4:12b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 5 |
| Hidden pass | 3 |
| False-green (public=pass, hidden=fail) | 2 |
| False-green / public-green rate | 2/5 |
| Public-red (no public pass) | 5 |
| Avg duration | 237.9s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; public-red |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; public-red |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; public-red |

#### `ollama/gemma4:e4b` — `maintenance_value` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-contract_visible` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 0 |
| Hidden pass | 0 |
| False-green (public=pass, hidden=fail) | 0 |
| False-green / public-green rate | — |
| Public-red (no public pass) | 10 |
| Avg duration | 120.2s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; public-red |
| `batch_splitter_utility` | Fail | Fail | &#x274C;&#x274C; public-red |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; public-red |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; public-red |
| `generated_openapi_refresh` | Fail | Fail | &#x274C;&#x274C; public-red |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `logger_warn_migration` | Fail | Fail | &#x274C;&#x274C; public-red |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; public-red |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; public-red |

#### `ollama/gemma4:e4b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 3 |
| Hidden pass | 2 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/3 |
| Public-red (no public pass) | 7 |
| Avg duration | 51.2s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; public-red |
| `batch_splitter_utility` | Fail | Fail | &#x274C;&#x274C; public-red |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; public-red |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `logger_warn_migration` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; public-red |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; public-red |

### local-gemma4-two-model-2026-06-20

- **Config:** `configs/matrix/local-gemma4-two-model.json`
- **Description:** e4b vs 31b, maintenance_value sparse, pass@1
- **Cells (model+pack+mode combos):** 2
- **Total rows:** 20

#### `ollama/gemma4:31b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-two-model-2026-06-20-gemma4-31b-maintenance_value-sparse` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 10 |
| Hidden pass | 7 |
| False-green (public=pass, hidden=fail) | 3 |
| False-green / public-green rate | 3/10 |
| Public-red (no public pass) | 0 |
| Avg duration | 299.6s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `explicit_validation_matrix` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `import_hygiene_fix` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `utcnow_timezone_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |

#### `ollama/gemma4:e4b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 8 |
| Hidden pass | 5 |
| False-green (public=pass, hidden=fail) | 3 |
| False-green / public-green rate | 3/8 |
| Public-red (no public pass) | 2 |
| Avg duration | 61.7s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `explicit_validation_matrix` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; public-red |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `import_hygiene_fix` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `logger_warn_migration` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; public-red |
| `utcnow_timezone_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |

### north-mini-vs-gemma4-12b-2026-06-21

- **Config:** `configs/matrix/north-mini-vs-gemma4-12b.json`
- **Description:** North Mini vs Gemma 4 12b, ci_forensics + maintenance_value + product_workflows, sparse + contract_visible, pass@1
- **Cells (model+pack+mode combos):** 6
- **Total rows:** 66

#### `ollama/gemma4:12b` — `ci_forensics` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible` |
| Total runs | 12 |
| Coverage | complete |
| Public pass | 7 |
| Hidden pass | 6 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/7 |
| Public-red (no public pass) | 5 |
| Avg duration | 279.1s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `async_export_race` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `config_deep_merge` | Fail | Fail | &#x274C;&#x274C; public-red |
| `csv_header_contract` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `decimal_money_rounding` | Fail | Fail | &#x274C;&#x274C; public-red |
| `dependency_api_change` | Fail | Fail | &#x274C;&#x274C; public-red |
| `env_bool_parser` | Fail | Fail | &#x274C;&#x274C; public-red |
| `idempotency_key_regression` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `mutable_default_leak` | Fail | Fail | &#x274C;&#x274C; public-red |
| `pagination_cursor_drift` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `stale_generated_schema` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `tenant_cache_leak` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `timezone_ci_only` | Pass | Pass | &#x2705;&#x2705; hidden pass |

#### `ollama/gemma4:12b` — `ci_forensics` — `sparse`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-sparse` |
| Total runs | 12 |
| Coverage | complete |
| Public pass | 5 |
| Hidden pass | 3 |
| False-green (public=pass, hidden=fail) | 2 |
| False-green / public-green rate | 2/5 |
| Public-red (no public pass) | 7 |
| Avg duration | 166.9s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `async_export_race` | Fail | Fail | &#x274C;&#x274C; public-red |
| `config_deep_merge` | Fail | Fail | &#x274C;&#x274C; public-red |
| `csv_header_contract` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `decimal_money_rounding` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `dependency_api_change` | Fail | Fail | &#x274C;&#x274C; public-red |
| `env_bool_parser` | Fail | Fail | &#x274C;&#x274C; public-red |
| `idempotency_key_regression` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `mutable_default_leak` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `pagination_cursor_drift` | Fail | Fail | &#x274C;&#x274C; public-red |
| `stale_generated_schema` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `tenant_cache_leak` | Fail | Fail | &#x274C;&#x274C; public-red |
| `timezone_ci_only` | Fail | Fail | &#x274C;&#x274C; public-red |

#### `ollama/gemma4:12b` — `maintenance_value` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 7 |
| Hidden pass | 6 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/7 |
| Public-red (no public pass) | 3 |
| Avg duration | 231.9s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; public-red |
| `batch_splitter_utility` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; public-red |
| `explicit_validation_matrix` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; public-red |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `utcnow_timezone_migration` | Pass | Fail | &#x2705;&#x274C; **false-green** |

#### `ollama/gemma4:12b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse` |
| Total runs | 10 |
| Coverage | complete |
| Public pass | 9 |
| Hidden pass | 7 |
| False-green (public=pass, hidden=fail) | 2 |
| False-green / public-green rate | 2/9 |
| Public-red (no public pass) | 1 |
| Avg duration | 201.5s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; public-red |
| `explicit_validation_matrix` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `import_hygiene_fix` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `utcnow_timezone_migration` | Pass | Pass | &#x2705;&#x2705; hidden pass |

#### `ollama/gemma4:12b` — `product_workflows` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-product_workflows-contract_visible` |
| Total runs | 11 |
| Coverage | complete |
| Public pass | 8 |
| Hidden pass | 7 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/8 |
| Public-red (no public pass) | 3 |
| Avg duration | 314.4s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `audit_log_redaction` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `billing_proration` | Fail | Fail | &#x274C;&#x274C; public-red |
| `bulk_invite_dedupe` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `cart_discount_stack` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `feature_rollout_bucket` | Fail | Fail | &#x274C;&#x274C; public-red |
| `inventory_reservation_idempotency` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `markdown_slug_collision` | Fail | Fail | &#x274C;&#x274C; public-red |
| `search_ranking_stability` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `silent_exception_swallower` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `support_sla_business_hours` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `webhook_signature_raw_body` | Pass | Pass | &#x2705;&#x2705; hidden pass |

#### `ollama/gemma4:12b` — `product_workflows` — `sparse`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-product_workflows-sparse` |
| Total runs | 11 |
| Coverage | complete |
| Public pass | 6 |
| Hidden pass | 2 |
| False-green (public=pass, hidden=fail) | 4 |
| False-green / public-green rate | 4/6 |
| Public-red (no public pass) | 5 |
| Avg duration | 292.5s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `audit_log_redaction` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `billing_proration` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `bulk_invite_dedupe` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `cart_discount_stack` | Fail | Fail | &#x274C;&#x274C; public-red |
| `feature_rollout_bucket` | Fail | Fail | &#x274C;&#x274C; public-red |
| `inventory_reservation_idempotency` | Fail | Fail | &#x274C;&#x274C; public-red |
| `markdown_slug_collision` | Fail | Fail | &#x274C;&#x274C; public-red |
| `search_ranking_stability` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `silent_exception_swallower` | Pass | Pass | &#x2705;&#x2705; hidden pass |
| `support_sla_business_hours` | Fail | Fail | &#x274C;&#x274C; public-red |
| `webhook_signature_raw_body` | Pass | Pass | &#x2705;&#x2705; hidden pass |

---

## 2. Historical Inventory

Rows not part of the controlled matrices above. Grouped by experiment_id
and explicitly labeled. **Do not pool these with controlled evidence.**

### Overlapping / Duplicate Experiments

#### `local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 10 | Models: `ollama/gemma4:12b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 5 | Hidden pass: 4 | False-green: 1
- DBs: maintenance_value-sparse.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | public-red |
| `batch_splitter_utility` | Fail | Fail | public-red |
| `docs_cli_sync` | Pass | Pass | hidden pass |
| `explicit_validation_matrix` | Fail | Fail | public-red |
| `fixture_schema_migration` | Pass | Pass | hidden pass |
| `generated_openapi_refresh` | Fail | Fail | public-red |
| `import_hygiene_fix` | Fail | Fail | public-red |
| `logger_warn_migration` | Pass | Fail | false-green |
| `regression_test_gap` | Pass | Pass | hidden pass |
| `utcnow_timezone_migration` | Pass | Pass | hidden pass |

#### `local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 10 | Models: `ollama/gemma4:e4b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 3 | Hidden pass: 2 | False-green: 1
- DBs: maintenance_value-sparse.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | false-green |
| `batch_splitter_utility` | Fail | Fail | public-red |
| `docs_cli_sync` | Fail | Fail | public-red |
| `explicit_validation_matrix` | Fail | Fail | public-red |
| `fixture_schema_migration` | Pass | Pass | hidden pass |
| `generated_openapi_refresh` | Fail | Fail | public-red |
| `import_hygiene_fix` | Fail | Fail | public-red |
| `logger_warn_migration` | Fail | Fail | public-red |
| `regression_test_gap` | Fail | Fail | public-red |
| `utcnow_timezone_migration` | Pass | Pass | hidden pass |

### Smoke Tests

#### `local-gemma4-12b-smoke-2026-06-20-gemma4-12b-maintenance_value-sparse` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:12b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 0 | Hidden pass: 0 | False-green: 0
- DBs: maintenance_value-sparse.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Fail | Fail | public-red |

#### `local-gemma4-e4b-smoke-2026-06-20-gemma4-e4b-maintenance_value-sparse` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:e4b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 1 | Hidden pass: 1 | False-green: 0
- DBs: maintenance_value-sparse.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Pass | Pass | hidden pass |

### Ad-hoc Manual Runs

#### `20260620T101957Z-custom-5d463a86` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:31b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 0 | Hidden pass: 0 | False-green: 0
- DBs: local-ollama-smoke.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Fail | Fail | public-red |

#### `20260620T102149Z-custom-0528f6e0` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:31b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 0 | Hidden pass: 0 | False-green: 0
- DBs: local-ollama-smoke-fixed.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Fail | Fail | public-red |

#### `20260620T113108Z-custom-eac70c5f` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:31b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 1 | Hidden pass: 1 | False-green: 0
- DBs: local-ollama-gemma4-31b-smoke.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Pass | Pass | hidden pass |

#### `20260620T160915Z-custom-43a21082` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:12b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 1 | Hidden pass: 1 | False-green: 0
- DBs: local-ollama-gemma4-12b-smoke-rerun.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Pass | Pass | hidden pass |

#### `20260621T133753Z-ci_forensics-948cabc6` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 12 | Models: `ollama/gemma4:12b`
- Packs: `ci_forensics`
- Modes: `contract_visible`
- Public pass: 8 | Hidden pass: 4 | False-green: 4
- DBs: gemma4-12b-ci-forensics.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `async_export_race` | Pass | Pass | hidden pass |
| `config_deep_merge` | Fail | Fail | public-red |
| `csv_header_contract` | Pass | Fail | false-green |
| `decimal_money_rounding` | Pass | Fail | false-green |
| `dependency_api_change` | Fail | Fail | public-red |
| `env_bool_parser` | Pass | Fail | false-green |
| `idempotency_key_regression` | Pass | Pass | hidden pass |
| `mutable_default_leak` | Pass | Pass | hidden pass |
| `pagination_cursor_drift` | Pass | Pass | hidden pass |
| `stale_generated_schema` | Fail | Fail | public-red |
| `tenant_cache_leak` | Pass | Fail | false-green |
| `timezone_ci_only` | Fail | Fail | public-red |

---

## 3. Source Manifest

Database sources scanned to produce this inventory. These files are not
committed to the repository.

| Database | SHA-256 (first 16) | Rows scanned | Unique runs | Experiment IDs |
|---|---:|---:|---|
| `data/ci-forensics-deepseek.sqlite` | `f2ec7405ac21ca74` | ? | 0 | 0 |
| `data/ci-forensics-glm52.sqlite` | `4f8ffe942651bf6d` | ? | 0 | 0 |
| `data/ci-forensics-v2.sqlite` | `6a16eff10f2a500c` | ? | 0 | 0 |
| `data/control-results.sqlite` | `14d372ccdaa873fc` | ? | 0 | 0 |
| `data/fresh-2026-06-20-north-mini-contract.sqlite` | `e9d9ea773365698d` | ? | 0 | 0 |
| `data/fresh-2026-06-20-north-mini-sparse.sqlite` | `08bd5b3dd36813d4` | ? | 0 | 0 |
| `data/fresh-2026-06-20-opencode-smoke.sqlite` | `78476cc7b705b0cf` | ? | 0 | 0 |
| `data/local-ollama-gemma3-smoke.sqlite` | `6cd283fe8b52fce1` | ? | 0 | 0 |
| `data/local-ollama-gemma4-12b-smoke-rerun.sqlite` | `2d0f8067af5e40d6` | ? | 1 | 1 |
| `data/local-ollama-gemma4-31b-smoke.sqlite` | `9a2b5f9140ba2b32` | ? | 1 | 1 |
| `data/local-ollama-qwen25-coder-smoke.sqlite` | `27f3f265fd0078bc` | ? | 0 | 0 |
| `data/local-ollama-smoke-fixed.sqlite` | `462803ce2a1fa786` | ? | 1 | 1 |
| `data/local-ollama-smoke.sqlite` | `847e5773556171b4` | ? | 1 | 1 |
| `data/maintenance-deepseek.sqlite` | `594669016f5636d2` | ? | 0 | 0 |
| `data/maintenance-value-north-mini.sqlite` | `ebc2c686e52b4278` | ? | 0 | 0 |
| `data/maintenance-value-v2.sqlite` | `3421ded97297dacf` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-contract_visible.sqlite` | `d4ac03c4b2c87a9f` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-sparse.sqlite` | `417b5ecb67da8d62` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-contract_visible.sqlite` | `ccc0544ce7972b10` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-sparse.sqlite` | `145e7beac32c51c3` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-contract_visible.sqlite` | `c9494017b4088147` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-sparse.sqlite` | `234adaa11dde3679` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-contract_visible.sqlite` | `6ea34e8564a820bb` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-sparse.sqlite` | `a5bf61f497d6b409` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-contract_visible.sqlite` | `3eb965e1f3e585a2` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-sparse.sqlite` | `1eb1507222865ad5` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-contract_visible.sqlite` | `ee38ea0d0339ed17` | ? | 0 | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-sparse.sqlite` | `9478084c32cf9b2b` | ? | 0 | 0 |
| `data/matrix/local-gemma4-12b-smoke-2026-06-20/gemma4-12b/maintenance_value-sparse.sqlite` | `7b80629385d06d61` | ? | 1 | 1 |
| `data/matrix/local-gemma4-e4b-smoke-2026-06-20/gemma4-e4b/maintenance_value-sparse.sqlite` | `33c1fbd769008270` | ? | 1 | 1 |
| `data/matrix/local-gemma4-full-2026-06-20/gemma4-12b/maintenance_value-sparse.sqlite` | `4256a2ba69ad44da` | ? | 10 | 1 |
| `data/matrix/local-gemma4-full-2026-06-20/gemma4-e4b/maintenance_value-sparse.sqlite` | `b78215f80b645c0d` | ? | 10 | 1 |
| `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value-contract_visible.sqlite` | `191c9d1eb661b543` | ? | 10 | 1 |
| `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value-sparse.sqlite` | `fb03ab726741770a` | ? | 10 | 1 |
| `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value-contract_visible.sqlite` | `68ae694eb09c4ed9` | ? | 10 | 1 |
| `data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value-sparse.sqlite` | `1ae0012b93db3128` | ? | 10 | 1 |
| `data/matrix/local-gemma4-two-model-2026-06-20/gemma4-31b/maintenance_value-sparse.sqlite` | `93f68bb85f312191` | ? | 10 | 1 |
| `data/matrix/local-gemma4-two-model-2026-06-20/gemma4-e4b/maintenance_value-sparse.sqlite` | `a1f0304f6afbe107` | ? | 10 | 1 |
| `data/matrix/north-mini-openrouter-completion/north-mini/product_workflows-contract_visible.sqlite` | `9e99dc8c3783ae36` | ? | 0 | 0 |
| `data/matrix/north-mini-openrouter-completion/north-mini/product_workflows-sparse.sqlite` | `02a68a7920476db9` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/ci_forensics-contract_visible.sqlite` | `3bbd8c8d17ca6b74` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/ci_forensics-sparse.sqlite` | `5686eb1f1281be93` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/maintenance_value-contract_visible.sqlite` | `d4174f85a26bf72e` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/maintenance_value-sparse.sqlite` | `382228ee5ba63fb0` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/product_workflows-contract_visible.sqlite` | `ce446f50ef7047bb` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/product_workflows-sparse.sqlite` | `e3b0c44298fc1c14` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/ci_forensics-contract_visible.sqlite` | `9bf05f4b1ba90009` | ? | 12 | 1 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/ci_forensics-sparse.sqlite` | `a03a2d771a8dcf70` | ? | 12 | 1 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/maintenance_value-contract_visible.sqlite` | `062b67059ca63832` | ? | 10 | 1 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/maintenance_value-sparse.sqlite` | `1e6176d72bcb6692` | ? | 10 | 1 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/product_workflows-contract_visible.sqlite` | `70f6b84c1c3ecf2d` | ? | 11 | 1 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/product_workflows-sparse.sqlite` | `6d2ef9f1fea67489` | ? | 11 | 1 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/ci_forensics-contract_visible.sqlite` | `b25c13f4ff47e188` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/ci_forensics-sparse.sqlite` | `b0eab1e084496a81` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/maintenance_value-contract_visible.sqlite` | `6c907f1c0bcc667a` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/maintenance_value-sparse.sqlite` | `5fdd79d145568385` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/product_workflows-contract_visible.sqlite` | `fa477a60e462a015` | ? | 0 | 0 |
| `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/product_workflows-sparse.sqlite` | `5d47cd6950bd7721` | ? | 0 | 0 |
| `data/north-mini-code-eval.sqlite` | `415f6cfbcfc3e6a5` | ? | 0 | 0 |
| `data/north-mini-full-2026-06-21/ci_forensics.sqlite` | `ae5a0a62c5b0b4f9` | ? | 0 | 0 |
| `data/north-mini-full-2026-06-21/gemma4-12b-ci-forensics.sqlite` | `b8db5a704ac970cf` | ? | 12 | 1 |
| `data/product-workflows-v2.sqlite` | `c5789108aa04f80e` | ? | 0 | 0 |
| `data/results.sqlite` | `3f58e6c1f59ef7b4` | ? | 0 | 0 |

---

## 4. Cross-Experiment Overlap Diagnostics

These (pack, scenario, model, prompt_mode) tuples appear in multiple
experiment_ids. They explain why naive pooling would inflate counts.

- `ci_forensics` / `async_export_race` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `config_deep_merge` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `csv_header_contract` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `decimal_money_rounding` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `dependency_api_change` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `env_bool_parser` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `idempotency_key_regression` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `mutable_default_leak` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `pagination_cursor_drift` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `stale_generated_schema` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `tenant_cache_leak` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `ci_forensics` / `timezone_ci_only` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `maintenance_value` / `adapter_field_rename` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `adapter_field_rename` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `adapter_field_rename` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `batch_splitter_utility` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `batch_splitter_utility` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `batch_splitter_utility` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `docs_cli_sync` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `docs_cli_sync` / `ollama/gemma4:12b` / `sparse` — appears in 5 experiments: 20260620T160915Z-custom-43a21082, local-gemma4-12b-smoke-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `docs_cli_sync` / `ollama/gemma4:31b` / `sparse` — appears in 4 experiments: 20260620T101957Z-custom-5d463a86, 20260620T102149Z-custom-0528f6e0, 20260620T113108Z-custom-eac70c5f, local-gemma4-two-model-2026-06-20-gemma4-31b-maintenance_value-sparse
- `maintenance_value` / `docs_cli_sync` / `ollama/gemma4:e4b` / `sparse` — appears in 4 experiments: local-gemma4-e4b-smoke-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `explicit_validation_matrix` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `explicit_validation_matrix` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `explicit_validation_matrix` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `fixture_schema_migration` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `fixture_schema_migration` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `fixture_schema_migration` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `generated_openapi_refresh` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `generated_openapi_refresh` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `generated_openapi_refresh` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `import_hygiene_fix` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `import_hygiene_fix` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `import_hygiene_fix` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `logger_warn_migration` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `logger_warn_migration` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `logger_warn_migration` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `regression_test_gap` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `regression_test_gap` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `regression_test_gap` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `maintenance_value` / `utcnow_timezone_migration` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `maintenance_value` / `utcnow_timezone_migration` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `maintenance_value` / `utcnow_timezone_migration` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse

---

## Analysis Notes

- **Unit of analysis**: experiment_id, not model name. Aggregation only within
  a single controlled experiment.
- **False-green rate**: false-greens divided by public-green attempts
  (not all retained rows, not all public passes across experiments).
- **Public-red**: rows with `public_pass=0, hidden_pass=0`. The cause
  (timeout, provider error, bad patch, no edit, etc.) is not classified
  from public-pass data alone. Do not read public-red as an
  infrastructure label without separate runtime evidence.
- **Overlapping rows**: flagged with &#x26A0;&#xFE0F; when the same
  (pack, scenario, model, prompt_mode) tuple exists in a controlled
  matrix.
- Run IDs are deduplicated globally across all database files.
  Conflicting duplicates (same run_id, different payload) are counted
  in the scan header.
- The controlled `local-gemma4-two-model` result (e4b 5/10 hidden,
  31B 7/10 hidden, both 3 false-greens among public passes) remains the
  cleanest Gemma evidence to date. It is pass@1, small, and sparse-only.
- **Frozen snapshot.** The source databases under `data/` are gitignored.
  Re-running this script requires the same local data.

