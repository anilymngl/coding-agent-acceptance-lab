# North Mini Code Evidence Pack

## Executive Claim

North Mini Code is operationally competent but semantically premature: it reliably performs the
OpenCode repository-repair loop, but often stops at public-test success instead of inferring the
full domain or architectural contract.

This is a behavior microscope, not a public leaderboard benchmark. The defensible claim is about
the trust gap between visible CI success and hidden acceptance on this curated local eval.

## Model-Card Connection

Cohere describes North Mini Code as `north-mini-code-1-0`, a 30B total / 3B active MoE model
trained for agentic coding, with a 256K context window and 64K max output tokens. The official
page explicitly names repo-level changes in harnesses like SWE-Agent and OpenCode as intended
uses. The page checked on 2026-06-20 did not provide a numeric benchmark table, so this report
does not claim official accuracy numbers.

Sources: https://docs.cohere.com/docs/north-mini-code-1.0, https://opencode.ai/docs/,
https://www.swebench.com/, https://www.tbench.ai/

## Methodology

- The model saw only visible challenge repos and public tests during the OpenCode call.
- The harness captured prompt, raw OpenCode stream, patch, public output, hidden output, and artifact paths.
- Hidden tests were injected only after the agent exited.
- Evaluator-agent reviews are indexed from validated `evaluation.json` files and preserve raw working boards/streams.
- Headline metrics use only scenarios whose audit status is `accepted`.

## Scorecard

| Metric | Value |
|---|---:|
| Runs | 27 |
| Public pass | 26/27 (96.3%) |
| Hidden pass | 12/27 (44.4%) |
| Trust gap | 51.9% |
| Public-green / hidden-red | 14/27 |
| False-green rate | 14/26 (53.8%) |
| Public-red rate | 3.7% |
| Severity-weighted hidden-failure rate | 60.8% |

The central diagnostic is the false-green rate: public tests passed but hidden acceptance failed.
Combined accepted rows: 14/26 public-green runs were hidden-red.

## Product Workflow Stress Read

Product workflow false-green rate: 9/10 (90.0%).

This pack is the strongest evidence that the weakness is semantic density, not repo scale.

## Strong-Model Control Snapshot

One product-workflow control run is included as a calibration check, not as a leaderboard result.
It asks whether the pack is broadly hard or uniquely exposing North Mini Code.

| Control Model | Runs | Public | Hidden | Trust Gap | False Green Rate |
|---|---:|---:|---:|---:|---:|
| `deepseek/deepseek-v4-pro` | 11 | 11/11 | 3/11 | 72.7% | 8/11 (72.7%) |

Interpretation: this control suggests the product-workflow pack is genuinely difficult,
so North Mini's failures should be framed as a trust-gap microscope result first, not as
a complete model-ranking claim.

## Pack Breakdown

| Pack | Runs | Public | Hidden | Trust Gap | False Green Rate |
|---|---:|---:|---:|---:|---:|
| `ci_forensics` | 12 | 12/12 | 8/12 | 33.3% | 4/12 (33.3%) |
| `data_semantics` | 4 | 4/4 | 3/4 | 25.0% | 1/4 (25.0%) |
| `product_workflows` | 11 | 10/11 | 1/11 | 81.8% | 9/10 (90.0%) |

## Evaluator-Agent Taxonomy

Public-green/hidden-red target runs reviewed: 14/14 (21 review rows indexed).

| Root Cause Category | Reviews |
|---|---:|
| `missed_hidden_contract` | 5 |
| `edge_case_gap` | 4 |
| `incomplete_domain_policy` | 4 |
| `wrong_fix_strategy` | 1 |

### Evaluator Review Details

