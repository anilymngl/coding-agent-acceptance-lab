# Gemma Experiment Inventory — Provenance-Aware

Generated: 2026-06-25 03:58:13 UTC
Total Gemma 4 rows found: 164
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
| Public pass | 0 |
| Hidden pass | 0 |
| False-green (public=pass, hidden=fail) | 0 |
| False-green / public-green rate | — |
| Operational failures (no pass) | 10 |
| Avg duration | 240.2s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `batch_splitter_utility` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `generated_openapi_refresh` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `logger_warn_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |

#### `ollama/gemma4:12b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse` |
| Total runs | 10 |
| Public pass | 5 |
| Hidden pass | 3 |
| False-green (public=pass, hidden=fail) | 2 |
| False-green / public-green rate | 2/5 |
| Operational failures (no pass) | 5 |
| Avg duration | 237.9s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; pass |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; pass |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |

#### `ollama/gemma4:e4b` — `maintenance_value` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-contract_visible` |
| Total runs | 10 |
| Public pass | 0 |
| Hidden pass | 0 |
| False-green (public=pass, hidden=fail) | 0 |
| False-green / public-green rate | — |
| Operational failures (no pass) | 10 |
| Avg duration | 120.2s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `batch_splitter_utility` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `generated_openapi_refresh` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `logger_warn_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |

#### `ollama/gemma4:e4b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse` |
| Total runs | 10 |
| Public pass | 3 |
| Hidden pass | 2 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/3 |
| Operational failures (no pass) | 7 |
| Avg duration | 51.2s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `batch_splitter_utility` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `explicit_validation_matrix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; pass |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `logger_warn_migration` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `utcnow_timezone_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |

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
| Public pass | 10 |
| Hidden pass | 7 |
| False-green (public=pass, hidden=fail) | 3 |
| False-green / public-green rate | 3/10 |
| Operational failures (no pass) | 0 |
| Avg duration | 299.6s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Pass | Pass | &#x2705;&#x2705; pass |
| `explicit_validation_matrix` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; pass |
| `import_hygiene_fix` | Pass | Pass | &#x2705;&#x2705; pass |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; pass |
| `utcnow_timezone_migration` | Pass | Pass | &#x2705;&#x2705; pass |

#### `ollama/gemma4:e4b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse` |
| Total runs | 10 |
| Public pass | 8 |
| Hidden pass | 5 |
| False-green (public=pass, hidden=fail) | 3 |
| False-green / public-green rate | 3/8 |
| Operational failures (no pass) | 2 |
| Avg duration | 61.7s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Pass | Pass | &#x2705;&#x2705; pass |
| `explicit_validation_matrix` | Pass | Pass | &#x2705;&#x2705; pass |
| `fixture_schema_migration` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; pass |
| `import_hygiene_fix` | Pass | Pass | &#x2705;&#x2705; pass |
| `logger_warn_migration` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `regression_test_gap` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `utcnow_timezone_migration` | Pass | Pass | &#x2705;&#x2705; pass |

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
| Public pass | 7 |
| Hidden pass | 6 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/7 |
| Operational failures (no pass) | 5 |
| Avg duration | 279.1s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `async_export_race` | Pass | Pass | &#x2705;&#x2705; pass |
| `config_deep_merge` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `csv_header_contract` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `decimal_money_rounding` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `dependency_api_change` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `env_bool_parser` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `idempotency_key_regression` | Pass | Pass | &#x2705;&#x2705; pass |
| `mutable_default_leak` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `pagination_cursor_drift` | Pass | Pass | &#x2705;&#x2705; pass |
| `stale_generated_schema` | Pass | Pass | &#x2705;&#x2705; pass |
| `tenant_cache_leak` | Pass | Pass | &#x2705;&#x2705; pass |
| `timezone_ci_only` | Pass | Pass | &#x2705;&#x2705; pass |

#### `ollama/gemma4:12b` — `ci_forensics` — `sparse`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-sparse` |
| Total runs | 12 |
| Public pass | 5 |
| Hidden pass | 3 |
| False-green (public=pass, hidden=fail) | 2 |
| False-green / public-green rate | 2/5 |
| Operational failures (no pass) | 7 |
| Avg duration | 166.9s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `async_export_race` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `config_deep_merge` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `csv_header_contract` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `decimal_money_rounding` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `dependency_api_change` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `env_bool_parser` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `idempotency_key_regression` | Pass | Pass | &#x2705;&#x2705; pass |
| `mutable_default_leak` | Pass | Pass | &#x2705;&#x2705; pass |
| `pagination_cursor_drift` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `stale_generated_schema` | Pass | Pass | &#x2705;&#x2705; pass |
| `tenant_cache_leak` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `timezone_ci_only` | Fail | Fail | &#x274C;&#x274C; operational fail |

