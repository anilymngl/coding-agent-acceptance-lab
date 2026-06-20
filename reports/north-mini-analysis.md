# North Mini Code: An Opinionated Analysis
## Based on Evidence Gathered in This Session

---

## How We Got Here

This didn't start as a model evaluation. It started as a framework.

We built `ci_vibe_lab` from scratch — scenario registry, worktree runner, SQLite persistence,
hidden-test injection, evaluator-agent workbench, Pydantic schema enforcement, patch-stat
accounting, resume logic, experiment IDs. Every architectural decision was made to answer one
question cleanly: **does the model actually fix the problem, or does it just make CI green?**

That distinction is the whole point. Standard evals answer the first question.
This harness answers the second.

By the end of this session we had run North Mini Code on **38 runs** across four
challenge packs. Here is all of it.

---

## The Complete Evidence Base

### Pack 1: `ci_forensics` — 10 runs (original evaluation)

These were the first 10 scenarios. Small, local, focused bugs. The kind of task the model was
explicitly designed and marketed for.

| Scenario | Public | Hidden | What it tested |
|---|:---:|:---:|---|
| `async_export_race` | ✅ | ✅ | Race condition in async export |
| `csv_header_contract` | ✅ | ❌ | CSV header ordering + empty/extra-field edge cases |
| `decimal_money_rounding` | ✅ | ❌ | Half-up cent rounding policy |
| `dependency_api_change` | ✅ | ❌ | New response field propagation |
| `env_bool_parser` | ✅ | ❌ | Boolean config: blank, whitespace, edge strings |
| `idempotency_key_regression` | ✅ | ✅ | Idempotency key logic |
| `pagination_cursor_drift` | ✅ | ✅ | Cursor-based pagination |
| `stale_generated_schema` | ✅ | ✅ | Regenerating a stale artifact |
| `tenant_cache_leak` | ✅ | ✅ | Cache key isolation per tenant |
| `timezone_ci_only` | ✅ | ✅ | Timezone handling in CI context |

**Result: 10/10 public, 6/10 hidden.**

The 4 hidden failures all share the same failure pattern: the model fixed the specific
assertion that was failing and stopped. It did not ask what broader rule the assertion
represented. The money rounding case is the clearest example — it got the value right for
the visible input, but applied the wrong rounding mode. Half-up vs. half-even is not
something a test covering one example will catch.

---

### Pack 2: Expanded runs — `data_semantics`, `product_workflows`, more `ci_forensics`

These 19 runs were added as we expanded the harness. This is where the picture gets sharp.

| Pack | Scenario | Public | Hidden | Notes |
|---|---|:---:|:---:|---|
| ci_forensics | `config_deep_merge` | ✅ | ✅ | Config merging |
| ci_forensics | `mutable_default_leak` | ✅ | ✅ | Python mutable default arg |
| data_semantics | `join_fanout` | ✅ | ✅ | SQL join producing extra rows |
| data_semantics | `api_pagination_boundary` | ✅ | ✅ | Loop break before appending last page |
| data_semantics | `scd_temporal_join` | ✅ | ✅ | Temporal join on SCD table |
| data_semantics | `metric_semantic_mismatch` (run 1) | ❌ | ❌ | Error on first attempt |
| data_semantics | `metric_semantic_mismatch` (run 2) | ✅ | ❌ | **Key failure — see below** |
| product_workflows | `webhook_signature_raw_body` | ✅ | ✅ | HMAC raw bytes vs parsed body |
| product_workflows | `audit_log_redaction` | ✅ | ❌ | Shallow vs. recursive redaction |
| product_workflows | `billing_proration` | ✅ | ❌ | Proration rounding + clamps |
| product_workflows | `bulk_invite_dedupe` | ✅ | ❌ | Email normalization completeness |
| product_workflows | `cart_discount_stack` | ✅ | ❌ | Discount ordering + zero floor |
| product_workflows | `feature_rollout_bucket` | ✅ | ❌ | Bucket boundary stability |
| product_workflows | `inventory_reservation_idempotency` | ✅ | ❌ | Mutation on insufficient stock |
| product_workflows | `markdown_slug_collision` | ✅ | ❌ | Punctuation normalization + repeats |
| product_workflows | `search_ranking_stability` | ✅ | ❌ | Deterministic recency tie-break |
| product_workflows | `support_sla_business_hours` | ✅ | ❌ | Weekend + business-hour carry |
| product_workflows | `silent_exception_swallower` | ❌ | ❌ | **900s timeout — zero edits** |
| ? | `dependency_api_change` | ❌ | ❌ | Pack unset — retry of a failure |

