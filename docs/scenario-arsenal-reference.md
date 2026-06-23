# Scenario Arsenal Reference

## The Core Problem

Models read code, run tests, and exit when CI is green. The problem is that
"CI is green" and "the contract is fixed" are not the same thing.

Across 39 runs of one model on the North Mini evidence pack, the failure mode
was systematic, not random:

- The model got the number right for the visible input with the wrong rounding
  mode.
- It redacted the visible secret without recursing into nested structures.
- It normalized the unit in the wrong API layer.

A consistent failure direction is learnable. The arsenal exists to make this
direction visible and measurable.

## How Scenarios Are Engineered

Every scenario has a **public test** the model can see and a **hidden test**
injected after the model exits. The public test checks the obvious, visible
requirement. The hidden test checks whether the implementation is actually
correct.

The gap between these two — the **trust gap** — is the headline metric. It
measures how often "looks fixed" is actually "is fixed."

But the public/hidden split alone does not make a good scenario. What makes a
scenario work is the **trap**: a plausible wrong path that satisfies the
visible test without fixing the contract. The trap is not a trick. It is the
most obvious fix that a reasonable model would take.

### Trap Taxonomy

Scenarios are designed to produce specific kinds of false-greens:

**Assertion-level fixes.** The model satisfies the visible assertion without
inferring the rule. `decimal_money_rounding` passes `0.29 * 3 = 0.87` with
`round(total * 100)`, but hidden tests require explicit half-up cent rounding.
The model got the number right with the wrong rounding mode.

**Scope-limited fixes.** The model fixes only what it can see.
`logger_warn_migration` updates `app/handlers.py` but leaves `app/tasks.py`
unchanged. `generated_openapi_refresh` hand-edits the visible route instead of
running the generator. The model fixed the file, not the pattern.

**Workaround fixes.** The model works around the symptom instead of fixing the
cause. `tenant_cache_leak` disables caching entirely instead of using a
composite cache key. The test passes, but the contract is violated.

**Shallow reasoning.** The model writes a fix that passes the visible case but
breaks on the general case. `feature_rollout_bucket` uses `hash()` which is
process-randomized. `config_deep_merge` does another `dict.update()` instead
of recursive merge. The model reasoned one level deep.

**Contract violations.** The model preserves visible behavior but violates an
unstated contract. `csv_header_contract` uses row keys as the schema, exporting
internal fields. `audit_log_redaction` redacts only `password`, missing
`api_key` and `token`. The model fixed the assertion, not the contract.

## What the Arsenal Measures

Challenge design defines six pivots from standard benchmarks. Each pivot
operationalizes a specific question about model behavior.

### 1. Score the trust gap, not the pass rate

A model at 95% public and 54% hidden is not a good model with a few edge
bugs. It is a model that ships confident wrong patches nearly half the time.

The trust gap is measured per-pack, per-model, per-prompt-mode. A deployment
policy uses these numbers to decide: use autonomously here, gate with hidden
acceptance here, do not delegate here.

### 2. Make the evaluator an agent, not a classifier

The evaluator gets a workbench: the seed repo, the model-patched repo with
hidden tests, and a scratch `shadow_repo` it can edit. It reproduces the
failure, forms a contract hypothesis, and optionally writes a better fix to
confirm its judgment before scoring.

A verdict backed by a shadow fix that passes every hidden test is a different
kind of evidence than a verdict backed by vibes.

### 3. Validate evidence as exact substrings

Every quote in an evaluator review must appear verbatim in the evaluation
packet. Pydantic checks the schema; the harness checks the quotes. Invent a
quote and validation fails, falling back to a deterministic summary.

The evaluator cannot hallucinate its way to confidence.

### 4. Count false-greens and weight by severity

The false-green rate — public green and hidden red, as a share of public
green — is the number that changes how you deploy, not accuracy. Each
scenario carries a risk area and impact weight, so a missed money contract
counts more than a missed doc sync.

### 5. Measure value per review hour, not just success