| Scenario | Verdict | Severity | Confidence | Patch Quality | Root Cause | Review Artifact |
|---|---|---|---:|---:|---|---|
| `audit_log_redaction` | public_green_hidden_red | high | 0.98 | 2 | The model only redacts top-level 'password' without recursively walking nested dictionaries or lists, missing api_key, token, and authorization keys. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125858Z-audit_log_redaction-9f29e7b1/evaluation.json` |
| `billing_proration` | public_green_hidden_red | medium | 0.95 | 2 | The patch uses int() truncation instead of half-up rounding, returns 0 instead of full charge when unused_days exceeds period_days, and returns negative values for downgrades. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125907Z-billing_proration-bcdb9b72/evaluation.json` |
| `bulk_invite_dedupe` | public_green_hidden_red | high | 0.95 | 2 | The model only implemented exact-string deduplication and failed to normalize email addresses or filter out invalid rows. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125925Z-bulk_invite_dedupe-bad578fa/evaluation.json` |
| `cart_discount_stack` | public_green_hidden_red | medium | 0.95 | 3 | The model added percent discount support but failed to implement the zero-floor requirement, allowing negative totals when discounts exceed the subtotal. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125938Z-cart_discount_stack-4c06770e/evaluation.json` |
| `csv_header_contract` | public_green_hidden_red | medium | 0.95 | 3 | Model replaced sorted keys with EXPORT_COLUMNS but kept the early empty-return guard and omitted extrasaction='ignore', causing empty-exports to lose the header and extra-field rows to crash. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002632Z-csv_header_contract-852f41d2/evaluation.json` |
| `decimal_money_rounding` | public_green_hidden_red | medium | 0.95 | 3 | The model switched float to Decimal but kept int() truncation instead of proper half-up cent rounding. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002646Z-decimal_money_rounding-1032440a/evaluation.json` |
| `dependency_api_change` | public_green_hidden_red | medium | 0.95 | 3 | Model fixed the error-detection condition but left charge_id hardcoded as 'legacy-charge' instead of reading the real id from the gateway result dict. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002709Z-dependency_api_change-cc10ad9c/evaluation.json` |
| `env_bool_parser` | public_green_hidden_red | medium | 0.95 | 3 | The patch handles lowercase false strings but omits whitespace stripping and treats empty string as truthy. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002726Z-env_bool_parser-be27b3d6/evaluation.json` |
| `feature_rollout_bucket` | public_green_hidden_red | medium | 0.95 | 2 | Model used a naive character-position heuristic (ord of first char) instead of the required stable SHA-256 based bucket. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132042Z-feature_rollout_bucket-14ec6bee/evaluation.json` |
| `inventory_reservation_idempotency` | public_green_hidden_red | medium | 0.95 | 2 | The model added idempotency-key deduplication but failed to check stock availability before decrementing, so insufficient-stock reservations return ok: True and mutate stock. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132110Z-inventory_reservation_idempotency-3aec4411/evaluation.json` |
| `markdown_slug_collision` | public_green_hidden_red | medium | 0.95 | 2 | The model added duplicate suffix counting in table_of_contents but left heading_slug with only space-based normalization, missing punctuation removal and whitespace/hyphen collapsing. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132139Z-markdown_slug_collision-6a73ae13/evaluation.json` |
| `metric_semantic_mismatch` | public_green_hidden_red | medium | 0.95 | 3 | The model placed unit normalization inside compute() instead of dashboard_total(), causing compute() to return normalized values when the hidden contract requires raw source values. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T012118Z-metric_semantic_mismatch-bfecbeae/evaluation.json` |
| `search_ranking_stability` | public_green_hidden_red | medium | 0.95 | 3 | The model patch separates title and body matches but does not sort within each group by published_at descending, violating the hidden contract tie-breaking rule. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132156Z-search_ranking_stability-a5f4d3a6/evaluation.json` |
| `support_sla_business_hours` | public_green_hidden_red | medium | 0.95 | 3 | The patch handles weekends and after-17:00 rollover but misses before-09:00 starts and minute-level precision, which are both exercised by the hidden test. | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132217Z-support_sla_business_hours-d705562d/evaluation.json` |

