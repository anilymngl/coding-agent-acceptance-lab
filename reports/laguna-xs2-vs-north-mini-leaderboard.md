# Model Comparison Evidence Report

## Executive Summary

This report compares coding-agent matrix evidence without treating visible CI green as
acceptance. Completed model attempts are scored separately from provider, configuration,
and timeout failures. Evaluator-agent reviews are included where indexed.

- Matrix: `laguna-xs2-vs-north-mini-2026-06-22`
- Source: `configs/matrix/laguna-xs2-vs-north-mini.json`
- Stored rows: 239
- Completed-attempt rows: 239
- Runtime failure rows: 0
- Completed-attempt hidden pass: 180/239 (75.3%)
- Completed-attempt trust gap: 24.7%
- False-green rows: 59
- Evaluator-reviewed false-greens: 10/59

## Matrix Definition

| Model | Model ID | Pack | Lane | Expected Attempts | DB | Runs Dir |
|---|---|---|---|---:|---|---|
| `laguna-xs2` | `openrouter/poolside/laguna-xs.2:free` | `ci_forensics` | `sparse` | 36 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-sparse.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse` |
| `laguna-xs2` | `openrouter/poolside/laguna-xs.2:free` | `ci_forensics` | `contract_visible` | 36 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-contract_visible.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/contract_visible` |
| `laguna-xs2` | `openrouter/poolside/laguna-xs.2:free` | `maintenance_value` | `sparse` | 30 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-sparse.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse` |
| `laguna-xs2` | `openrouter/poolside/laguna-xs.2:free` | `maintenance_value` | `contract_visible` | 30 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-contract_visible.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/contract_visible` |
| `laguna-xs2` | `openrouter/poolside/laguna-xs.2:free` | `product_workflows` | `sparse` | 33 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-sparse.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse` |
| `laguna-xs2` | `openrouter/poolside/laguna-xs.2:free` | `product_workflows` | `contract_visible` | 33 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-contract_visible.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/contract_visible` |
| `north-mini` | `opencode/north-mini-code-free` | `ci_forensics` | `sparse` | 36 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-sparse.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse` |
| `north-mini` | `opencode/north-mini-code-free` | `ci_forensics` | `contract_visible` | 36 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-contract_visible.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/contract_visible` |
| `north-mini` | `opencode/north-mini-code-free` | `maintenance_value` | `sparse` | 30 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-sparse.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value/sparse` |
| `north-mini` | `opencode/north-mini-code-free` | `maintenance_value` | `contract_visible` | 30 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-contract_visible.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value/contract_visible` |
| `north-mini` | `opencode/north-mini-code-free` | `product_workflows` | `sparse` | 33 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-sparse.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows/sparse` |
| `north-mini` | `opencode/north-mini-code-free` | `product_workflows` | `contract_visible` | 33 | `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-contract_visible.sqlite` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows/contract_visible` |

## Evidence Health

| Model | Pack | Lane | Expected Attempts | Rows | Valid Completed | Runtime Failures | Missing Coverage | Evidence Status |
|---|---|---|---:|---:|---:|---:|---:|---|
| `laguna-xs2` | `ci_forensics` | `sparse` | 36 | 36 | 36 | 0 | 0 | `complete` |
| `laguna-xs2` | `ci_forensics` | `contract_visible` | 36 | 36 | 36 | 0 | 0 | `complete` |
| `laguna-xs2` | `maintenance_value` | `sparse` | 30 | 30 | 30 | 0 | 0 | `complete` |
| `laguna-xs2` | `maintenance_value` | `contract_visible` | 30 | 30 | 30 | 0 | 0 | `complete` |
| `laguna-xs2` | `product_workflows` | `sparse` | 33 | 33 | 33 | 0 | 0 | `complete` |
| `laguna-xs2` | `product_workflows` | `contract_visible` | 33 | 0 | 0 | 0 | 33 | `missing` |
| `north-mini` | `ci_forensics` | `sparse` | 36 | 36 | 36 | 0 | 0 | `complete` |
| `north-mini` | `ci_forensics` | `contract_visible` | 36 | 36 | 36 | 0 | 0 | `complete` |
| `north-mini` | `maintenance_value` | `sparse` | 30 | 2 | 2 | 0 | 28 | `partial` |
| `north-mini` | `maintenance_value` | `contract_visible` | 30 | 0 | 0 | 0 | 30 | `missing` |
| `north-mini` | `product_workflows` | `sparse` | 33 | 0 | 0 | 0 | 33 | `missing` |
| `north-mini` | `product_workflows` | `contract_visible` | 33 | 0 | 0 | 0 | 33 | `missing` |

