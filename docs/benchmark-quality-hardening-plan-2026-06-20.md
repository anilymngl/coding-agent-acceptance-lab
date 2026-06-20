# Benchmark Quality Hardening Plan

Date: 2026-06-20

## Goal Statement

Turn this repo from a sharp internal trust-gap microscope into an auditable,
interruption-safe, multi-lane benchmark-quality evidence system, without losing
the thing that makes it valuable: a small curated set of deterministic scenarios
that expose when visible CI green is not the same as acceptance.

The target is not a public leaderboard first. The target is a claim discipline:
every reported number should make clear whether it measures sparse-contract
inference, explicit-contract implementation, runtime reliability, evaluator
judgment, or repeated-attempt consistency.

The end-state artifact should be useful outside the repo without overstating
the evidence. The final package should include:

- a benchmark-quality research report:
  `reports/benchmark-quality-research-report-<date>.md`
- a LinkedIn-postable summary:
  `reports/post.md`
- a completed local Ollama Gemma matrix using the two smallest configured Gemma
  4 models, currently `ollama/gemma4:e4b` and `ollama/gemma4:12b`
- clear language that local Ollama rows are local-runtime evidence, not a hosted
  public leaderboard

The final public-facing message should be:

> We built a small trust-gap benchmark for coding agents. It does not ask only
> whether CI went green. It asks whether that green state can be trusted after
> hidden acceptance checks, and it separates sparse-ticket inference from
> explicit-contract implementation.

## Central Discussion

The current eval design is intentionally minimal and modest, but sharply
curated. It already finds a repeatable signal:

- North Mini gets public green very reliably, but hidden acceptance exposes a
  large trust gap.
- DeepSeek improves results but does not collapse the trust gap.
- Gemma 4 31B matches North Mini on sparse `maintenance_value`, with the same
  30% trust gap.
- Gemma 4 e4b is faster and weaker, but still shows the same broad pattern.
- The same spec-completeness tasks fail hidden across model families.

That is a strong sign that the benchmark is measuring something real. The weak
spot is not the core idea. The weak spot is claim quality around the core idea.

Right now, the executed eval mostly answers:

> Can a model infer and implement the full contract from a sparse ticket plus
> weak public tests?

That is a useful deployment question. It is not the same as:

> Can a model implement a clearly specified contract?

The next quality phase must separate those questions cleanly. Sparse lanes
should remain the behavior microscope. `contract_visible` lanes should measure
implementation capability once ambiguity is removed. Runtime failures should
stay out of semantic failure counts. Evaluator reviews should be validated and
cross-checked. Scenario audits should move from seeded acceptance to explicit
review notes, especially for product and data semantics.

## Starting Evidence

Current strongest evidence:

- Canonical North Mini report:
  `reports/north-mini-ultimate-eval-report-2026-06-20.md`
- First local multi-model matrix:
  `reports/gemma4-matrix-analysis-2026-06-20.md`
- Matrix leaderboard:
  `reports/leaderboard-local-gemma4-two-model.md`
- Matrix integrity:
  `reports/integrity-local-gemma4-two-model.md`
- Fresh-run runtime audit:
  `reports/north-mini-fresh-run-harness-audit-2026-06-20.md`
- Methodology:
  `docs/challenge-design.md`

Current high-confidence facts:

- Public/hidden split works and is the central methodology.
- Hidden tests are injected after the model exits.
- The completed Gemma 4 two-model matrix has 20/20 completed rows, 0 runtime
  failures, and 120/120 artifacts present.
- Gemma 4 matrix false-greens have 6/6 evaluator review coverage.
- No-output/provider stalls were a real confound in earlier fresh runs and must
  remain operational reliability evidence, not semantic model evidence.

Current quality gaps:

- `contract_visible` matrix evidence is not complete.
- Product and data-semantic hidden tests need explicit external audit notes.
- Many scenario audit rows are seeded defaults, not independent reviews.
- Evaluator coverage is good in reports but not uniformly indexed across older
  DBs.
- Single-evaluator-model judgment is not enough for benchmark-grade claims.
- pass@1 variance is visible and not yet measured systematically.
- Matrix coverage is currently cleanest for `maintenance_value` only.
- The local Ollama lane has compared e4b and 31B, but the final local-small-model
  matrix should explicitly compare the two smallest configured Gemma 4 models:
  e4b and 12b.

## Quality Bar

Use three claim tiers.

### Tier 1: Internal Behavior Microscope

Allowed now.

Claims:

- public green is not acceptance
- sparse prompt trust gap exists on these curated scenarios
- product and policy-heavy tasks are risky under sparse visible tests
- mechanical maintenance is a better operating zone

Requirements:

- public/hidden isolation
- artifact preservation
- no runtime failures counted as semantic failures
- clear caveats

### Tier 2: Defensible Comparative Matrix

Allowed after this plan's core hardening work.