The maintenance pack runs three attempts per task and reports accepted patches
per review hour. A model that needs three tries to land a clean 8-line patch
is not the same value as one that does it in one try, even if both eventually
pass.

### 6. Produce a deployment policy, not a leaderboard rank

The output is a partition: use autonomously here, gate with hidden acceptance
here, do not delegate here. The harness is built to produce that partition.

## The Four Packs

Each pack targets a different slice of the problem. The pack boundary is not
about difficulty or topic — it is about what kind of reasoning the scenario
requires.

### `ci_forensics` — 12 scenarios

Practical CI debugging. Read logs, reproduce failures, separate product bugs
from environment drift, keep patches minimal.

The finding: mechanical tasks (schema regeneration, import hygiene) pass
hidden tests at 70%+. Money math, business calendars, and state invariants
sit under 30%. The dividing line is whether the spec is richer than the
visible test.

| Scenario | Category | Difficulty | Trap |
|---|---|---|---|
| `dependency_api_change` | dependency-boundary | easy | Hardcode legacy success |
| `timezone_ci_only` | environment-drift | medium | Change expected dates |
| `stale_generated_schema` | generated-artifact | easy | Hand-edit generated JSON |
| `async_export_race` | race-condition | medium | Add sleeps |
| `pagination_cursor_drift` | pagination | medium | Hardcode visible pages |
| `env_bool_parser` | configuration | easy | Special-case `"false"` |
| `tenant_cache_leak` | isolation | medium | Disable caching |
| `decimal_money_rounding` | money | medium | Use `round()` on floats |
| `idempotency_key_regression` | idempotency | easy | Add randomness |
| `csv_header_contract` | data-contract | medium | Use row keys as schema |
| `config_deep_merge` | data-structure | medium | Shallow merge |
| `mutable_default_leak` | state-leak | easy | `.clear()` in test |

### `product_workflows` — 11 scenarios

Product-level reasoning. The spec is richer than the visible test. Models must
understand user-facing contracts: email normalization, discount stacking,
inventory idempotency, search ranking, billing proration.

The finding: DeepSeek went 11/11 public but 3/11 hidden. The useful
cross-model comparison is the false-green rate, not absolute hidden pass.
"Even a strong model misses most hidden contracts at pass@1" is a more
valuable fact than who scored higher.

| Scenario | Category | Difficulty | Trap |
|---|---|---|---|
| `bulk_invite_dedupe` | import-workflow | easy | Exact-string dedupe only |
| `markdown_slug_collision` | docs-workflow | easy | Suffix only exact dupes |
| `feature_rollout_bucket` | feature-flags | medium | Use `hash()` |
| `audit_log_redaction` | security-logging | medium | Top-level password only |
| `cart_discount_stack` | checkout | medium | One discount type only |
| `inventory_reservation_idempotency` | inventory | medium | Double-reserve on retry |
| `search_ranking_stability` | search | medium | Return insertion order |
| `billing_proration` | billing | medium | Float truncation |
| `webhook_signature_raw_body` | webhooks | easy | Compare signature to secret |
| `support_sla_business_hours` | support | hard | Special-case Friday only |
| `silent_exception_swallower` | error-handling | easy | Wrap whole loop |

### `data_semantics` — 4 scenarios

Cross-domain data reasoning. Unit conversion, SQL cardinality, temporal joins,
pagination boundaries.

The finding: models satisfy the visible assertion instead of inferring the
rule. A model that divides one metric by 100 without generalizing unit
conversion is exhibiting the same failure direction as one that redacts the
visible secret without recursing. The failure mode is semantic, not about
capability.

| Scenario | Category | Difficulty | Trap |
|---|---|---|---|
| `metric_semantic_mismatch` | cross-domain | medium | Divide one metric only |
| `join_fanout` | relational-algebra | medium | Divide by COUNT |
| `api_pagination_boundary` | boundary-logic | easy | Hardcode page count |
| `scd_temporal_join` | temporal-logic | medium | Python-level hack |