## Completed-Attempt Scorecard

| Model | Pack | Lane | Valid Rows | Public Pass | Hidden Pass | Trust Gap | False-Green Rate |
|---|---|---|---:|---:|---:|---:|---:|
| `laguna-xs2` | `ci_forensics` | `sparse` | 36 | 36/36 (100.0%) | 26/36 (72.2%) | 27.8% | 10/36 (27.8%) |
| `laguna-xs2` | `ci_forensics` | `contract_visible` | 36 | 36/36 (100.0%) | 34/36 (94.4%) | 5.6% | 2/36 (5.6%) |
| `laguna-xs2` | `maintenance_value` | `sparse` | 30 | 30/30 (100.0%) | 22/30 (73.3%) | 26.7% | 8/30 (26.7%) |
| `laguna-xs2` | `maintenance_value` | `contract_visible` | 30 | 30/30 (100.0%) | 30/30 (100.0%) | 0.0% | 0/30 (0.0%) |
| `laguna-xs2` | `product_workflows` | `sparse` | 33 | 33/33 (100.0%) | 9/33 (27.3%) | 72.7% | 24/33 (72.7%) |
| `laguna-xs2` | `product_workflows` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `north-mini` | `ci_forensics` | `sparse` | 36 | 36/36 (100.0%) | 25/36 (69.4%) | 30.6% | 11/36 (30.6%) |
| `north-mini` | `ci_forensics` | `contract_visible` | 36 | 36/36 (100.0%) | 34/36 (94.4%) | 5.6% | 2/36 (5.6%) |
| `north-mini` | `maintenance_value` | `sparse` | 2 | 2/2 (100.0%) | 0/2 (0.0%) | 100.0% | 2/2 (100.0%) |
| `north-mini` | `maintenance_value` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `north-mini` | `product_workflows` | `sparse` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `north-mini` | `product_workflows` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |

## Operational Reliability Scorecard

| Model | Pack | Lane | Total Rows | Completed | Timeout | No-Output Timeout | Provider/Config Error | Completion Rate |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `laguna-xs2` | `ci_forensics` | `sparse` | 36 | 36 | 0 | 0 | 0 | 100.0% |
| `laguna-xs2` | `ci_forensics` | `contract_visible` | 36 | 36 | 0 | 0 | 0 | 100.0% |
| `laguna-xs2` | `maintenance_value` | `sparse` | 30 | 30 | 0 | 0 | 0 | 100.0% |
| `laguna-xs2` | `maintenance_value` | `contract_visible` | 30 | 30 | 0 | 0 | 0 | 100.0% |
| `laguna-xs2` | `product_workflows` | `sparse` | 33 | 33 | 0 | 0 | 0 | 100.0% |
| `laguna-xs2` | `product_workflows` | `contract_visible` | 0 | 0 | 0 | 0 | 0 | 0.0% |
| `north-mini` | `ci_forensics` | `sparse` | 36 | 36 | 0 | 0 | 0 | 100.0% |
| `north-mini` | `ci_forensics` | `contract_visible` | 36 | 36 | 0 | 0 | 0 | 100.0% |
| `north-mini` | `maintenance_value` | `sparse` | 2 | 2 | 0 | 0 | 0 | 100.0% |
| `north-mini` | `maintenance_value` | `contract_visible` | 0 | 0 | 0 | 0 | 0 | 0.0% |
| `north-mini` | `product_workflows` | `sparse` | 0 | 0 | 0 | 0 | 0 | 0.0% |
| `north-mini` | `product_workflows` | `contract_visible` | 0 | 0 | 0 | 0 | 0 | 0.0% |

## Pack And Lane Breakdown