Claims:

- model A and model B differ on a named pack/lane under matched runtime policy
- sparse vs `contract_visible` reveals how much ambiguity contributes
- repeated attempts show consistency or variance for named scenarios

Requirements:

- complete matrix cells or explicit missing-cell status
- integrity report passes
- evaluator coverage for all false-greens
- scenario audit status populated in rows
- sparse and `contract_visible` not merged by default
- runtime reliability scored separately

### Tier 3: Public Benchmark-Style Summary

Not allowed yet.

Requirements before considering:

- external audit notes for hidden tests
- at least two evaluator sources or human agreement checks
- multi-model matrix across at least `maintenance_value`, `ci_forensics`, and
  `product_workflows`
- pass@3 or repeated-attempt variance report
- stable no-output/provider failure handling
- claim ledger reviewed for every headline number

## Non-Goals

- Do not weaken hidden tests to improve model scores.
- Do not broaden scenario count at the cost of inspectability.
- Do not merge sparse and `contract_visible` lanes into one headline.
- Do not treat local Ollama hardware timing as hosted-model capability.
- Do not publish a global leaderboard before the audit and agreement layers are
  in place.
- Do not hide runtime failures; classify them separately.

## Workstream 1: Evidence Taxonomy And DB Hygiene

### Purpose

Make every row machine-classifiable before interpretation. A report should not
need human memory to know whether a row is semantic evidence, runtime evidence,
or missing coverage.

### Deliverables

- Backfill or compute `scenario_audit_status` for older run DBs.
- Add a matrix/report helper that joins runs to `scenario_audits` by scenario
  when row fields are blank.
- Add a standard evidence status enum to every report:
  - `valid_completed_attempt`
  - `public_red`
  - `false_green`
  - `hidden_pass`
  - `agent_timeout`
  - `no_output_timeout`
  - `provider_config_error`
  - `runner_error`
  - `missing_cell`
  - `quarantined_scenario`
- Add a command or report section that shows:
  - rows by evidence status
  - rows by audit status
  - false-greens lacking evaluator review
  - rows whose scenario audit is only seeded/default

### Practical Implementation

Prefer a report-layer implementation before mutating historical DBs:

```bash
uv run ci-vibe-report integrity \
  --matrix configs/matrix/local-gemma4-two-model.json \
  --out reports/integrity-local-gemma4-two-model.md
```

Then add a separate DB hygiene report:

```bash
uv run ci-vibe-report evidence-health \
  --db data/ci-forensics-v2.sqlite \
  --db data/product-workflows-v2.sqlite \
  --db data/maintenance-value-v2.sqlite \
  --out reports/evidence-health-2026-06-20.md
```

If a new command is too much, add the same section to `leaderboard` and
`ultimate` first.

### Acceptance Criteria

- No headline report has blank audit-status counts.
- Every row is assigned exactly one evidence status.
- No-output timeout rows cannot appear in false-green totals.
- Missing matrix cells appear as missing coverage, not as model failures.
- All report-level denominators state whether they are completed-attempt,
  all-row, scenario-level, or best-of-N.

## Workstream 2: Contract-Visible Maintenance Lane

### Purpose

Separate ambiguity from implementation capability.

Sparse asks:

> Can the model infer the full contract from a weak public test and nearby code?

`contract_visible` asks:

> Can the model implement the contract when the acceptance criteria are stated?

The difference between those lanes is the most important benchmark-quality
upgrade.

### Deliverables

- A two-model local Gemma 4 `contract_visible` maintenance matrix config.
- A sparse-vs-contract report.
- A per-scenario recovery table:
  - sparse false-green -> contract hidden-pass
  - sparse false-green -> contract false-green
  - sparse public-red -> contract hidden-pass
  - sparse hidden-pass -> contract hidden-pass
- A short interpretation section:
  - ambiguity bottleneck
  - implementation bottleneck
  - variance/noise candidate

### Config Shape

Add a config such as:

```text
configs/matrix/local-gemma4-two-model-contract-visible.json
```

It should mirror `configs/matrix/local-gemma4-two-model.json` except:

- `prompt_modes`: `["contract_visible"]`
- matrix id should make the lane explicit
- output paths should not overwrite sparse DBs

### Commands

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-two-model-contract-visible.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-two-model-contract-visible.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-two-model-contract-visible.json --dry-run
```

Run only after smoke gates pass:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-two-model-contract-visible.json --resume
```

Generate reports:

```bash
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-two-model-contract-visible.json \
  --out reports/leaderboard-local-gemma4-two-model-contract-visible.md \
  --include-artifact-index

uv run ci-vibe-report integrity \
  --matrix configs/matrix/local-gemma4-two-model-contract-visible.json \
  --out reports/integrity-local-gemma4-two-model-contract-visible.md
```

### Acceptance Criteria

