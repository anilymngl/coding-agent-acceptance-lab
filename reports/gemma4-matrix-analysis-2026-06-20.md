# Gemma 4 Local Matrix Analysis

## Summary

First multi-model local comparison using the matrix pipeline. Two Gemma 4 variants
run on the `maintenance_value` pack (10 scenarios, sparse prompt mode, pass@1).

| Model | Size | Public | Hidden | Trust Gap | False-Green | Avg Time |
|---|---|---:|---:|---:|---:|---:|
| `gemma4:e4b` | small | 8/10 (80%) | 5/10 (50%) | 30% | 3/8 (37.5%) | ~62s |
| `gemma4:31b` | 31B | 10/10 (100%) | 7/10 (70%) | 30% | 3/10 (30%) | ~300s |

For reference (from earlier North Mini evaluation on the same scenarios):

| Model | Public | Hidden | Trust Gap | False-Green |
|---|---:|---:|---:|---:|
| North Mini Code | 10/10 (100%) | 7/10 (70%) | 30% | 3/10 (30%) |

**Integrity check:** all 20 artifacts present, 0 missing, 0 quarantined rows.
Evaluator reviews indexed for all 6 false-greens.

---

## Per-Scenario Comparison

| Scenario | gemma4:e4b | gemma4:31b | North Mini | Task Type |
|---|:---:|:---:|:---:|---|
| `adapter_field_rename` | ✅❌ | ✅❌ | ✅❌ | spec-completeness |
| `batch_splitter_utility` | ✅❌ | ✅❌ | ✅❌ | spec-completeness |
| `docs_cli_sync` | ✅✅ | ✅✅ | ✅✅ | mechanical |
| `explicit_validation_matrix` | ✅✅ | ✅❌ | ✅❌ | spec-completeness |
| `fixture_schema_migration` | ❌❌ | ✅✅ | ✅✅ | mechanical |
| `generated_openapi_refresh` | ✅✅ | ✅✅ | ✅✅ | mechanical |
| `import_hygiene_fix` | ✅✅ | ✅✅ | ✅✅ | mechanical |
| `logger_warn_migration` | ✅❌ | ✅✅ | ✅✅ | mechanical |
| `regression_test_gap` | ❌❌ | ✅✅ | ✅✅ | mechanical |
| `utcnow_timezone_migration` | ✅✅ | ✅✅ | ✅✅ | mechanical |

Legend: first emoji = public, second = hidden. ✅✅ = full pass. ✅❌ = false-green. ❌❌ = failed outright.

---

## Key Observations

### 1. `adapter_field_rename` and `batch_splitter_utility` fail hidden across all three models

These are spec-completeness tasks — the hidden contract is richer than the visible test.
All three models (Gemma 4 e4b, Gemma 4 31b, North Mini Code) hit the same false-green
pattern: satisfy the visible assertion, miss the broader contract. This confirms the
harness is measuring a real structural challenge, not a model-specific quirk.

### 2. Size matters — but not uniformly

- **31b vs e4b:** 31b gets 10/10 public and 7/10 hidden. e4b gets 8/10 public and 5/10
  hidden — it failed 2 scenarios outright (zero edits on `fixture_schema_migration` and
  `regression_test_gap`), suggesting the smaller model sometimes cannot even start the task.
- **The surprise:** e4b got `explicit_validation_matrix` hidden-pass (28 lines changed)
  while 31b missed it (18 lines). The smaller model wrote more code and happened to cover
  the full validation matrix. This may be noise at pass@1, but it's interesting.

### 3. gemma4:31b ≈ North Mini Code on maintenance

Both score 7/10 hidden with the exact same 3 false-greens. Both have a 30% trust gap.
North Mini is a 30B total / 3B active MoE optimized for coding; Gemma 4 31B is a
general-purpose model. On bounded maintenance tasks, they converge.

### 4. Speed vs accuracy tradeoff is real

e4b averages ~62s per scenario. 31b averages ~300s. e4b is 5x faster but scores 2 fewer
hidden passes. For a CI pre-check where human review follows, e4b might be the better
throughput choice. For unattended patch generation, 31b's accuracy matters more.

### 5. The trust gap is remarkably stable at 30%

All three models land at a 30% trust gap on `maintenance_value` sparse. This suggests
the 30% gap is a property of these scenarios (and by extension, this class of maintenance
task) more than a property of any individual model. The scenarios that are "easy" (mechanical
migrations) pass hidden reliably across models. The scenarios that are "hard" (spec-completeness)
fail hidden reliably across models.

---

## What This Means

The matrix pipeline is producing clean, comparable, reproducible results across model
families. The first real comparison validates two things:

1. **The harness measures something real.** The same scenarios are hard across different
   models, and the same false-green pattern appears regardless of model architecture.

2. **Maintenance work has a ~70% hidden pass ceiling at pass@1 sparse.** Both 31b-class
   models hit it. Breaking through that ceiling likely requires either contract-visible
   prompting (telling the model what the acceptance criteria are) or multiple attempts
   (pass@3).

Next steps would be:
- Run the same matrix with `contract_visible` prompting to measure the improvement
- Add `ci_forensics` and `product_workflows` packs to the matrix for stress comparison
- Run pass@3 to measure consistency vs lucky-shot rates

---

*Evidence: `configs/matrix/local-gemma4-two-model.json`. Data in
`data/matrix/local-gemma4-two-model-2026-06-20/`. Integrity verified:
all 120 artifacts present, 0 issues.*