## Benchmark Quality Audit

Audit status counts: {'accepted': 27}

| Scenario | Status | Risk Area | Impact | Inferability | Hidden Legitimacy | Flexibility | Notes |
|---|---|---|---:|---:|---:|---:|---|
| `api_pagination_boundary` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `async_export_race` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `audit_log_redaction` | accepted | authorization_security | 5 | 4 | 4 | 4 | Nested secret redaction is security-sensitive and must be recursive. |
| `billing_proration` | accepted | financial | 5 | 4 | 4 | 4 | Proration has direct billing impact and must handle rounding, clamps, and downgrades. |
| `bulk_invite_dedupe` | accepted | data_integrity | 4 | 4 | 4 | 4 | Invite dedupe must normalize casing/spacing and reject invalid invite rows. |
| `cart_discount_stack` | accepted | financial | 4 | 4 | 4 | 4 | Discount policy must preserve ordering, zero floors, and input stability. |
| `config_deep_merge` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `csv_header_contract` | accepted | data_integrity | 4 | 4 | 4 | 4 | Export schema is a documented data contract across empty and extra-field cases. |
| `decimal_money_rounding` | accepted | financial | 5 | 4 | 4 | 4 | Financial correctness depends on explicit cent rounding policy. |
| `dependency_api_change` | accepted | compatibility | 4 | 4 | 4 | 4 | Dependency adapter must propagate the new response contract, not only pass the visible ok check. |
| `env_bool_parser` | accepted | business_correctness | 3 | 4 | 4 | 4 | Configuration parsing should normalize common string forms, blanks, and whitespace. |
| `feature_rollout_bucket` | accepted | business_correctness | 4 | 4 | 4 | 4 | Rollout buckets must be stable and respect percentage boundaries. |
| `idempotency_key_regression` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `inventory_reservation_idempotency` | accepted | state_corruption | 5 | 4 | 4 | 4 | Failed reservations must not mutate stock; retries must be idempotent. |
| `join_fanout` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `markdown_slug_collision` | accepted | compatibility | 3 | 4 | 4 | 4 | Slug generation must normalize punctuation and repeated collisions deterministically. |
| `metric_semantic_mismatch` | accepted | semantic_architecture | 5 | 4 | 4 | 4 | Challenge tests ownership of unit normalization between raw metric API and dashboard layer. |
| `mutable_default_leak` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `pagination_cursor_drift` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `scd_temporal_join` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `search_ranking_stability` | accepted | business_correctness | 4 | 4 | 4 | 4 | Ranking stability affects user-visible relevance and deterministic tie-breaks. |
| `silent_exception_swallower` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `stale_generated_schema` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `support_sla_business_hours` | accepted | business_correctness | 4 | 4 | 4 | 4 | SLA deadlines must respect business calendars and working-hour carry. |
| `tenant_cache_leak` | accepted | authorization_security | 5 | 4 | 4 | 4 | Tenant isolation failures can expose cross-tenant data. |
| `timezone_ci_only` | accepted | business_correctness | 3 | 4 | 4 | 4 | Default accepted audit seed; review before public benchmark release. |
| `webhook_signature_raw_body` | accepted | authorization_security | 5 | 4 | 4 | 4 | Signature verification must use exact raw bytes. |

## Claim Ledger

| Claim | Evidence | Source | Confidence | Caveat |
|---|---|---|---|---|
| Operational competence is strong | Public pass: 26/27 (96.3%) | SQLite run rows plus public output artifacts | high | Small curated local task set, not a broad benchmark. |
| Semantic trust gap is large | Trust gap: 51.9% | Public/hidden pass split after hidden test injection | high | Hidden tests are authored contracts; benchmark audit reduces but does not remove author bias. |
| Product workflows are the sharpest stressor | Product false-green: 9/10 (90.0%) | Rows where challenge_pack is product_workflows | high | Add control-model run before claiming difficulty is model-specific. |
| Evaluator-agent diagnostics are accountable | Public-green/hidden-red target runs reviewed: 14/14 | evaluator_reviews table plus raw review artifacts | medium | Single evaluator model; broader evaluator agreement remains future work. |