- 20 expected rows, 20 completed rows, 0 missing cells, or explicit runtime
  failure accounting.
- Integrity report has 0 missing artifacts.
- False-greens have evaluator reviews.
- Report states sparse and `contract_visible` separately.
- No combined score averages sparse and contract-visible rows.

## Workstream 3: Interval Smoke Tests

### Purpose

Long model runs fail in ways that look like model weakness if they are not
checked early and repeatedly. Interval smoke tests make runtime health visible
before expensive or misleading evidence accumulates.

### Smoke Philosophy

Do not wait until the end of a matrix to discover:

- OpenCode is producing no stdout/stderr
- Ollama loaded the wrong model or unloaded between cells
- first-output timeout is too strict
- matrix paths point at the wrong DB
- hidden tests are leaking into model-visible worktrees
- evaluator review indexing is broken
- reports are counting runtime failures as model failures

Use smoke tests as gates between phases and as interval checks during long
runs.

### Smoke Gate A: Static Harness Health

Run before any model tokens.

```bash
uv run python -m unittest discover -s tests -v

uv run ci-vibe-run list
uv run ci-vibe-run list --pack maintenance_value
```

Pass condition:

- unit tests pass
- expected packs and scenarios list successfully

Stop condition:

- any harness test fails
- expected scenario count changed without intentional scenario work

### Smoke Gate B: No-Model Harness Path

Run before any model matrix.

```bash
uv run ci-vibe-run run \
  --challenge dependency_api_change \
  --no-opencode \
  --db /tmp/ci-vibe-no-model-smoke.sqlite \
  --runs-dir /tmp/ci-vibe-no-model-smoke-runs

uv run ci-vibe-run inspect \
  --db /tmp/ci-vibe-no-model-smoke.sqlite \
  --latest \
  --full
```

Pass condition:

- baseline is red
- public/hidden execution works
- artifacts are written

Stop condition:

- hidden tests are present before model exit
- artifact paths are missing
- DB row is malformed

### Smoke Gate C: Model Invocation Health

Run one tiny model task before each long lane.

For local Gemma 4:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-e4b-smoke.json --stop-on-failure
```

For 31B direct smoke if needed:

```bash
uv run ci-vibe-run run \
  --challenge docs_cli_sync \
  --model ollama/gemma4:31b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 300 \
  --prompt-mode sparse \
  --db /tmp/ci-vibe-gemma4-31b-smoke.sqlite \
  --runs-dir /tmp/ci-vibe-gemma4-31b-smoke-runs
```

Pass condition:

- OpenCode emits stdout/stderr before first-output timeout
- exit code is 0
- patch is non-empty when the task requires code/docs change
- public and hidden pass for the smoke task

Stop condition:

- `opencode_exit_code=124`
- stdout and stderr are both empty
- provider/config error
- model ID resolves incorrectly

### Smoke Gate D: Matrix Path And Resume Health

Run before real matrix execution.

```bash
uv run ci-vibe-matrix validate <config>
uv run ci-vibe-matrix plan <config>
uv run ci-vibe-matrix run <config> --dry-run --resume
uv run ci-vibe-matrix dbs <config>
```

Pass condition:

- expected cells match the intended model x pack x lane count
- DB paths are unique
- run dirs are unique
- resume plan does not skip cells unexpectedly

Stop condition:

- sparse and contract-visible point to same DB
- two models share output roots
- expected count does not match scenario count

### Smoke Gate E: Interval Runtime Check During Matrix

Run after every 3 cells for local 31B, after every 5 cells for faster models, or
after every 30 minutes, whichever comes first.

Manual interval check:

```bash
uv run ci-vibe-matrix status <config>
```

Then inspect latest row if anything looks off:

```bash
uv run ci-vibe-run inspect \
  --db <latest-cell-db> \
  --latest \
  --full
```

Pass condition:

- completed count increases
- runtime failures remain 0 or are explicitly understood
- latest row has non-empty OpenCode stream
- model latency is in expected range

Stop condition:

- two consecutive no-output timeouts
- same provider/config error repeats twice
- DB row is written without artifact paths
- hidden test appears in prompt or model-visible files before injection

Recommended future automation:

```json
{
  "interval_smoke": {
    "enabled": true,
    "every_completed_rows": 3,
    "max_no_output_timeouts": 1,
    "status_after_each_cell": true,
    "stop_on_repeated_runtime_failure": true
  }
}
```

### Smoke Gate F: Post-Lane Integrity

Run immediately after every lane.

```bash
uv run ci-vibe-report integrity \
  --matrix <config> \
  --out reports/integrity-<matrix-id>.md

uv run ci-vibe-report leaderboard \
  --matrix <config> \
  --out reports/leaderboard-<matrix-id>.md \
  --include-artifact-index