### `maintenance_value` — 10 scenarios

Low-risk maintenance tasks. Measures value per review hour, not just success.
A model that needs three tries to land a clean 8-line patch is not the same
value as one that does it in one try.

The finding: Gemma 4 e4b got 5/10 hidden, 31b got 7/10 hidden. The 30% trust
gap means even on maintenance tasks, models ship confident wrong patches 30%
of the time.

| Scenario | Category | Difficulty | Trap |
|---|---|---|---|
| `generated_openapi_refresh` | generated-artifacts | easy | Hand-edit visible route |
| `logger_warn_migration` | mechanical-migration | easy | Fix only public file |
| `utcnow_timezone_migration` | mechanical-migration | easy | Patch only visible helper |
| `regression_test_gap` | test-generation | easy | Edit production code |
| `adapter_field_rename` | adapter-normalization | easy | Drop old-field compat |
| `fixture_schema_migration` | fixture-maintenance | easy | Loosen loader |
| `docs_cli_sync` | documentation-sync | easy | Re-accept old flag |
| `import_hygiene_fix` | repo-hygiene | easy | `sys.path` hack |
| `explicit_validation_matrix` | validation | medium | Only handle visible case |
| `batch_splitter_utility` | utility-implementation | easy | Miss empty input |

## What the Evidence Shows

The North Mini evidence (39 runs of `opencode/north-mini-code-free` plus one
DeepSeek control) describes one model in one harness, not a universal law.
But it surfaces signal that pass@1 cannot.

**The failure mode is systematic, not random.** Across the false-green runs,
the model satisfied the specific failing assertion instead of inferring the
rule. A consistent failure direction is learnable, which means guardrails can
be built around it.

**The loop is good; the reasoning stops at the assertion.** Every completed
run followed the correct agent loop — read, edit, test, exit — with no sprawl.
The weakness is not tool use. It is that the model asks "what makes this test
pass?" instead of "what else should be true here?"

**The task-type split is semantic, not about capability.** Mechanical
migrations pass hidden at 70%+. Money math, business calendars, auth
completeness, and state invariants sit under 30%. The dividing line is whether
the spec is richer than the visible test, not model size.

**The false-green rate is the deployment-changing number.** Roughly four in
ten public-green patches are still contract-broken. That is not a reason to
avoid the model. It is a reason to put a hidden-acceptance gate before merge
and use it confidently inside that gate.

## Running Scenarios

Single scenario:
```bash
uv run ci-vibe-run run \
  --challenge dependency_api_change \
  --model ollama/gemma4:31b \
  --prompt-mode sparse
```

Full pack via matrix:
```bash
uv run ci-vibe-matrix run \
  --config configs/matrix/local-gemma4-two-model.json \
  --pack maintenance_value
```

Inspect metadata:
```bash
uv run ci-vibe-run list --pack ci_forensics
uv run ci-vibe-run inspect --challenge decimal_money_rounding
```

Analyze trust gaps:
```bash
uv run ci-vibe-report leaderboard \
  --config configs/matrix/local-gemma4-two-model.json
```

## Adding Scenarios

A new scenario needs:

1. A seed repo where the public test fails
2. A public test that checks the visible requirement
3. A hidden test that checks the real contract
4. A trap: the plausible wrong fix that satisfies public but not hidden
5. Metadata: vibe, expected_behavior, success_signals, failure_modes

The hidden test must pass on a correct implementation and fail on the trap
implementation. If it passes on both, the scenario is not sharp enough. If it
fails on both, the scenario is not solvable.

A new pack needs a prompt lede, a mix of difficulties and categories, and at
least one model run to establish baseline evidence.

## Further Reading

- Challenge design methodology: `docs/challenge-design.md`
- North Mini evidence: `reports/north-mini-analysis.md`
- Gemma 4 matrix analysis: `reports/gemma4-matrix-analysis-2026-06-20.md`
- Scenario source of truth: `ci_vibe_lab/scenarios.py`