**Product workflows: 10/11 public, 1/11 hidden.** That number needs to sit with you for a moment.
The model wrote syntactically correct Python, made targeted edits, and made CI green on 10 of
11 product workflow tasks. It correctly fixed the business logic on exactly 1 of them.

---

### The `metric_semantic_mismatch` Evaluator Verdict

This was the most precisely diagnosed failure of the session. North Mini fixed the visible test
by normalizing units inside `compute()` — the low-level raw-data API. The hidden test checked
that `compute()` returns raw source values. It failed because the model put the fix in the
wrong layer.

The DeepSeek evaluator agent confirmed this with 0.95 confidence and 4 evidence objects:

> *"Model applied cents-to-dollars normalization inside compute() (the low-level raw API)
> instead of dashboard_total() (the user-facing layer)."*

This is not a bug. This is a model that doesn't reason about API layer boundaries. It reasons
about test assertions. The assertion happened to be satisfiable by converting in the wrong
place, and the model took that path.

---

### Pack 3: `maintenance_value` — 10 scenarios (best-of-3)

These were deliberately un-adversarial. Mechanical. Boring. Exactly the tasks that should be
safe to delegate.

| Scenario | Public | Hidden | Type |
|---|:---:|:---:|---|
| `docs_cli_sync` | ✅ | ✅ | Update README after CLI flag rename |
| `fixture_schema_migration` | ✅ | ✅ | Migrate JSON fixtures after schema change |
| `generated_openapi_refresh` | ✅ | ✅ | Regenerate stale OpenAPI artifact |
| `import_hygiene_fix` | ✅ | ✅ | Fix broken relative imports |
| `logger_warn_migration` | ✅ | ✅ | Replace deprecated `logger.warn` |
| `regression_test_gap` | ✅ | ✅ | Add missing regression test |
| `utcnow_timezone_migration` | ✅ | ✅ | Replace `datetime.utcnow()` with aware UTC |
| `adapter_field_rename` | ✅ | ❌ | Normalize DTO after field rename (2 attempts, both fail) |
| `batch_splitter_utility` | ✅ | ❌ | Implement batching with complete spec |
| `explicit_validation_matrix` | ✅ | ❌ | Full input validation matrix |

**Result: 10/10 public, 7/10 hidden.**

Seven out of ten on best-of-3 for genuinely boring maintenance work. The three failures
are all spec-completeness tasks — not "understand what code does" but "implement everything the
spec says including the parts not tested visibly." The `adapter_field_rename` failure is
notable: it failed across all three attempts with identical patch size (4 lines), meaning the model is consistently
hitting the same blind spot, not making random errors.

---

## The Full Picture

| Pack | Runs | Public | Hidden | False-Green |
|---|---:|---:|---:|---:|
| `ci_forensics` | 12 | 12/12 (100%) | 8/12 (67%) | 4 |
| `data_semantics` | 5 | 4/5 (80%) | 3/5 (60%) | 1 |
| `product_workflows` | 11 | 10/11 (91%) | 1/11 (9%) | 9 |
| `maintenance_value` | 10 | 10/10 (100%) | 7/10 (70%) | 3 |
| **Combined** | **38** | **36/38 (95%)** | **19/38 (50%)** | **17** |

One timeout (`silent_exception_swallower`, 900 seconds, zero edits).  
Seventeen runs where the model made CI green while the contract was still broken.

---

## What This Model Actually Is

### The loop is genuinely good

Every completed run followed the correct agent loop: read files, identify the failure, make a
targeted edit, rerun tests, exit. This is not trivial. Many models produce sprawling edits,
touch unrelated files, or get stuck in loops. North Mini Code does none of these things. It is
clean, fast, and disciplined at the process level.

This matches Cohere's stated design intent: a 30B total / 3B active MoE optimized for agentic
coding in terminal harnesses. The architecture shows. It is genuinely good at the mechanics.

### The reasoning stops at the assertion

The failure pattern across all 17 false-green runs is the same: the model satisfies the
specific assertion that is failing rather than inferring the rule the assertion is testing.

- `decimal_money_rounding`: Got the number right for the visible input. Wrong rounding mode.
- `env_bool_parser`: Handled the common false strings. Missed blank and whitespace.
- `billing_proration`: Correct calculation for the visible example. Wrong boundary behavior.
- `audit_log_redaction`: Replaced the visible secret. Didn't recurse into nested structures.
- `metric_semantic_mismatch`: Fixed the unit mismatch. Put the fix in the wrong API layer.
- `adapter_field_rename` (x2): Made the adapter work for the visible field. Missed compatibility contract.