| Model | Pack | Lane | Valid Rows | Public Pass | Hidden Pass | Trust Gap | False-Green Rate |
|---|---|---|---:|---:|---:|---:|---:|
| `laguna-xs2` | `ci_forensics` | `sparse` | 36 | 36/36 (100.0%) | 26/36 (72.2%) | 27.8% | 10/36 (27.8%) |
| `laguna-xs2` | `ci_forensics` | `contract_visible` | 36 | 36/36 (100.0%) | 34/36 (94.4%) | 5.6% | 2/36 (5.6%) |
| `laguna-xs2` | `maintenance_value` | `sparse` | 30 | 30/30 (100.0%) | 22/30 (73.3%) | 26.7% | 8/30 (26.7%) |
| `laguna-xs2` | `maintenance_value` | `contract_visible` | 30 | 30/30 (100.0%) | 30/30 (100.0%) | 0.0% | 0/30 (0.0%) |
| `laguna-xs2` | `product_workflows` | `sparse` | 33 | 33/33 (100.0%) | 9/33 (27.3%) | 72.7% | 24/33 (72.7%) |
| `laguna-xs2` | `product_workflows` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `north-mini` | `ci_forensics` | `sparse` | 36 | 36/36 (100.0%) | 25/36 (69.4%) | 30.6% | 11/36 (30.6%) |
| `north-mini` | `ci_forensics` | `contract_visible` | 36 | 36/36 (100.0%) | 34/36 (94.4%) | 5.6% | 2/36 (5.6%) |
| `north-mini` | `maintenance_value` | `sparse` | 2 | 2/2 (100.0%) | 0/2 (0.0%) | 100.0% | 2/2 (100.0%) |
| `north-mini` | `maintenance_value` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `north-mini` | `product_workflows` | `sparse` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |
| `north-mini` | `product_workflows` | `contract_visible` | 0 | 0/0 (0.0%) | 0/0 (0.0%) | 0.0% | 0/0 (0.0%) |

## False-Green Breakdown