```

Pass condition:

- all required artifacts present
- false-greens are listed
- runtime failure inbox is correct
- missing cells are explicit

Stop condition:

- artifact count mismatch
- false-green count differs between DB query and report
- report cannot classify runtime failures

### Smoke Gate G: Evaluator Review Smoke

Before batch reviewing all false-greens, run one evaluator review.

```bash
uv run ci-vibe-matrix evaluate <config> \
  --loose \
  --max-rows 1
```

Pass condition:

- `evaluation.json` validates
- evidence quotes are exact substrings
- review artifact paths are indexed

Stop condition:

- evaluator emits invalid JSON repeatedly
- evidence validation fails
- review is written but not discoverable by the report

## Workstream 4: External Scenario Audit

### Purpose

Remove the strongest author-bias objection: hidden tests are authored contracts.

The goal is not to make every scenario obvious. The goal is to prove the hidden
contract is inferable, legitimate, and not merely a private preference.

### Deliverables

- One audit packet per scenario, starting with product workflows and data
  semantics.
- A revised audit table with non-default notes.
- Audit status for each scenario:
  - `accepted`
  - `accepted_contract_visible`
  - `revise_public_prompt`
  - `revise_hidden_test`
  - `quarantine`
- Report section showing audit coverage and unresolved audit issues.

### Audit Questions

For each scenario, answer:

1. What is the user-visible or system-visible contract?
2. Where can the model infer it from the sparse repo?
3. Does the public test represent the contract or only one example?
4. Does the hidden test check behavior instead of patch shape?
5. Are there multiple good implementations?
6. Is the hidden expectation standard practice or project-specific policy?
7. Should this scenario belong in sparse, `contract_visible`, or both?
8. What would make the scenario unfair?
9. What exact report caveat should accompany this scenario?

### Practical Order

Audit these first:

1. `audit_log_redaction`
2. `billing_proration`
3. `bulk_invite_dedupe`
4. `cart_discount_stack`
5. `inventory_reservation_idempotency`
6. `metric_semantic_mismatch`
7. `support_sla_business_hours`
8. `feature_rollout_bucket`
9. `search_ranking_stability`
10. `markdown_slug_collision`

Reason: these drive the strongest claims and the largest risk of perceived
hidden-test unfairness.

### Acceptance Criteria

- No product-workflow scenario has default audit notes.
- Every high-impact scenario has a concrete inferability note.
- Any scenario with weak inferability is moved to `contract_visible` or revised.
- Quarantined scenarios are excluded from headline metrics by default.

## Workstream 5: Evaluator Agreement

### Purpose

Validated evaluator JSON prevents sloppy review artifacts, but it does not prove
the evaluator is right. Agreement checks make review quality measurable.

### Deliverables

- A second evaluator pass on all false-greens in:
  - product workflows
  - data semantics
  - Gemma 4 matrix
- A disagreement report:
  - same verdict
  - same root-cause family
  - severity agreement
  - confidence spread
  - human tie-break needed
- Optional human spot-audit for high-impact disagreements.

### Practical Command Shape

Use existing evaluator workflow first. If a second evaluator model is available,
run it into a separate review root:

```bash
uv run ci-vibe-evaluate run \
  --db data/product-workflows-v2.sqlite \
  --hidden-only \
  --public-green-only \
  --target-model opencode/north-mini-code-free \
  --model <second-evaluator-model> \
  --auto-approve \
  --out runs/evaluator-agent/<second-model>-product-pghr \
  --report reports/<second-model>-product-pghr.md \
  --loose
```

Then report agreement:

```bash
uv run ci-vibe-report evaluator-agreement \
  --reviews runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr \
  --reviews runs/evaluator-agent/<second-model>-product-pghr \
  --out reports/evaluator-agreement-product-2026-06-20.md