In every case, a competent engineer reading the same code would have asked "what else should
be true here?" The model doesn't ask that question. It asks "what makes this test pass?"

### The task-type split is clean and actionable

This is the most useful finding. The hidden-pass rate is not uniformly bad — it splits sharply
by task type:

**Reliable (≥70% hidden pass):**
- Mechanical text/API migrations (`logger.warn`, `utcnow`, `deprecated_flag`)
- Stale artifact regeneration (OpenAPI, schemas, fixtures)
- Import and package structure fixes
- Missing regression tests
- Cursor-based pagination logic
- Cache key isolation

**Unreliable (<30% hidden pass):**
- Money math with explicit rounding policy
- Business calendars and SLA rules
- Inventory/reservation state mutation
- Auth and audit log completeness
- Discount and billing policy stacking
- Feature rollout bucket boundaries
- Any task where the hidden contract is richer than the visible test

The line between these two categories is not capability — it is semantic density. When the
task is "do this specific mechanical transformation everywhere," the model is excellent. When
the task is "implement this policy completely, including the edge cases the visible test
doesn't cover," it stops too soon.

### The 900-second timeout on `silent_exception_swallower`

This is the strangest data point. The scenario is genuinely easy — fix a `try/except` scope
inside a loop. But the model produced zero edits and hit the 900-second ceiling. There's no
recovery in the OpenCode stderr beyond the timeout message.

My best read: the model got into a reasoning loop, probably second-guessing whether a bare
`except KeyError` was appropriate or whether it should use `.get()`, without ever committing
to either. The task is syntactically simple but requires a firm decision about exception scope.
Indecision at 3B active parameters is expensive.

---

## The Context That Makes This Fairer

The expanded pack included a DeepSeek control run on product workflows. It went **11/11 public,
3/11 hidden**. A much more capable model — by any standard benchmark — still failed 8 of 11
hidden product workflow tests.

This means product workflows are genuinely hard, not just hard for North Mini. The tasks we
designed — billing proration, SLA calendars, discount stacking, audit redaction — require
reading business intent from sparse signals. That is a different skill from code repair, and
even strong models don't do it reliably at pass@1.

North Mini's 1/11 on product workflows is still worse than DeepSeek's 3/11. But the gap
is not as large as the absolute number suggests. The right comparison is the *false-green
rate*: North Mini produces confident, clean, wrong patches. DeepSeek produces more of them
correctly, but still misses most of the hidden contract.

---

## My Opinionated Take

**North Mini Code is a better-than-expected cheap CI repair agent with a precise and
consistent failure mode.**

"Better than expected" because the loop behavior is genuinely clean. I expected a 3B-active
model to fumble tool use, produce verbose edits, or time out regularly. It doesn't. It's
fast, targeted, and disciplined. That has real value.

"Precise and consistent failure mode" because it isn't randomly wrong — it's systematically
wrong in the same direction every time. It satisfies visible tests. It doesn't infer contracts.
That is learnable, and it means you can build reliable operating policies around it.

**The deployment policy this evidence supports:**

Use autonomously, merge on public pass:
- Mechanical deprecation migrations (APIs, function names, imports)
- Stale artifact regeneration (schemas, generated clients, fixtures)
- Doc/README sync after interface changes
- Missing regression tests for already-fixed bugs

Use with hidden acceptance gate before merge:
- Adapters and DTO normalization
- Validation completeness
- Pagination and cursor logic
- Cache isolation and idempotency

Do not delegate without strong human review:
- Money math (any rounding policy)
- Business rules (SLAs, calendars, rollout logic)
- Auth and audit correctness
- State mutation with invariants
- Any task where the spec is richer than the visible test

**The number that matters most isn't the pass rate. It's the false-green rate.**

95% public pass looks excellent. 50% hidden pass looks mediocre. But 17 false-green runs out
of 36 public-green runs — a 47% false-green rate among seemingly-passing patches — is the
number that changes how you deploy it. Nearly half the time that North Mini makes CI green,
the underlying contract is still broken. That's not a reason not to use it. It's a reason to
build a hidden-acceptance gate into your pipeline before merge, and use it confidently inside
that gate.

A model that is fast, cheap, clean at the loop, and fails in a predictable, detectable way is
a very useful tool. It just needs the right guardrails — and now you know exactly what those
guardrails need to catch.

---

*Evidence base: 38 runs across 4 challenge packs (maintenance counted best-of-3),
1 evaluator-agent verdict,
1 DeepSeek control run. All data in `data/north-mini-code-eval.sqlite`,
`data/results.sqlite`, and `data/maintenance-value-north-mini.sqlite`.*