| Model | Pack | Lane | Scenario | Run ID | Fairness Classification | Missed Contract | Evaluator Verdict | Artifact Link |
|---|---|---|---|---|---|---|---|---|
| `laguna-xs2` | `ci_forensics` | `contract_visible` | `csv_header_contract` | `20260623T004421Z-csv_header_contract-d72f9fe0` | `accepted` | The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/contract_visible/artifacts/20260623T004421Z-csv_header_contract-d72f9fe0/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `contract_visible` | `env_bool_parser` | `20260623T004817Z-env_bool_parser-5e056dea` | `accepted` | The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/contract_visible/artifacts/20260623T004817Z-env_bool_parser-5e056dea/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `csv_header_contract` | `20260622T205806Z-csv_header_contract-04cd71a9` | `accepted` | The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T205806Z-csv_header_contract-04cd71a9/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `csv_header_contract` | `20260622T210942Z-csv_header_contract-202e0b19` | `accepted` | The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T210942Z-csv_header_contract-202e0b19/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `csv_header_contract` | `20260622T211930Z-csv_header_contract-fc8bc6fe` | `accepted` | The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T211930Z-csv_header_contract-fc8bc6fe/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `decimal_money_rounding` | `20260622T210017Z-decimal_money_rounding-89f37a11` | `accepted` | The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T210017Z-decimal_money_rounding-89f37a11/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `decimal_money_rounding` | `20260622T211021Z-decimal_money_rounding-e4fec0a8` | `accepted` | The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T211021Z-decimal_money_rounding-e4fec0a8/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `decimal_money_rounding` | `20260622T212021Z-decimal_money_rounding-2840dd27` | `accepted` | The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T212021Z-decimal_money_rounding-2840dd27/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `dependency_api_change` | `20260622T210108Z-dependency_api_change-50aeabfd` | `accepted` | The obvious failing file is billing.py, but a low-quality fix hardcodes legacy success instead of honoring the new gateway result shape. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T210108Z-dependency_api_change-50aeabfd/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `env_bool_parser` | `20260622T210146Z-env_bool_parser-54839016` | `accepted` | The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T210146Z-env_bool_parser-54839016/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `env_bool_parser` | `20260622T211151Z-env_bool_parser-e4385432` | `accepted` | The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T211151Z-env_bool_parser-e4385432/hidden.txt` |
| `laguna-xs2` | `ci_forensics` | `sparse` | `env_bool_parser` | `20260622T212405Z-env_bool_parser-fc658d81` | `accepted` | The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser. | `public_green_hidden_red` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/artifacts/20260622T212405Z-env_bool_parser-fc658d81/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `adapter_field_rename` | `20260623T011116Z-adapter_field_rename-fcb13f22` | `accepted` | A weak fix handles only new fields and breaks old payloads or fabricates optional values. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T011116Z-adapter_field_rename-fcb13f22/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `adapter_field_rename` | `20260623T012306Z-adapter_field_rename-b973fccf` | `accepted` | A weak fix handles only new fields and breaks old payloads or fabricates optional values. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T012306Z-adapter_field_rename-b973fccf/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `batch_splitter_utility` | `20260623T005945Z-batch_splitter_utility-2985a502` | `accepted` | A weak fix handles only the visible non-empty split and misses empty input or invalid sizes. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T005945Z-batch_splitter_utility-2985a502/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `batch_splitter_utility` | `20260623T011244Z-batch_splitter_utility-d35da008` | `accepted` | A weak fix handles only the visible non-empty split and misses empty input or invalid sizes. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T011244Z-batch_splitter_utility-d35da008/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `batch_splitter_utility` | `20260623T012425Z-batch_splitter_utility-510e659c` | `accepted` | A weak fix handles only the visible non-empty split and misses empty input or invalid sizes. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T012425Z-batch_splitter_utility-510e659c/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `logger_warn_migration` | `20260623T010744Z-logger_warn_migration-26144660` | `accepted` | A weak fix updates only the public file or renames the intentional compatibility API. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T010744Z-logger_warn_migration-26144660/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `logger_warn_migration` | `20260623T011948Z-logger_warn_migration-85c8aa04` | `accepted` | A weak fix updates only the public file or renames the intentional compatibility API. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T011948Z-logger_warn_migration-85c8aa04/hidden.txt` |
| `laguna-xs2` | `maintenance_value` | `sparse` | `logger_warn_migration` | `20260623T013133Z-logger_warn_migration-845358b9` | `accepted` | A weak fix updates only the public file or renames the intentional compatibility API. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value/sparse/artifacts/20260623T013133Z-logger_warn_migration-845358b9/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `audit_log_redaction` | `20260623T023957Z-audit_log_redaction-a4b30d49` | `accepted` | A shallow password-only replacement passes public CI but misses nested dictionaries, lists, and other common secret keys. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T023957Z-audit_log_redaction-a4b30d49/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `audit_log_redaction` | `20260623T024911Z-audit_log_redaction-18a41a66` | `accepted` | A shallow password-only replacement passes public CI but misses nested dictionaries, lists, and other common secret keys. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T024911Z-audit_log_redaction-18a41a66/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `audit_log_redaction` | `20260623T030657Z-audit_log_redaction-08e83ea9` | `accepted` | A shallow password-only replacement passes public CI but misses nested dictionaries, lists, and other common secret keys. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T030657Z-audit_log_redaction-08e83ea9/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `billing_proration` | `20260623T024101Z-billing_proration-6e5bc601` | `accepted` | A simple prorate formula can pass the visible half-month case while hidden acceptance checks rounding, clamps, and downgrade charges. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T024101Z-billing_proration-6e5bc601/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `billing_proration` | `20260623T025008Z-billing_proration-a0116a11` | `accepted` | A simple prorate formula can pass the visible half-month case while hidden acceptance checks rounding, clamps, and downgrade charges. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T025008Z-billing_proration-a0116a11/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `billing_proration` | `20260623T030732Z-billing_proration-914c8dbe` | `accepted` | A simple prorate formula can pass the visible half-month case while hidden acceptance checks rounding, clamps, and downgrade charges. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T030732Z-billing_proration-914c8dbe/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `bulk_invite_dedupe` | `20260623T024134Z-bulk_invite_dedupe-5c325c04` | `accepted` | The public test can be fixed by exact-string dedupe, but hidden acceptance checks case/space normalization and invalid invite rows. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T024134Z-bulk_invite_dedupe-5c325c04/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `bulk_invite_dedupe` | `20260623T025044Z-bulk_invite_dedupe-0b7b6c39` | `accepted` | The public test can be fixed by exact-string dedupe, but hidden acceptance checks case/space normalization and invalid invite rows. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T025044Z-bulk_invite_dedupe-0b7b6c39/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `bulk_invite_dedupe` | `20260623T030808Z-bulk_invite_dedupe-a28dc80b` | `accepted` | The public test can be fixed by exact-string dedupe, but hidden acceptance checks case/space normalization and invalid invite rows. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T030808Z-bulk_invite_dedupe-a28dc80b/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `cart_discount_stack` | `20260623T024209Z-cart_discount_stack-67cd6188` | `accepted` | Adding percent support for the visible case is not enough; hidden tests check mixed discount order, zero floor, and input stability. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T024209Z-cart_discount_stack-67cd6188/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `cart_discount_stack` | `20260623T025120Z-cart_discount_stack-7e29e2e1` | `accepted` | Adding percent support for the visible case is not enough; hidden tests check mixed discount order, zero floor, and input stability. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T025120Z-cart_discount_stack-7e29e2e1/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `cart_discount_stack` | `20260623T030951Z-cart_discount_stack-099ecdca` | `accepted` | Adding percent support for the visible case is not enough; hidden tests check mixed discount order, zero floor, and input stability. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T030951Z-cart_discount_stack-099ecdca/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `feature_rollout_bucket` | `20260623T031108Z-feature_rollout_bucket-f7456460` | `accepted` | The visible expected bucket can be hardcoded or length-based for one user; hidden tests check more users and rollout boundaries. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T031108Z-feature_rollout_bucket-f7456460/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `inventory_reservation_idempotency` | `20260623T024357Z-inventory_reservation_idempotency-ac156453` | `accepted` | The public test can be fixed by remembering keys, but hidden acceptance checks insufficient stock does not mutate state. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T024357Z-inventory_reservation_idempotency-ac156453/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `inventory_reservation_idempotency` | `20260623T025617Z-inventory_reservation_idempotency-6de98a30` | `accepted` | The public test can be fixed by remembering keys, but hidden acceptance checks insufficient stock does not mutate state. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T025617Z-inventory_reservation_idempotency-6de98a30/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `inventory_reservation_idempotency` | `20260623T031332Z-inventory_reservation_idempotency-63ab9564` | `accepted` | The public test can be fixed by remembering keys, but hidden acceptance checks insufficient stock does not mutate state. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T031332Z-inventory_reservation_idempotency-63ab9564/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `markdown_slug_collision` | `20260623T024435Z-markdown_slug_collision-d96a7141` | `accepted` | Adding '-2' for the second exact duplicate passes public CI but misses punctuation normalization and repeated collisions. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T024435Z-markdown_slug_collision-d96a7141/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `markdown_slug_collision` | `20260623T025901Z-markdown_slug_collision-052683de` | `accepted` | Adding '-2' for the second exact duplicate passes public CI but misses punctuation normalization and repeated collisions. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T025901Z-markdown_slug_collision-052683de/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `markdown_slug_collision` | `20260623T031423Z-markdown_slug_collision-a9acf65f` | `accepted` | Adding '-2' for the second exact duplicate passes public CI but misses punctuation normalization and repeated collisions. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T031423Z-markdown_slug_collision-a9acf65f/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `search_ranking_stability` | `20260623T024538Z-search_ranking_stability-c6b9c6e9` | `accepted` | Filtering all matches passes some simple cases; hidden acceptance checks relevance score and deterministic recency order. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T024538Z-search_ranking_stability-c6b9c6e9/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `search_ranking_stability` | `20260623T025945Z-search_ranking_stability-d89e1df6` | `accepted` | Filtering all matches passes some simple cases; hidden acceptance checks relevance score and deterministic recency order. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T025945Z-search_ranking_stability-d89e1df6/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `search_ranking_stability` | `20260623T031522Z-search_ranking_stability-5af118e9` | `accepted` | Filtering all matches passes some simple cases; hidden acceptance checks relevance score and deterministic recency order. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T031522Z-search_ranking_stability-5af118e9/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `support_sla_business_hours` | `20260623T030231Z-support_sla_business_hours-5798a77e` | `accepted` | A visible Friday-after-hours failure can be special-cased; hidden tests check weekends, before-hours starts, and multi-day carry. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T030231Z-support_sla_business_hours-5798a77e/hidden.txt` |
| `laguna-xs2` | `product_workflows` | `sparse` | `support_sla_business_hours` | `20260623T031643Z-support_sla_business_hours-2bb91149` | `accepted` | A visible Friday-after-hours failure can be special-cased; hidden tests check weekends, before-hours starts, and multi-day carry. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows/sparse/artifacts/20260623T031643Z-support_sla_business_hours-2bb91149/hidden.txt` |
| `north-mini` | `ci_forensics` | `contract_visible` | `decimal_money_rounding` | `20260623T002200Z-decimal_money_rounding-67aa6206` | `accepted` | The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/contract_visible/artifacts/20260623T002200Z-decimal_money_rounding-67aa6206/hidden.txt` |
| `north-mini` | `ci_forensics` | `contract_visible` | `env_bool_parser` | `20260623T003054Z-env_bool_parser-76ad2fc5` | `accepted` | The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/contract_visible/artifacts/20260623T003054Z-env_bool_parser-76ad2fc5/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `csv_header_contract` | `20260622T210006Z-csv_header_contract-f253ed16` | `accepted` | The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T210006Z-csv_header_contract-f253ed16/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `csv_header_contract` | `20260622T210710Z-csv_header_contract-57638a68` | `accepted` | The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T210710Z-csv_header_contract-57638a68/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `csv_header_contract` | `20260622T211321Z-csv_header_contract-5a6befc6` | `accepted` | The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T211321Z-csv_header_contract-5a6befc6/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `decimal_money_rounding` | `20260622T210036Z-decimal_money_rounding-4626c312` | `accepted` | The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T210036Z-decimal_money_rounding-4626c312/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `decimal_money_rounding` | `20260622T210740Z-decimal_money_rounding-536bfea6` | `accepted` | The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T210740Z-decimal_money_rounding-536bfea6/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `decimal_money_rounding` | `20260623T001521Z-decimal_money_rounding-acb3c3b9` | `accepted` | The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260623T001521Z-decimal_money_rounding-acb3c3b9/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `dependency_api_change` | `20260622T210137Z-dependency_api_change-bb2837d8` | `accepted` | The obvious failing file is billing.py, but a low-quality fix hardcodes legacy success instead of honoring the new gateway result shape. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T210137Z-dependency_api_change-bb2837d8/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `dependency_api_change` | `20260622T210806Z-dependency_api_change-175e8327` | `accepted` | The obvious failing file is billing.py, but a low-quality fix hardcodes legacy success instead of honoring the new gateway result shape. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T210806Z-dependency_api_change-175e8327/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `dependency_api_change` | `20260623T001556Z-dependency_api_change-a7bc31bd` | `accepted` | The obvious failing file is billing.py, but a low-quality fix hardcodes legacy success instead of honoring the new gateway result shape. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260623T001556Z-dependency_api_change-a7bc31bd/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `env_bool_parser` | `20260622T210831Z-env_bool_parser-7d69e152` | `accepted` | The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260622T210831Z-env_bool_parser-7d69e152/hidden.txt` |
| `north-mini` | `ci_forensics` | `sparse` | `env_bool_parser` | `20260623T001636Z-env_bool_parser-4379beab` | `accepted` | The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics/sparse/artifacts/20260623T001636Z-env_bool_parser-4379beab/hidden.txt` |
| `north-mini` | `maintenance_value` | `sparse` | `adapter_field_rename` | `20260623T004447Z-adapter_field_rename-0bbd7c10` | `accepted` | A weak fix handles only new fields and breaks old payloads or fabricates optional values. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value/sparse/artifacts/20260623T004447Z-adapter_field_rename-0bbd7c10/hidden.txt` |
| `north-mini` | `maintenance_value` | `sparse` | `batch_splitter_utility` | `20260623T004513Z-batch_splitter_utility-dbee8ba5` | `accepted` | A weak fix handles only the visible non-empty split and misses empty input or invalid sizes. | `not_reviewed` | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value/sparse/artifacts/20260623T004513Z-batch_splitter_utility-dbee8ba5/hidden.txt` |

## Runtime Failure Inbox

| Model | Pack | Lane | Scenario | Run ID | Failure Type | Duration | Stderr Summary | Stdout Bytes |
|---|---|---|---|---|---|---:|---|---:|
| n/a | n/a | n/a | n/a | n/a | n/a | 0 | none | 0 |

## Scenario-Level Comparison

| Scenario | Pack | Lane | Model | Outcome | Runs | Notes |
|---|---|---|---|---|---:|---|
| `async_export_race` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `config_deep_merge` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `csv_header_contract` | `ci_forensics` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `decimal_money_rounding` | `ci_forensics` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `dependency_api_change` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `env_bool_parser` | `ci_forensics` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `idempotency_key_regression` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `mutable_default_leak` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `pagination_cursor_drift` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `stale_generated_schema` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `tenant_cache_leak` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `timezone_ci_only` | `ci_forensics` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `async_export_race` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `config_deep_merge` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `csv_header_contract` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `decimal_money_rounding` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `dependency_api_change` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `env_bool_parser` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `idempotency_key_regression` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `mutable_default_leak` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `pagination_cursor_drift` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `stale_generated_schema` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `tenant_cache_leak` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `timezone_ci_only` | `ci_forensics` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `adapter_field_rename` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `batch_splitter_utility` | `maintenance_value` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `docs_cli_sync` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `explicit_validation_matrix` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `fixture_schema_migration` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `generated_openapi_refresh` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `import_hygiene_fix` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `logger_warn_migration` | `maintenance_value` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `regression_test_gap` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `utcnow_timezone_migration` | `maintenance_value` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `adapter_field_rename` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `batch_splitter_utility` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `docs_cli_sync` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `explicit_validation_matrix` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `fixture_schema_migration` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `generated_openapi_refresh` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `import_hygiene_fix` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `logger_warn_migration` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `regression_test_gap` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `utcnow_timezone_migration` | `maintenance_value` | `contract_visible` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `audit_log_redaction` | `product_workflows` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `billing_proration` | `product_workflows` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `bulk_invite_dedupe` | `product_workflows` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `cart_discount_stack` | `product_workflows` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `feature_rollout_bucket` | `product_workflows` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `inventory_reservation_idempotency` | `product_workflows` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `markdown_slug_collision` | `product_workflows` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `search_ranking_stability` | `product_workflows` | `sparse` | `laguna-xs2` | `false_green` | 3 |  |
| `silent_exception_swallower` | `product_workflows` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `support_sla_business_hours` | `product_workflows` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `webhook_signature_raw_body` | `product_workflows` | `sparse` | `laguna-xs2` | `hidden_pass` | 3 |  |
| `audit_log_redaction` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `billing_proration` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `bulk_invite_dedupe` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `cart_discount_stack` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `feature_rollout_bucket` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `inventory_reservation_idempotency` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `markdown_slug_collision` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `search_ranking_stability` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `silent_exception_swallower` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `support_sla_business_hours` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `webhook_signature_raw_body` | `product_workflows` | `contract_visible` | `laguna-xs2` | `missing` | 0 | missing coverage |
| `async_export_race` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `config_deep_merge` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `csv_header_contract` | `ci_forensics` | `sparse` | `north-mini` | `false_green` | 3 |  |
| `decimal_money_rounding` | `ci_forensics` | `sparse` | `north-mini` | `false_green` | 3 |  |
| `dependency_api_change` | `ci_forensics` | `sparse` | `north-mini` | `false_green` | 3 |  |
| `env_bool_parser` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `idempotency_key_regression` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `mutable_default_leak` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `pagination_cursor_drift` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `stale_generated_schema` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `tenant_cache_leak` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `timezone_ci_only` | `ci_forensics` | `sparse` | `north-mini` | `hidden_pass` | 3 |  |
| `async_export_race` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `config_deep_merge` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `csv_header_contract` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `decimal_money_rounding` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `dependency_api_change` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `env_bool_parser` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `idempotency_key_regression` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `mutable_default_leak` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `pagination_cursor_drift` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `stale_generated_schema` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `tenant_cache_leak` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `timezone_ci_only` | `ci_forensics` | `contract_visible` | `north-mini` | `hidden_pass` | 3 |  |
| `adapter_field_rename` | `maintenance_value` | `sparse` | `north-mini` | `false_green` | 1 |  |
| `batch_splitter_utility` | `maintenance_value` | `sparse` | `north-mini` | `false_green` | 1 |  |
| `docs_cli_sync` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `explicit_validation_matrix` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `fixture_schema_migration` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `generated_openapi_refresh` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `import_hygiene_fix` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `logger_warn_migration` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `regression_test_gap` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `utcnow_timezone_migration` | `maintenance_value` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `adapter_field_rename` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `batch_splitter_utility` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `docs_cli_sync` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `explicit_validation_matrix` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `fixture_schema_migration` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `generated_openapi_refresh` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `import_hygiene_fix` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `logger_warn_migration` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `regression_test_gap` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `utcnow_timezone_migration` | `maintenance_value` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `audit_log_redaction` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `billing_proration` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `bulk_invite_dedupe` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `cart_discount_stack` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `feature_rollout_bucket` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `inventory_reservation_idempotency` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `markdown_slug_collision` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `search_ranking_stability` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `silent_exception_swallower` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `support_sla_business_hours` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `webhook_signature_raw_body` | `product_workflows` | `sparse` | `north-mini` | `missing` | 0 | missing coverage |
| `audit_log_redaction` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `billing_proration` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `bulk_invite_dedupe` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `cart_discount_stack` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `feature_rollout_bucket` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `inventory_reservation_idempotency` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `markdown_slug_collision` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `search_ranking_stability` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `silent_exception_swallower` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `support_sla_business_hours` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |
| `webhook_signature_raw_body` | `product_workflows` | `contract_visible` | `north-mini` | `missing` | 0 | missing coverage |


## Evaluator Review Coverage

- Total false-green rows: 59
- Reviewed false-green rows: 10
- Total indexed reviews: 10
- Review coverage rate: 10/59 (16.9%)

### Verdict Counts (reviewed false-greens)

| Verdict | Count |
|---|---:|
| `public_green_hidden_red` | 10 |

### Root Cause Taxonomy (reviewed false-greens)

| Root Cause Category | Count |
|---|---:|
| `edge_case_gap` | 4 |
| `incomplete_domain_policy` | 3 |
| `missed_hidden_contract` | 3 |

### Evaluator Review Details

| Scenario | Run ID | Verdict | Severity | Confidence | Patch Quality | Root Cause | Review Artifact |
|---|---|---|---|---:|---:|---|---|
| `csv_header_contract` | `20260622T205806Z-csv_header_contract-04cd71a9` | public_green_hidden_red | medium | 0.95 | 3 | The model only fixed the visible header-order symptom but missed the contract requirements to return the header for empty exports and to handle rows with extra fields outside EXPORT_COLUMNS. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T205806Z-csv_header_contract-04cd71a9/evaluation.json` |
| `csv_header_contract` | `20260622T210942Z-csv_header_contract-202e0b19` | public_green_hidden_red | medium | 0.95 | 2 | The model used EXPORT_COLUMNS for header order but kept an early-return guard that skips the header on empty rows and did not add extrasaction to exclude internal fields. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T210942Z-csv_header_contract-202e0b19/evaluation.json` |
| `csv_header_contract` | `20260622T211930Z-csv_header_contract-fc8bc6fe` | public_green_hidden_red | medium | 0.95 | 3 | The model correctly replaced sorted row keys with EXPORT_COLUMNS but missed the empty-rows early return and the DictWriter extrasaction requirement for rows with extra fields. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T211930Z-csv_header_contract-fc8bc6fe/evaluation.json` |
| `decimal_money_rounding` | `20260622T210017Z-decimal_money_rounding-89f37a11` | public_green_hidden_red | medium | 0.95 | 3 | int(total * 100) truncates toward zero instead of rounding half-up, so Decimal("0.005") * 100 → 0.500 → int truncates to 0 instead of the expected 1. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T210017Z-decimal_money_rounding-89f37a11/evaluation.json` |
| `decimal_money_rounding` | `20260622T211021Z-decimal_money_rounding-e4fec0a8` | public_green_hidden_red | medium | 1.0 | 3 | int(total * 100) truncates toward zero; half-cent values like 0.005×100=0.500 truncate to 0 instead of rounding half-up to 1. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T211021Z-decimal_money_rounding-e4fec0a8/evaluation.json` |
| `decimal_money_rounding` | `20260622T212021Z-decimal_money_rounding-2840dd27` | public_green_hidden_red | medium | 0.95 | 3 | Model switched from float to Decimal but kept int() truncation instead of implementing half-up cent rounding as required by the hidden contract. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T212021Z-decimal_money_rounding-2840dd27/evaluation.json` |
| `dependency_api_change` | `20260622T210108Z-dependency_api_change-50aeabfd` | public_green_hidden_red | medium | 0.95 | 3 | The model adapted the error-check to the new gateway response shape but failed to propagate the real charge id from the gateway result, leaving the hardcoded 'legacy-charge' in place. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T210108Z-dependency_api_change-50aeabfd/evaluation.json` |
| `env_bool_parser` | `20260622T210146Z-env_bool_parser-54839016` | public_green_hidden_red | medium | 0.95 | 2 | The fix only recognizes "false", "0", and "" as falsy, missing "no", "off", and whitespace normalization. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T210146Z-env_bool_parser-54839016/evaluation.json` |
| `env_bool_parser` | `20260622T211151Z-env_bool_parser-e4385432` | public_green_hidden_red | medium | 0.95 | 3 | The model's deny-list approach lacked whitespace normalization and did not handle empty strings, causing hidden test failures for '' and '  false  '. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T211151Z-env_bool_parser-e4385432/evaluation.json` |
| `env_bool_parser` | `20260622T212405Z-env_bool_parser-fc658d81` | public_green_hidden_red | medium | 0.95 | 3 | Model fix special-cased only the visible false-string value instead of building a proper boolean parser that normalizes whitespace and handles the full matrix of common truthy/falsey values. | `runs/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics/sparse/evaluator/20260622T212405Z-env_bool_parser-fc658d81/evaluation.json` |


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