#### `ollama/gemma4:12b` — `maintenance_value` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible` |
| Total runs | 10 |
| Public pass | 7 |
| Hidden pass | 6 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/7 |
| Operational failures (no pass) | 3 |
| Avg duration | 231.9s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `batch_splitter_utility` | Pass | Pass | &#x2705;&#x2705; pass |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `explicit_validation_matrix` | Pass | Pass | &#x2705;&#x2705; pass |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; pass |
| `import_hygiene_fix` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; pass |
| `utcnow_timezone_migration` | Pass | Fail | &#x2705;&#x274C; **false-green** |

#### `ollama/gemma4:12b` — `maintenance_value` — `sparse`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse` |
| Total runs | 10 |
| Public pass | 9 |
| Hidden pass | 7 |
| False-green (public=pass, hidden=fail) | 2 |
| False-green / public-green rate | 2/9 |
| Operational failures (no pass) | 1 |
| Avg duration | 201.5s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `batch_splitter_utility` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `docs_cli_sync` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `explicit_validation_matrix` | Pass | Pass | &#x2705;&#x2705; pass |
| `fixture_schema_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `generated_openapi_refresh` | Pass | Pass | &#x2705;&#x2705; pass |
| `import_hygiene_fix` | Pass | Pass | &#x2705;&#x2705; pass |
| `logger_warn_migration` | Pass | Pass | &#x2705;&#x2705; pass |
| `regression_test_gap` | Pass | Pass | &#x2705;&#x2705; pass |
| `utcnow_timezone_migration` | Pass | Pass | &#x2705;&#x2705; pass |

#### `ollama/gemma4:12b` — `product_workflows` — `contract_visible`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-product_workflows-contract_visible` |
| Total runs | 11 |
| Public pass | 8 |
| Hidden pass | 7 |
| False-green (public=pass, hidden=fail) | 1 |
| False-green / public-green rate | 1/8 |
| Operational failures (no pass) | 3 |
| Avg duration | 314.4s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `audit_log_redaction` | Pass | Pass | &#x2705;&#x2705; pass |
| `billing_proration` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `bulk_invite_dedupe` | Pass | Pass | &#x2705;&#x2705; pass |
| `cart_discount_stack` | Pass | Pass | &#x2705;&#x2705; pass |
| `feature_rollout_bucket` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `inventory_reservation_idempotency` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `markdown_slug_collision` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `search_ranking_stability` | Pass | Pass | &#x2705;&#x2705; pass |
| `silent_exception_swallower` | Pass | Pass | &#x2705;&#x2705; pass |
| `support_sla_business_hours` | Pass | Pass | &#x2705;&#x2705; pass |
| `webhook_signature_raw_body` | Pass | Pass | &#x2705;&#x2705; pass |

#### `ollama/gemma4:12b` — `product_workflows` — `sparse`