```

If `evaluator-agreement` does not exist yet, implement it as a small report
over `evaluation.json` files.

### Acceptance Criteria

- Every high-impact false-green has at least two review sources or one review
  plus human audit note.
- Disagreements are explicit, not hidden.
- Headline reports state evaluator coverage and agreement rate.

## Workstream 6: pass@3 And Variance

### Purpose

Single attempts are noisy. The Gemma e4b `explicit_validation_matrix` pass while
31B missed is a good example: it may reveal useful style difference, or it may
be pass@1 luck.

### Deliverables

- pass@3 matrix config for `maintenance_value`.
- Repeated-attempt report:
  - first-attempt hidden pass
  - any-of-3 hidden pass
  - all-of-3 hidden pass
  - false-green persistence
  - scenario volatility
- Scenario labels:
  - stable pass
  - stable fail
  - volatile
  - public-red unstable
  - runtime unstable

### Practical Rules

- Keep attempt-level and scenario-level metrics separate.
- Do not report best-of-3 without also reporting all-attempt cost.
- Preserve review-hour/value metrics for maintenance tasks.
- Use the same timeouts and delay policy across compared models.

### Acceptance Criteria

- Every pass@3 report states both attempt-level and scenario-level denominators.
- A scenario is not called "solved" unless the selection rule is stated.
- Volatile scenarios are flagged before model-level conclusions.

## Workstream 7: Broader Matrix Coverage

### Purpose

The clean Gemma matrix is currently maintenance-only. To test whether the
trust-gap pattern generalizes, add broader packs only after lane and audit
hygiene are in place.

### Order

1. `maintenance_value`, `contract_visible`
2. `ci_forensics`, sparse
3. `ci_forensics`, `contract_visible`
4. local Ollama smallest-two Gemma 4 matrix: `gemma4:e4b` and `gemma4:12b`
5. `product_workflows`, sparse
6. `product_workflows`, `contract_visible`
7. pass@3 on selected volatile scenarios

### Why This Order

- Maintenance is already proven operationally viable.
- `contract_visible` maintenance gives the clean ambiguity/capability split.
- `ci_forensics` is the middle-difficulty calibration pack.
- The local smallest-two Gemma 4 matrix gives a practical throughput-oriented
  local-model readout before spending more time on larger local models.
- Product workflows should wait for audit notes because they drive the strongest
  and most controversial claims.

### Local Ollama Smallest-Two Gemma Matrix

Purpose:

- compare the smallest practical local Gemma 4 models under the same matrix
  discipline as the larger 31B run
- show the local speed/quality frontier without frontloading expensive models
- produce a clean research-report table and a LinkedIn-postable summary

Models:

- `ollama/gemma4:e4b`
- `ollama/gemma4:12b`

If the Ollama catalog or repo config changes, choose the two smallest Gemma 4
models configured in `opencode.json`. Do not substitute Gemma 3, Qwen, or other
families into the Gemma-only lane.

User-requested fallback:

- If `ollama/gemma4:12b` is not viable, use a separate Qwen fallback lane
  rather than silently replacing the Gemma row.
- Preferred fallback config:
  `configs/matrix/local-gemma4-e4b-qwen36-fallback.json`.
- Preferred fallback model: `ollama/qwen3.6:27b`.
- Rationale: Ollama's Qwen3.6 catalog lists 27B and 35B variants; 27B is the
  smallest Qwen3.6 tag. This is a role-equivalent fallback for local
  coding-agent evidence, not a size-equivalent replacement for Gemma 4 12B.
- Report any Qwen row separately from the Gemma-only matrix.

Required smoke checks before running the 12B lane:

```bash
ollama list | rg 'gemma4:(e4b|12b)'
ollama pull gemma4:12b
curl -s http://localhost:11434/api/tags
opencode models | rg '^ollama/gemma4:(e4b|12b)'
```

Observed local gate on 2026-06-20:

- Initial blocker: Ollama `0.21.0` could not pull `gemma4:12b`.
- Resolution: Ollama was upgraded to `0.30.10`.
- Installed Gemma 4 models after upgrade: `gemma4:e4b`, `gemma4:12b`,
  `gemma4:31b`.
- OpenCode lists `ollama/gemma4:e4b`, `ollama/gemma4:12b`, and
  `ollama/gemma4:31b`.
- `configs/matrix/local-gemma4-12b-smoke.json` completed one sparse
  `docs_cli_sync` attempt, but the model produced an empty patch:
  public `0`, hidden `0`, duration `55.1s`, run
  `20260620T160329Z-docs_cli_sync-2d774a99`.
- A direct 12B rerun passed public and hidden:
  `20260620T160915Z-docs_cli_sync-51838e9d`, duration `113.7s`.
- Sparse `configs/matrix/local-gemma4-smallest-two.json` then ran:
  e4b complete; 12B mixed with one `agent_timeout` on
  `explicit_validation_matrix`.

Run a one-cell smoke for each model before a full pack:

```bash
uv run ci-vibe-run run \
  --challenge docs_cli_sync \
  --model ollama/gemma4:e4b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 120 \
  --prompt-mode sparse \
  --db /tmp/ci-vibe-gemma4-e4b-docs-smoke.sqlite \
  --runs-dir /tmp/ci-vibe-gemma4-e4b-docs-smoke-runs

uv run ci-vibe-run run \
  --challenge docs_cli_sync \
  --model ollama/gemma4:12b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 240 \
  --prompt-mode sparse \
  --db /tmp/ci-vibe-gemma4-12b-docs-smoke.sqlite \
  --runs-dir /tmp/ci-vibe-gemma4-12b-docs-smoke-runs