## What Can And Cannot Be Defended

**Can defend:** North Mini Code is highly effective at visible-feedback CI repair in this harness,
and the public-green/hidden-red split reveals a substantial trust gap on sparse semantic contracts.

**Cannot yet defend:** broad model leaderboard ranking, statistically stable pass rates, or claims
that these failures generalize to all coding workloads. Multi-seed runs and control models are still required.

## Artifact Index

| Run ID | Scenario | Prompt | Patch | Public Output | Hidden Output | Evaluator JSON | Patch SHA256 Prefix |
|---|---|---|---|---|---|---|---|
| `20260619T002607Z-async_export_race-ee56ebae` | `async_export_race` | `runs/north-mini-code-eval/artifacts/20260619T002607Z-async_export_race-ee56ebae/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002607Z-async_export_race-ee56ebae/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002607Z-async_export_race-ee56ebae/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002607Z-async_export_race-ee56ebae/hidden.txt` | `` | `752161c5fe94` |
| `20260619T002632Z-csv_header_contract-852f41d2` | `csv_header_contract` | `runs/north-mini-code-eval/artifacts/20260619T002632Z-csv_header_contract-852f41d2/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002632Z-csv_header_contract-852f41d2/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002632Z-csv_header_contract-852f41d2/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002632Z-csv_header_contract-852f41d2/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002632Z-csv_header_contract-852f41d2/evaluation.json` | `8f12b3614600` |
| `20260619T002646Z-decimal_money_rounding-1032440a` | `decimal_money_rounding` | `runs/north-mini-code-eval/artifacts/20260619T002646Z-decimal_money_rounding-1032440a/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002646Z-decimal_money_rounding-1032440a/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002646Z-decimal_money_rounding-1032440a/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002646Z-decimal_money_rounding-1032440a/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002646Z-decimal_money_rounding-1032440a/evaluation.json` | `9ca2b900d0a2` |
| `20260619T002709Z-dependency_api_change-cc10ad9c` | `dependency_api_change` | `runs/north-mini-code-eval/artifacts/20260619T002709Z-dependency_api_change-cc10ad9c/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002709Z-dependency_api_change-cc10ad9c/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002709Z-dependency_api_change-cc10ad9c/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002709Z-dependency_api_change-cc10ad9c/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002709Z-dependency_api_change-cc10ad9c/evaluation.json` | `f7d350b8574c` |
| `20260619T002726Z-env_bool_parser-be27b3d6` | `env_bool_parser` | `runs/north-mini-code-eval/artifacts/20260619T002726Z-env_bool_parser-be27b3d6/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002726Z-env_bool_parser-be27b3d6/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002726Z-env_bool_parser-be27b3d6/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002726Z-env_bool_parser-be27b3d6/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-primary-pghr/20260619T002726Z-env_bool_parser-be27b3d6/evaluation.json` | `109cfe082de7` |
| `20260619T002739Z-idempotency_key_regression-436e7772` | `idempotency_key_regression` | `runs/north-mini-code-eval/artifacts/20260619T002739Z-idempotency_key_regression-436e7772/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002739Z-idempotency_key_regression-436e7772/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002739Z-idempotency_key_regression-436e7772/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002739Z-idempotency_key_regression-436e7772/hidden.txt` | `` | `62012d1798bd` |
| `20260619T002750Z-pagination_cursor_drift-396c45d0` | `pagination_cursor_drift` | `runs/north-mini-code-eval/artifacts/20260619T002750Z-pagination_cursor_drift-396c45d0/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002750Z-pagination_cursor_drift-396c45d0/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002750Z-pagination_cursor_drift-396c45d0/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002750Z-pagination_cursor_drift-396c45d0/hidden.txt` | `` | `c5d94acac7c3` |
| `20260619T002804Z-stale_generated_schema-e9017db9` | `stale_generated_schema` | `runs/north-mini-code-eval/artifacts/20260619T002804Z-stale_generated_schema-e9017db9/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002804Z-stale_generated_schema-e9017db9/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002804Z-stale_generated_schema-e9017db9/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002804Z-stale_generated_schema-e9017db9/hidden.txt` | `` | `0842ab7d5050` |
| `20260619T002822Z-tenant_cache_leak-ddfd542f` | `tenant_cache_leak` | `runs/north-mini-code-eval/artifacts/20260619T002822Z-tenant_cache_leak-ddfd542f/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002822Z-tenant_cache_leak-ddfd542f/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002822Z-tenant_cache_leak-ddfd542f/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002822Z-tenant_cache_leak-ddfd542f/hidden.txt` | `` | `cc166c523352` |
| `20260619T002852Z-timezone_ci_only-79f9fc72` | `timezone_ci_only` | `runs/north-mini-code-eval/artifacts/20260619T002852Z-timezone_ci_only-79f9fc72/prompt.txt` | `runs/north-mini-code-eval/artifacts/20260619T002852Z-timezone_ci_only-79f9fc72/patch.diff` | `runs/north-mini-code-eval/artifacts/20260619T002852Z-timezone_ci_only-79f9fc72/public.txt` | `runs/north-mini-code-eval/artifacts/20260619T002852Z-timezone_ci_only-79f9fc72/hidden.txt` | `` | `be3e608188cd` |
| `20260619T012118Z-metric_semantic_mismatch-bfecbeae` | `metric_semantic_mismatch` | `runs/artifacts/20260619T012118Z-metric_semantic_mismatch-bfecbeae/prompt.txt` | `runs/artifacts/20260619T012118Z-metric_semantic_mismatch-bfecbeae/patch.diff` | `runs/artifacts/20260619T012118Z-metric_semantic_mismatch-bfecbeae/public.txt` | `runs/artifacts/20260619T012118Z-metric_semantic_mismatch-bfecbeae/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T012118Z-metric_semantic_mismatch-bfecbeae/evaluation.json` | `94c3ce0ce421` |
| `20260619T012552Z-config_deep_merge-eaa43f94` | `config_deep_merge` | `runs/artifacts/20260619T012552Z-config_deep_merge-eaa43f94/prompt.txt` | `runs/artifacts/20260619T012552Z-config_deep_merge-eaa43f94/patch.diff` | `runs/artifacts/20260619T012552Z-config_deep_merge-eaa43f94/public.txt` | `runs/artifacts/20260619T012552Z-config_deep_merge-eaa43f94/hidden.txt` | `` | `a8af6e5f0ff9` |
| `20260619T013222Z-join_fanout-41939451` | `join_fanout` | `runs/artifacts/20260619T013222Z-join_fanout-41939451/prompt.txt` | `runs/artifacts/20260619T013222Z-join_fanout-41939451/patch.diff` | `runs/artifacts/20260619T013222Z-join_fanout-41939451/public.txt` | `runs/artifacts/20260619T013222Z-join_fanout-41939451/hidden.txt` | `` | `000575e705cd` |
| `20260619T015455Z-silent_exception_swallower-e3da305c` | `silent_exception_swallower` | `runs/artifacts/20260619T015455Z-silent_exception_swallower-e3da305c/prompt.txt` | `runs/artifacts/20260619T015455Z-silent_exception_swallower-e3da305c/patch.diff` | `runs/artifacts/20260619T015455Z-silent_exception_swallower-e3da305c/public.txt` | `runs/artifacts/20260619T015455Z-silent_exception_swallower-e3da305c/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-results/20260619T015455Z-silent_exception_swallower-e3da305c/evaluation.json` | `e3b0c44298fc` |
| `20260619T125307Z-mutable_default_leak-241badf7` | `mutable_default_leak` | `runs/artifacts/20260619T125307Z-mutable_default_leak-241badf7/prompt.txt` | `runs/artifacts/20260619T125307Z-mutable_default_leak-241badf7/patch.diff` | `runs/artifacts/20260619T125307Z-mutable_default_leak-241badf7/public.txt` | `runs/artifacts/20260619T125307Z-mutable_default_leak-241badf7/hidden.txt` | `` | `2903509664d9` |
| `20260619T125329Z-api_pagination_boundary-a332b6c2` | `api_pagination_boundary` | `runs/artifacts/20260619T125329Z-api_pagination_boundary-a332b6c2/prompt.txt` | `runs/artifacts/20260619T125329Z-api_pagination_boundary-a332b6c2/patch.diff` | `runs/artifacts/20260619T125329Z-api_pagination_boundary-a332b6c2/public.txt` | `runs/artifacts/20260619T125329Z-api_pagination_boundary-a332b6c2/hidden.txt` | `` | `521dfc7ee7ad` |
| `20260619T125346Z-scd_temporal_join-029435b6` | `scd_temporal_join` | `runs/artifacts/20260619T125346Z-scd_temporal_join-029435b6/prompt.txt` | `runs/artifacts/20260619T125346Z-scd_temporal_join-029435b6/patch.diff` | `runs/artifacts/20260619T125346Z-scd_temporal_join-029435b6/public.txt` | `runs/artifacts/20260619T125346Z-scd_temporal_join-029435b6/hidden.txt` | `` | `dcd696700022` |
| `20260619T125858Z-audit_log_redaction-9f29e7b1` | `audit_log_redaction` | `runs/artifacts/20260619T125858Z-audit_log_redaction-9f29e7b1/prompt.txt` | `runs/artifacts/20260619T125858Z-audit_log_redaction-9f29e7b1/patch.diff` | `runs/artifacts/20260619T125858Z-audit_log_redaction-9f29e7b1/public.txt` | `runs/artifacts/20260619T125858Z-audit_log_redaction-9f29e7b1/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125858Z-audit_log_redaction-9f29e7b1/evaluation.json` | `7694168242a8` |
| `20260619T125907Z-billing_proration-bcdb9b72` | `billing_proration` | `runs/artifacts/20260619T125907Z-billing_proration-bcdb9b72/prompt.txt` | `runs/artifacts/20260619T125907Z-billing_proration-bcdb9b72/patch.diff` | `runs/artifacts/20260619T125907Z-billing_proration-bcdb9b72/public.txt` | `runs/artifacts/20260619T125907Z-billing_proration-bcdb9b72/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125907Z-billing_proration-bcdb9b72/evaluation.json` | `fab223b5d3f8` |
| `20260619T125925Z-bulk_invite_dedupe-bad578fa` | `bulk_invite_dedupe` | `runs/artifacts/20260619T125925Z-bulk_invite_dedupe-bad578fa/prompt.txt` | `runs/artifacts/20260619T125925Z-bulk_invite_dedupe-bad578fa/patch.diff` | `runs/artifacts/20260619T125925Z-bulk_invite_dedupe-bad578fa/public.txt` | `runs/artifacts/20260619T125925Z-bulk_invite_dedupe-bad578fa/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125925Z-bulk_invite_dedupe-bad578fa/evaluation.json` | `7bf99f737521` |
| `20260619T125938Z-cart_discount_stack-4c06770e` | `cart_discount_stack` | `runs/artifacts/20260619T125938Z-cart_discount_stack-4c06770e/prompt.txt` | `runs/artifacts/20260619T125938Z-cart_discount_stack-4c06770e/patch.diff` | `runs/artifacts/20260619T125938Z-cart_discount_stack-4c06770e/public.txt` | `runs/artifacts/20260619T125938Z-cart_discount_stack-4c06770e/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T125938Z-cart_discount_stack-4c06770e/evaluation.json` | `6bec24f8a894` |
| `20260619T132042Z-feature_rollout_bucket-14ec6bee` | `feature_rollout_bucket` | `runs/artifacts/20260619T132042Z-feature_rollout_bucket-14ec6bee/prompt.txt` | `runs/artifacts/20260619T132042Z-feature_rollout_bucket-14ec6bee/patch.diff` | `runs/artifacts/20260619T132042Z-feature_rollout_bucket-14ec6bee/public.txt` | `runs/artifacts/20260619T132042Z-feature_rollout_bucket-14ec6bee/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132042Z-feature_rollout_bucket-14ec6bee/evaluation.json` | `da62d8c57744` |
| `20260619T132110Z-inventory_reservation_idempotency-3aec4411` | `inventory_reservation_idempotency` | `runs/artifacts/20260619T132110Z-inventory_reservation_idempotency-3aec4411/prompt.txt` | `runs/artifacts/20260619T132110Z-inventory_reservation_idempotency-3aec4411/patch.diff` | `runs/artifacts/20260619T132110Z-inventory_reservation_idempotency-3aec4411/public.txt` | `runs/artifacts/20260619T132110Z-inventory_reservation_idempotency-3aec4411/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132110Z-inventory_reservation_idempotency-3aec4411/evaluation.json` | `a7c6b0dbbd8a` |
| `20260619T132139Z-markdown_slug_collision-6a73ae13` | `markdown_slug_collision` | `runs/artifacts/20260619T132139Z-markdown_slug_collision-6a73ae13/prompt.txt` | `runs/artifacts/20260619T132139Z-markdown_slug_collision-6a73ae13/patch.diff` | `runs/artifacts/20260619T132139Z-markdown_slug_collision-6a73ae13/public.txt` | `runs/artifacts/20260619T132139Z-markdown_slug_collision-6a73ae13/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132139Z-markdown_slug_collision-6a73ae13/evaluation.json` | `258b55452469` |
| `20260619T132156Z-search_ranking_stability-a5f4d3a6` | `search_ranking_stability` | `runs/artifacts/20260619T132156Z-search_ranking_stability-a5f4d3a6/prompt.txt` | `runs/artifacts/20260619T132156Z-search_ranking_stability-a5f4d3a6/patch.diff` | `runs/artifacts/20260619T132156Z-search_ranking_stability-a5f4d3a6/public.txt` | `runs/artifacts/20260619T132156Z-search_ranking_stability-a5f4d3a6/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132156Z-search_ranking_stability-a5f4d3a6/evaluation.json` | `8d20ad7010ee` |
| `20260619T132217Z-support_sla_business_hours-d705562d` | `support_sla_business_hours` | `runs/artifacts/20260619T132217Z-support_sla_business_hours-d705562d/prompt.txt` | `runs/artifacts/20260619T132217Z-support_sla_business_hours-d705562d/patch.diff` | `runs/artifacts/20260619T132217Z-support_sla_business_hours-d705562d/public.txt` | `runs/artifacts/20260619T132217Z-support_sla_business_hours-d705562d/hidden.txt` | `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr/20260619T132217Z-support_sla_business_hours-d705562d/evaluation.json` | `360773d4dfbb` |
| `20260619T132233Z-webhook_signature_raw_body-1dca4613` | `webhook_signature_raw_body` | `runs/artifacts/20260619T132233Z-webhook_signature_raw_body-1dca4613/prompt.txt` | `runs/artifacts/20260619T132233Z-webhook_signature_raw_body-1dca4613/patch.diff` | `runs/artifacts/20260619T132233Z-webhook_signature_raw_body-1dca4613/public.txt` | `runs/artifacts/20260619T132233Z-webhook_signature_raw_body-1dca4613/hidden.txt` | `` | `345abb538bfa` |