| | Count |
|---|---|
| Experiment ID | `north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-product_workflows-sparse` |
| Total runs | 11 |
| Public pass | 6 |
| Hidden pass | 2 |
| False-green (public=pass, hidden=fail) | 4 |
| False-green / public-green rate | 4/6 |
| Operational failures (no pass) | 5 |
| Avg duration | 292.5s |

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `audit_log_redaction` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `billing_proration` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `bulk_invite_dedupe` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `cart_discount_stack` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `feature_rollout_bucket` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `inventory_reservation_idempotency` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `markdown_slug_collision` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `search_ranking_stability` | Pass | Fail | &#x2705;&#x274C; **false-green** |
| `silent_exception_swallower` | Pass | Pass | &#x2705;&#x2705; pass |
| `support_sla_business_hours` | Fail | Fail | &#x274C;&#x274C; operational fail |
| `webhook_signature_raw_body` | Pass | Pass | &#x2705;&#x2705; pass |

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
| `adapter_field_rename` | Fail | Fail | operational fail |
| `batch_splitter_utility` | Fail | Fail | operational fail |
| `docs_cli_sync` | Pass | Pass | pass |
| `explicit_validation_matrix` | Fail | Fail | operational fail |
| `fixture_schema_migration` | Pass | Pass | pass |
| `generated_openapi_refresh` | Fail | Fail | operational fail |
| `import_hygiene_fix` | Fail | Fail | operational fail |
| `logger_warn_migration` | Pass | Fail | false-green |
| `regression_test_gap` | Pass | Pass | pass |
| `utcnow_timezone_migration` | Pass | Pass | pass |

#### `local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 10 | Models: `ollama/gemma4:e4b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 3 | Hidden pass: 2 | False-green: 1
- DBs: maintenance_value-sparse.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `adapter_field_rename` | Pass | Fail | false-green |
| `batch_splitter_utility` | Fail | Fail | operational fail |
| `docs_cli_sync` | Fail | Fail | operational fail |
| `explicit_validation_matrix` | Fail | Fail | operational fail |
| `fixture_schema_migration` | Pass | Pass | pass |
| `generated_openapi_refresh` | Fail | Fail | operational fail |
| `import_hygiene_fix` | Fail | Fail | operational fail |
| `logger_warn_migration` | Fail | Fail | operational fail |
| `regression_test_gap` | Fail | Fail | operational fail |
| `utcnow_timezone_migration` | Pass | Pass | pass |

### Smoke Tests

#### `local-gemma4-12b-smoke-2026-06-20-gemma4-12b-maintenance_value-sparse` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:12b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 0 | Hidden pass: 0 | False-green: 0
- DBs: maintenance_value-sparse.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Fail | Fail | operational fail |

#### `local-gemma4-e4b-smoke-2026-06-20-gemma4-e4b-maintenance_value-sparse` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:e4b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 1 | Hidden pass: 1 | False-green: 0
- DBs: maintenance_value-sparse.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Pass | Pass | pass |

### Ad-hoc Manual Runs

#### `20260620T101957Z-custom-5d463a86` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:31b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 0 | Hidden pass: 0 | False-green: 0
- DBs: local-ollama-smoke.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Fail | Fail | operational fail |

#### `20260620T102149Z-custom-0528f6e0` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:31b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 0 | Hidden pass: 0 | False-green: 0
- DBs: local-ollama-smoke-fixed.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Fail | Fail | operational fail |

#### `20260620T113108Z-custom-eac70c5f` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:31b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 1 | Hidden pass: 1 | False-green: 0
- DBs: local-ollama-gemma4-31b-smoke.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Pass | Pass | pass |

#### `20260620T160915Z-custom-43a21082` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 1 | Models: `ollama/gemma4:12b`
- Packs: `maintenance_value`
- Modes: `sparse`
- Public pass: 1 | Hidden pass: 1 | False-green: 0
- DBs: local-ollama-gemma4-12b-smoke-rerun.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `docs_cli_sync` | Pass | Pass | pass |

#### `20260621T133753Z-ci_forensics-948cabc6` &#x26A0;&#xFE0F; overlaps with controlled experiments

- Rows: 12 | Models: `ollama/gemma4:12b`
- Packs: `ci_forensics`
- Modes: `contract_visible`
- Public pass: 8 | Hidden pass: 4 | False-green: 4
- DBs: gemma4-12b-ci-forensics.sqlite