```

Then add a config such as:

```text
configs/matrix/local-gemma4-smallest-two.json
```

Minimum config shape:

- models: `gemma4-e4b`, `gemma4-12b`
- pack: `maintenance_value`
- lanes: `sparse`, then `contract_visible` after sparse is healthy
- runs: `1` before pass@3 work
- warmup: enabled
- separate DB/run roots from the earlier e4b/31B matrix

Fallback config shape if 12B is rejected:

- models: `gemma4-e4b`, `qwen36-27b`
- model id: `ollama/qwen3.6:27b`
- pack: `maintenance_value`
- lanes: `sparse`, then `contract_visible`
- output roots must include `qwen36-fallback`
- report separately from Gemma-only results

Expected report outputs:

```text
reports/leaderboard-local-gemma4-smallest-two.md
reports/integrity-local-gemma4-smallest-two.md
reports/gemma4-smallest-two-research-report-<date>.md
reports/post.md
```

`reports/post.md` must be readable as a standalone LinkedIn post. It should be
short, caveated, and evidence-backed:

- one-sentence hook about public green not being acceptance
- what was run: local Ollama Gemma 4 e4b and 12b, pack, lane, pass policy
- key table: public, hidden, trust gap, false-greens, average time
- one concrete failure pattern
- one caveat: local runtime and curated benchmark, not a public leaderboard
- one practical lesson for engineering teams

Acceptance criteria:

- both local models pass model-invocation smoke before full matrix work, or any
  failed smoke is explicitly classified before the full matrix is launched
- matrix cells are complete or runtime failures are explicitly classified
- if 12B is replaced, Qwen3.6 fallback rows are clearly labeled as fallback
  local-runtime evidence
- warmup durations are logged outside run-row latency
- integrity report has 0 missing artifacts for completed cells
- false-greens are evaluator-reviewed before the research report is finalized
- `reports/post.md` includes no unsupported ranking claim

### Acceptance Criteria

- No pack enters a cross-model headline until its integrity report passes.
- Product-workflow claims must include audit coverage.
- Local model rows are marked as local runtime evidence, not hosted-model
  leaderboard evidence.
- The local smallest-two Gemma matrix is reported separately from the earlier
  e4b/31B matrix.

## Workstream 8: Report And Claim Ledger Hardening

### Purpose

Benchmark quality is mostly claim quality. Reports should make the safe
interpretation the easy interpretation.

### Required Report Sections

Every major report should include:

- Scope:
  - models
  - packs
  - lanes
  - pass policy
  - date
- Evidence health:
  - expected rows
  - completed rows
  - runtime failures
  - missing cells
  - quarantined rows
- Capability score:
  - completed-attempt metrics only
- Operational reliability:
  - timeout/no-output/provider/config rows
- Sparse vs contract-visible split:
  - never merged by default
- False-green table:
  - scenario
  - missed contract
  - evaluator verdict
  - audit status
- Claim ledger:
  - claim
  - evidence
  - confidence
  - caveat
  - allowed tier
- What cannot be defended.

### Headline Rules

Allowed:

- "On `maintenance_value` sparse pass@1, Gemma 4 31B and North Mini both reached
  7/10 hidden with a 30% trust gap."
- "Product workflows are a sparse-contract stress pack with high false-green
  rates across North Mini and DeepSeek."

Not allowed:

- "Model X is better than model Y overall."
- "This is a public benchmark leaderboard."
- "Product backend work has an 82% failure rate."
- "Runtime timeout rows are hidden failures."

### Acceptance Criteria

- Every report has a "What Can And Cannot Be Defended" section.
- Every headline number is traceable to DBs and artifacts.
- Every partial result says partial.
- Every local-model result says local runtime conditions.

## Workstream 9: Scenario Portfolio Quality

### Purpose

Keep the suite small and sharp while avoiding one-note traps.

### Portfolio Targets

Maintain a balanced scenario portfolio:

- mechanical maintenance
- adapter/compatibility contracts
- data semantics
- product policy
- financial correctness
- security/audit behavior
- state mutation/idempotency
- ranking/determinism
- generated artifacts

Do not add more scenarios until current ones are audited and lane-separated.

### Scenario Admission Checklist

Before adding a scenario:

- Does it reveal a specific real agent failure mode?
- Is the hidden test behavioral, not patch-shape based?
- Is the contract inferable in sparse mode?
- If not inferable, is it explicitly marked `contract_visible`?
- Is there at least one plausible wrong fix?
- Is the public test weak in a realistic way?
- Can a human review the whole scenario in under 10 minutes?
- Does it add a new failure mode, or duplicate an existing one?

### Acceptance Criteria

- New scenarios require audit metadata at creation time.
- No scenario ships with only default audit notes if it is high-impact.
- Duplicate failure modes are consolidated or explicitly justified.

## Workstream 10: Dashboard And Operator UX

### Purpose

Make evidence health visible before interpretation.

### Dashboard Additions

- Evidence-health banner:
  - complete
  - partial
  - runtime-contaminated
  - audit-incomplete
  - evaluator-incomplete
- Lane selector that keeps sparse and `contract_visible` separate.
- Runtime failure inbox.
- Audit coverage table.
- Evaluator agreement table.
- Volatile scenario table after pass@3.

### Acceptance Criteria

- Dashboard cannot silently mix sparse and contract-visible rows.
- Runtime failures are visually separate from false-greens.
- Missing cells are visible.

## Workstream 11: Research Report And LinkedIn Post

### Purpose

Translate the hardened benchmark evidence into a clear public-facing research
artifact without weakening caveats or turning the result into a fake leaderboard.

The report should be useful to engineers who want to understand the method. The
post should be useful to readers who only have time for the central lesson.

### Required Artifacts

```text
reports/benchmark-quality-research-report-<date>.md
reports/post.md
```

### Research Report Shape

The research report should include:

- title and one-paragraph thesis
- method summary:
  - public tests visible to model
  - hidden tests injected after model exit
  - sparse vs `contract_visible`
  - runtime failures separated from semantic failures
- evidence table:
  - North Mini canonical evidence
  - DeepSeek control
  - Gemma 4 e4b/31B matrix
  - Gemma 4 e4b/12B local-small matrix after it exists
- benchmark-quality section:
  - what is strong
  - what is still weak
  - what was done to harden claims
- local Ollama section:
  - hardware/runtime caveat
  - warmup not counted as row latency
  - smallest-two model comparison
- failure pattern examples:
  - adapter field preservation
  - batch-size validation
  - money rounding
  - recursive audit redaction
- claim ledger
- what can and cannot be defended
- next work

### `reports/post.md` Shape

The LinkedIn post should be concise and self-contained:

```markdown
# Post

We tested a coding-agent failure mode that normal benchmarks often hide:
CI goes green, but the contract is still broken.

...
```

Required content:

- no more than 1,800 characters unless intentionally writing a long-form post
- plain language
- one small results table or compact bullet scorecard
- one concrete example of a false-green
- explicit caveat: curated local eval, not a public leaderboard
- practical takeaway for engineering teams
- link/pointer to the research report path

Forbidden content:

- "best model" claims
- unsupported broad generalization
- local Ollama results presented as hosted-model benchmark results
- hidden-test details that would compromise future model-under-test paths

### Acceptance Criteria

- `reports/post.md` can stand alone without repo context.
- Every number in the post appears in the research report.
- Every number in the research report traces to a report, DB, or artifact.
- The local e4b/12B matrix is included only after its integrity report passes.
- The post says "trust gap" and explains it in plain words.
- The post does not imply hidden tests were visible to the model.

## Execution Roadmap

### Phase 0: Commit Current Docs

Purpose:

- preserve the current state before more benchmark-quality work begins

Actions:

```bash
git status -sb
git diff --check
uv run ci-vibe-matrix status configs/matrix/local-gemma4-two-model.json
```

Then commit the current docs update and this plan.

Acceptance:

- clean whitespace check
- current matrix status still complete
- docs commit is small and reviewable

### Phase 1: Add Evidence Health Report

Purpose:

- make row classification explicit before running more data

Actions:

- implement or extend report-layer evidence-health sections
- join blank run audit statuses to `scenario_audits`
- add tests for evidence classification

Acceptance:

- unit tests pass
- evidence-health report shows no unclassified rows for canonical DBs

### Phase 2: Contract-Visible Maintenance Matrix

Purpose:

- measure ambiguity vs implementation capability

Actions:

- add contract-visible matrix config
- run all smoke gates
- run matrix
- generate leaderboard and integrity
- run evaluator on false-greens
- write sparse-vs-contract analysis

Acceptance:

- complete matrix or explicit runtime caveat
- all false-greens reviewed
- report answers: "Did explicit contract visibility reduce the trust gap?"

### Phase 3: External Audit Sprint

Purpose:

- reduce hidden-test author-bias risk

Actions:

- create audit packets for product/data scenarios
- replace default audit notes
- quarantine or revise weak scenarios

Acceptance:

- product workflows have no default audit notes
- report says which scenarios are accepted vs revised/quarantined

### Phase 4: Evaluator Agreement

Purpose:

- make review judgments more reliable

Actions:

- run second evaluator or human audit on false-greens
- build agreement report
- add disagreement caveats to headline reports

Acceptance:

- high-impact false-greens have agreement evidence
- disagreements are surfaced

### Phase 5: pass@3 / Variance

Purpose:

- distinguish stable weaknesses from one-shot variance

Actions:

- run repeated attempts on maintenance and selected product scenarios
- produce volatility report
- update deployment policy by stable/volatile categories

Acceptance:

- scenario-level and attempt-level metrics are both present
- no best-of-3 claim lacks cost/attempt caveat

### Phase 6: Broader Matrix

Purpose:

- test whether signals hold outside maintenance

Actions:

- run `ci_forensics` matrix
- run product matrix only after audit is complete
- generate pack-specific reports

Acceptance:

- each pack has integrity, evaluator coverage, and audit coverage
- no global leaderboard summary is produced unless all tier-3 requirements are
  met

### Phase 7: Local Ollama Smallest-Two Gemma Matrix

Purpose:

- create a practical local-model readout using the smallest two configured
  Gemma 4 models, not only the e4b/31B comparison

Actions:

- confirm `ollama/gemma4:e4b` and `ollama/gemma4:12b` are available to OpenCode
- pull `gemma4:12b` if needed
- run one-cell smoke for both models
- add `configs/matrix/local-gemma4-smallest-two.json`
- run sparse `maintenance_value`
- run `contract_visible` only after sparse health is clean
- generate leaderboard, integrity, and evaluator-reviewed false-green reports

Acceptance:

- e4b and 12B both pass smoke before full matrix work, or 12B's no-edit smoke
  failure is explicitly accepted as an evidence-status row before spending full
  matrix runtime
- if 12B is not viable, `local-gemma4-e4b-qwen36-fallback.json` exists and is
  validated before any Qwen run
- matrix results are complete or runtime failures are explicitly classified
- warmup time is logged outside measured run latency
- report clearly labels this as local Ollama evidence
- no result is merged with the earlier e4b/31B matrix unless explicitly shown as
  a separate comparison table

### Phase 8: Research Report And `post.md`

Purpose:

- produce a final research artifact and a LinkedIn-postable summary that carry
  the benchmark-quality caveats correctly

Actions:

- write `reports/benchmark-quality-research-report-<date>.md`
- write `reports/post.md`
- verify every post number exists in the research report
- verify every research-report number traces to source reports, DBs, or
  artifacts
- add both files to `reports/REPORTS.md`

Acceptance:

- `reports/post.md` is readable as a standalone LinkedIn post
- the post names the trust gap and explains it plainly
- the post includes the local e4b/12B matrix only if integrity passed
- no unsupported ranking or public-leaderboard claim appears

## Interval Smoke Schedule For Long Runs

Use this exact schedule for any long matrix or pass@3 run.

Before run:

1. `uv run python -m unittest discover -s tests -v`
2. no-model harness smoke
3. model invocation smoke
4. `ci-vibe-matrix validate`
5. `ci-vibe-matrix plan`
6. `ci-vibe-matrix run --dry-run --resume`

During run:

- after every 3 completed local-31B rows:
  - `uv run ci-vibe-matrix status <config>`
  - inspect latest row if duration or status looks abnormal
- after any runtime failure:
  - inspect latest row
  - rerun a tiny model smoke before continuing
- after two consecutive runtime failures:
  - stop the lane
  - classify as operational reliability issue
  - do not keep spending model time

After run:

1. integrity report
2. leaderboard report
3. evaluator review smoke
4. batch evaluator reviews
5. final leaderboard regeneration with evaluator coverage
6. research-report update
7. `reports/post.md` update when the lane changes the public-facing story
8. docs/report summary update

## Decision Rules

### Continue

Continue a lane when:

- smoke gates pass
- runtime failures are isolated and classified
- expected rows are still reachable
- no hidden leakage is detected

### Pause

Pause a lane when:

- one no-output timeout occurs on a model that was previously healthy
- matrix status shows unexpected missing rows
- generated DB path is wrong
- evaluator indexing fails

### Stop

Stop a lane when:

- two consecutive no-output timeouts happen
- provider/config error repeats
- hidden tests are visible before model exit
- artifact integrity fails in a way that loses source evidence
- output paths collide across lanes or models

## Final Definition Of Done

This benchmark-quality hardening goal is done when:

- `contract_visible` maintenance exists and is reported separately from sparse
- every canonical row has an evidence status
- every canonical scenario has non-default audit notes or is explicitly marked
  lower risk
- product/data hidden tests have external or second-pass audit notes
- all false-greens in headline reports have evaluator coverage
- evaluator agreement exists for high-impact false-greens
- pass@3 or repeated-attempt variance exists for at least maintenance and the
  most important product scenarios
- local Ollama smallest-two Gemma matrix exists for `ollama/gemma4:e4b` and
  `ollama/gemma4:12b`, with smoke, integrity, and runtime caveats
- reports show evidence health, operational reliability, claim ledger, and
  "what cannot be defended"
- `reports/benchmark-quality-research-report-<date>.md` exists
- `reports/post.md` exists and is LinkedIn-postable without unsupported claims
- no report presents partial matrix results as a public leaderboard

## The Practical North Star

The benchmark should be small enough that a serious engineer can inspect every
important failure, but rigorous enough that a skeptical reader cannot dismiss
the result as hidden-test trickery, runtime contamination, or leaderboard hype.

The central claim to earn is:

> Under realistic sparse tickets and weak public tests, public green is often
> not acceptance. This harness can show exactly when that happens, why it
> happens, whether explicit contracts fix it, and how much variance remains
> across attempts and models.