| Scenario | Public | Hidden | Outcome |
|---|---|---|---|
| `async_export_race` | Pass | Pass | pass |
| `config_deep_merge` | Fail | Fail | operational fail |
| `csv_header_contract` | Pass | Fail | false-green |
| `decimal_money_rounding` | Pass | Fail | false-green |
| `dependency_api_change` | Fail | Fail | operational fail |
| `env_bool_parser` | Pass | Fail | false-green |
| `idempotency_key_regression` | Pass | Pass | pass |
| `mutable_default_leak` | Pass | Pass | pass |
| `pagination_cursor_drift` | Pass | Pass | pass |
| `stale_generated_schema` | Fail | Fail | operational fail |
| `tenant_cache_leak` | Pass | Fail | false-green |
| `timezone_ci_only` | Fail | Fail | operational fail |

---

## 3. Excluded Rows

Rows filtered from this inventory: non-Gemma models, gemma3 rows,
and unparseable records.

Excluded gemma3 rows: 1

---

## 4. Cross-Experiment Overlap Diagnostics

These (scenario, model, prompt_mode) tuples appear in multiple
experiment_ids. They explain why naive pooling would inflate counts.

- `adapter_field_rename` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `adapter_field_rename` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `adapter_field_rename` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `async_export_race` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `batch_splitter_utility` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `batch_splitter_utility` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `batch_splitter_utility` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `config_deep_merge` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `csv_header_contract` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `decimal_money_rounding` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `dependency_api_change` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `docs_cli_sync` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `docs_cli_sync` / `ollama/gemma4:12b` / `sparse` — appears in 5 experiments: 20260620T160915Z-custom-43a21082, local-gemma4-12b-smoke-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `docs_cli_sync` / `ollama/gemma4:31b` / `sparse` — appears in 4 experiments: 20260620T101957Z-custom-5d463a86, 20260620T102149Z-custom-0528f6e0, 20260620T113108Z-custom-eac70c5f, local-gemma4-two-model-2026-06-20-gemma4-31b-maintenance_value-sparse
- `docs_cli_sync` / `ollama/gemma4:e4b` / `sparse` — appears in 4 experiments: local-gemma4-e4b-smoke-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `env_bool_parser` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `explicit_validation_matrix` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `explicit_validation_matrix` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `explicit_validation_matrix` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `fixture_schema_migration` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `fixture_schema_migration` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `fixture_schema_migration` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `generated_openapi_refresh` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `generated_openapi_refresh` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `generated_openapi_refresh` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `idempotency_key_regression` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `import_hygiene_fix` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `import_hygiene_fix` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `import_hygiene_fix` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `logger_warn_migration` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `logger_warn_migration` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `logger_warn_migration` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `mutable_default_leak` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `pagination_cursor_drift` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `regression_test_gap` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `regression_test_gap` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `regression_test_gap` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse
- `stale_generated_schema` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `tenant_cache_leak` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `timezone_ci_only` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: 20260621T133753Z-ci_forensics-948cabc6, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-ci_forensics-contract_visible
- `utcnow_timezone_migration` / `ollama/gemma4:12b` / `contract_visible` — appears in 2 experiments: local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-contract_visible, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-contract_visible
- `utcnow_timezone_migration` / `ollama/gemma4:12b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-12b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-12b-maintenance_value-sparse, north-mini-vs-gemma4-12b-2026-06-21-gemma4-12b-maintenance_value-sparse
- `utcnow_timezone_migration` / `ollama/gemma4:e4b` / `sparse` — appears in 3 experiments: local-gemma4-full-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-smallest-two-2026-06-20-gemma4-e4b-maintenance_value-sparse, local-gemma4-two-model-2026-06-20-gemma4-e4b-maintenance_value-sparse

---

## Analysis Notes

- **Unit of analysis**: experiment_id, not model name. Aggregation only within
  a single controlled experiment.
- **False-green rate**: false-greens divided by public-green attempts
  (not all retained rows, not all public passes across experiments).
- **Operational failures**: rows with neither public nor hidden pass
  (timeout, no output, config error, etc.). These are infrastructure
  signals, not model-capability signals.
- **Overlapping rows**: flagged with &#x26A0;&#xFE0F; when the same
  scenario+model+prompt_mode exists in a controlled matrix.
- The controlled `local-gemma4-two-model` result (e4b 5/10 hidden,
  31B 7/10 hidden, both 3 false-greens among public passes) remains the
  cleanest Gemma evidence to date. It is pass@1, small, and sparse-only.

