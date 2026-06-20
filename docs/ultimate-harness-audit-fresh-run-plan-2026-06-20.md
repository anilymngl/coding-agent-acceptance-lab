# Ultimate Harness Audit And Fresh-Run Plan

## Purpose

This plan exists because the current evaluation has produced a useful but
dangerous signal: models can make public CI green while hidden acceptance stays
red. That signal is worth keeping, but it is not yet clean enough to defend as
a mature benchmark result without a deeper audit.

The immediate concern is concrete:

- The review-hour metric created interpretive noise.
- DeepSeek's false-green rate looks surprisingly high for a strong model.
- Some hidden tests may be checking legitimate implied engineering contracts.
- Some hidden tests may be testing contracts that were not visible enough to the
  model under test.
- The final report must separate model weakness from harness-design pressure.

The goal is not to make the benchmark easier. The goal is to make the benchmark
more accountable. A hidden test can be hard, but it must be fair. A false-green
can be damning, but only if the missed contract was reasonably inferable from
the visible repo, prompt, docs, source names, public tests, or standard
engineering practice.

## Executive Summary

The next version of this evaluation should become a two-lane system:

1. **Behavior microscope lane**
   - Sparse prompts.
   - Public tests visible.
   - Hidden tests injected after the agent exits.
   - Measures public-test overfitting, diligence, search discipline, and
     semantic inference.

2. **Contract-visible lane**
   - Same repos and hidden tests.
   - The model also receives explicit acceptance criteria derived from scenario
     metadata.
   - Measures whether failures are caused by model capability or by underexposed
     task contracts.

The final report should not say "DeepSeek is bad" or "North Mini is good" from
one aggregate score. It should say exactly where each model failed, whether the
failure was fair, whether a stronger control model escaped the trap, and what
workflow policy the evidence supports.

## Current State

### Existing Strengths

The harness already has important pieces:

- Scenario generation is deterministic.
- Public tests are visible during the agent run.
- Hidden tests are injected only after the agent exits.
- Run artifacts include prompts, patches, public output, hidden output, and raw
  OpenCode streams.
- SQLite stores run rows for analysis and dashboarding.
- Evaluator-agent workbenches exist and preserve raw review artifacts.
- Pydantic validates evaluator JSON.
- The dashboard and reports already expose trust-gap thinking.
- The report index now distinguishes current canonical reports from historical
  partial reports.

### Current Weaknesses

The harness currently mixes several concepts under one false-green label:

- **Search miss:** the contract was present in the repo or public prompt, but
  the model did not inspect enough files.
- **Standard engineering miss:** the contract was not explicitly named, but a
  competent engineer should infer it from the task class.
- **Edge inference miss:** the hidden case is a reasonable edge case, but the
  public prompt/test did not state it.
- **Underspecified hidden contract:** the hidden test checks behavior that was
  not visible enough to support a strong model-failure claim.
- **Possible harness bug:** the hidden test, public test, metadata, runner, or
  metric calculation is wrong.

The current reports also previously allowed the review-throughput metric to be
misread. That has been partly fixed by separating:

- selected accepted patch review throughput
- all-attempt review throughput

But for the next fresh run, review-hour metrics should be demoted from headline
model ranking and treated as a secondary reviewability/economics metric.

## Core Questions To Answer

The full audit and fresh run must answer these questions:

1. Are hidden tests legitimate acceptance tests or arbitrary gotchas?
2. Which false-greens are fair evidence of model failure?
3. Which false-greens are really spec-exposure failures?
4. Does a stronger model fail because the task is intrinsically hard, because
   the harness creates public-test optimization pressure, or because the hidden
   contract is underexposed?
5. Does contract-visible prompting reduce false-greens materially?
6. Are current metrics measuring the intended thing?
7. Can the final report defend claims without overstating them?
8. Can another person reproduce the run and inspect every artifact?

## Non-Negotiable Principles

### Do Not Weaken The Benchmark To Make Models Look Better

If a hidden test checks a fair contract, keep it. Strong models should be
allowed to fail real acceptance requirements. The goal is not to remove traps.
The goal is to classify traps honestly.

### Do Not Hide Harness Weakness

If a hidden test is too implicit, label it. If it should be moved to the
contract-visible lane, move it. If it should be quarantined, quarantine it.

### Do Not Treat Review-Hour As A Model Quality Score

Review-hour metrics are useful only after the report explains their denominator.
They can support review-cost analysis, but they should not outrank hidden pass,
false-green rate, failure taxonomy, or contract visibility.

### Preserve The Sparse-Prompt Lane

Sparse prompting is still useful because real agent workflows often have weak
specs and visible failing tests. This lane measures behavior under ambiguous
work conditions. It should remain, but it must be labeled as such.

### Add A Contract-Visible Lane

A mature eval must be able to say whether the model failed despite being given
the contract. This is the cleanest way to separate model capability from
under-specification.

## Definitions

### Public Pass

The public test suite passes after the model patch. These tests were visible to
the agent during the OpenCode run.

### Hidden Pass

The hidden acceptance suite passes after hidden tests are injected. These tests
were not visible to the agent during the OpenCode run.

### False-Green

`public_pass=1` and `hidden_pass=0`.

This should no longer be treated as one monolithic category. Every false-green
must receive a fairness classification.

### Trust Gap

`public_pass_rate - hidden_pass_rate`.

This remains a central metric, but it must be reported with lane, pack, model,
and audit-status filters.

### Selected-Review Throughput

Accepted patches divided by estimated review hours for only the selected
accepted patches.

This answers: "How cheap are the accepted patches to review after selection?"

### All-Attempt Review Throughput

Accepted patches divided by estimated review hours for all attempted patches in
the workflow.

This answers: "How much accepted work did the full attempt workflow produce per
estimated review hour?"

### Contract Visibility

How visible the hidden acceptance contract was to the model under test.

Proposed levels:

- `explicit`: stated in prompt, README, comments, public tests, or source docs.
- `repo_inferable`: not directly stated, but inferable by inspecting nearby
  source files or obvious sibling usages.
- `standard_practice`: not written, but expected from common engineering
  practice for the task type.
- `edge_inferable`: reasonable edge case, but not strongly signaled.
- `underexposed`: hidden test adds contract that the model had little reason to
  infer.
- `bug_or_invalid`: test or harness behavior appears wrong.

### Fair False-Green

A false-green where the missed hidden contract is `explicit`,
`repo_inferable`, or strong `standard_practice`.

### Weak False-Green

A false-green where the missed hidden contract is `edge_inferable` or
`underexposed`.

### Invalid False-Green

A false-green where the hidden test or harness is classified as
`bug_or_invalid`.

## Target End State

At the end of this work, the repo should contain:

- audited scenario metadata
- revised challenge prompts where needed
- explicit prompt-mode support in the runner
- a fresh full run across selected models and lanes
- evaluator-agent review over all material false-greens
- updated dashboard metrics and filters
- a final end report that makes defensible claims only
- a clean git history with each major change committed separately

## Workstream 1: Scenario Fairness Audit

### Objective

Review every scenario and classify whether its hidden acceptance criteria are
fair, underexposed, or invalid.

### Scope

Audit all registered scenarios in `ci_vibe_lab/scenarios.py`, grouped by pack:

- `ci_forensics`
- `product_workflows`
- `data_semantics`
- `maintenance_value`

Also verify standalone `challenges/` directories against registered scenarios.

### Audit Questions Per Scenario

For each scenario, answer:

1. What does the public prompt explicitly say?
2. What does the visible public test explicitly check?
3. What can the model infer by inspecting source files?
4. What can the model infer from names, comments, constants, schemas, generated
   artifacts, docs, or README files?
5. What does the hidden test check?
6. Is each hidden assertion behavior-based?
7. Does any hidden assertion pin implementation details unnecessarily?
8. Is the hidden contract explicit, repo-inferable, standard-practice,
   edge-inferable, underexposed, or invalid?
9. Should the scenario remain in sparse-prompt headline metrics?
10. Should the scenario remain only in contract-visible metrics?
11. Should the prompt be revised?
12. Should the hidden test be revised?
13. Should the scenario be quarantined?

### Required Scenario Audit Fields

Add or extend scenario audit metadata so every scenario has:

- `scenario`
- `pack`
- `audit_version`
- `audit_status`
- `risk_area`
- `impact_weight`
- `contract_visibility`
- `fairness_classification`
- `hidden_legitimacy_score`
- `inferability_score`
- `public_prompt_sufficiency_score`
- `public_test_sufficiency_score`
- `standard_practice_score`
- `implementation_flexibility_score`
- `recommended_lane`
- `requires_prompt_revision`
- `requires_hidden_revision`
- `audit_notes`
- `audited_by`
- `updated_at`

### Proposed Audit Status Values

Use these statuses:

- `accepted_sparse`: valid for sparse-prompt headline metrics.
- `accepted_contract_visible`: valid only when acceptance criteria are visible.
- `revise_public_prompt`: keep scenario, but revise prompt before fresh run.
- `revise_hidden_test`: hidden acceptance needs adjustment.
- `quarantine`: exclude from headline metrics until fixed.

### Proposed Fairness Classifications

Use these classifications:

- `search_miss`
- `standard_engineering_miss`
- `semantic_contract_miss`
- `edge_inference_miss`
- `underexposed_contract`
- `harness_or_test_bug`

### Initial Suspect Scenarios

These need special attention because they may be too implicit for sparse-prompt
headline claims:

- `batch_splitter_utility`
  - Hidden test checks non-positive batch size.
  - This is a reasonable utility contract, but it is not visible in the current
    prompt.
  - Likely classification: `edge_inference_miss` or prompt revision.

- `explicit_validation_matrix`
  - Prompt says "documented finite validation rules," but the visible repo may
    not actually contain a full document.
  - If no document exists, this is underexposed.
  - Likely action: add visible docs or move to contract-visible lane.

- `adapter_field_rename`
  - Hidden test checks old-field backward compatibility and optional email
    preservation.
  - The prompt says normalize adapter boundary only. Backward compatibility is
    plausible, but optional email preservation may need stronger visibility.
  - Likely action: classify per assertion, possibly revise prompt or add
    visible fixture/comment.

- `logger_warn_migration`
  - Hidden test checks another runtime file.
  - This is likely fair because a mechanical migration implies repo search.
  - Likely classification: `search_miss`.

- `utcnow_timezone_migration`
  - Hidden test checks another function in same file.
  - This is likely fair because the task is a mechanical migration.
  - Likely classification: `search_miss`.

### Audit Deliverables

Produce:

- `reports/scenario-audit-2026-06-20.md`
- updated SQLite `scenario_audits` rows
- optional generated CSV export
- a table of quarantined or revised scenarios
- a table of accepted sparse-lane scenarios
- a table of contract-visible-only scenarios

## Workstream 2: Prompt-Mode Architecture

### Objective

Add explicit prompt modes so the same scenario can be evaluated under different
spec exposure levels.

### Required Prompt Modes

Add runner support for:

- `sparse`
- `contract_visible`
- `audit_visible`

### Sparse Mode

Sparse mode preserves current behavior:

- prompt lede
- scenario title
- generic instructions
- public tests only
- no hidden answer key

This lane tests how the model behaves when the task resembles normal weakly
specified CI repair.

### Contract-Visible Mode

Contract-visible mode adds scenario metadata to the prompt:

- expected behavior
- success signals
- known failure modes
- explicit constraints

It must not reveal hidden test source code. It should reveal acceptance
contracts in plain English.

Example prompt addition:

```text
Acceptance contract:
- Split in stable order by positive batch size.
- Return no empty batches.
- Reject non-positive batch sizes.

Known failure modes to avoid:
- Leaves an empty tail batch.
- Silently accepts batch_size <= 0.
- Sorts or reorders input items.
```

### Audit-Visible Mode

Audit-visible mode is for harness debugging only. It can include:

- scenario trap
- intended hidden-contract summary
- audit notes

This mode should not be used for headline model evaluation. It exists to debug
whether the model can solve the challenge when the full intent is visible.

### Runner Changes

Add CLI flag:

```bash
uv run ci-vibe-run run \
  --prompt-mode sparse
```

Default should remain `sparse` for backward compatibility.

Persist in SQLite:

- `prompt_mode`
- `contract_visibility`
- `scenario_audit_status`
- `scenario_audit_version`

Artifact prompt files must clearly include the prompt mode.

### Report Changes

Reports must group by `prompt_mode`.

Headline metrics should default to:

- accepted sparse-lane scenarios
- latest fresh-run databases
- no quarantined scenarios

Contract-visible metrics should be shown as a diagnostic comparison, not mixed
into sparse headline metrics.

## Workstream 3: False-Green Taxonomy

### Objective

Replace one undifferentiated false-green count with a taxonomy that explains
what failed and whether the failure is fair.

### New Run-Level Classification

Add a table or derived layer for false-green review:

- `run_id`
- `scenario`
- `pack`
- `model`
- `prompt_mode`
- `public_pass`
- `hidden_pass`
- `false_green_type`
- `contract_visibility`
- `fairness_classification`
- `root_cause_category`
- `harness_verdict`
- `evaluator_verdict`
- `human_audit_verdict`
- `confidence`
- `notes`

### False-Green Type Values

Use:

- `search_miss`
- `edge_case_miss`
- `semantic_boundary_miss`
- `business_policy_miss`
- `mechanical_scope_miss`
- `underspecified_contract`
- `test_or_harness_bug`

### Harness Verdict Values

Use:

- `valid_model_failure`
- `valid_but_weak_signal`
- `spec_exposure_failure`
- `invalid_harness_failure`
- `needs_review`

### How This Changes Metrics

Reports should show:

- raw false-green rate
- fair false-green rate
- weak false-green rate
- invalid false-green count
- prompt-mode delta

Example:

```text
Raw false-green: 14/33
Fair false-green: 9/33
Weak/spec-exposure false-green: 5/33
Invalid false-green: 0/33
```

This prevents one number from carrying too much interpretive weight.

## Workstream 4: Metric Cleanup

### Objective

Make metrics describe exactly what they measure.

### Keep As Headline Metrics

Use these as headline metrics:

- public pass rate
- hidden pass rate
- trust gap
- raw false-green rate
- fair false-green rate
- contract-visible recovery rate
- best-of-N scenario success for multi-run packs

### Demote To Secondary Metrics

Keep but demote:

- selected-review throughput
- all-attempt review throughput
- median changed lines
- patch files touched
- duration
- accepted patches per runtime hour

These are useful economics metrics, but they should not determine model
capability ranking.

### Add New Metrics

Add:

- `contract_visible_recovery_rate`
  - Among sparse false-greens, fraction fixed in contract-visible mode.

- `model_diligence_gap`
  - Hidden pass delta between sparse and contract-visible modes.

- `fair_false_green_rate`
  - Valid model failures divided by public-green runs.

- `spec_exposure_failure_rate`
  - Spec-exposure failures divided by public-green runs.

- `quarantine_rate`
  - Quarantined scenarios divided by total audited scenarios.

- `control_delta_hidden_pass`
  - Strong model hidden pass minus target model hidden pass.

- `control_delta_fair_false_green`
  - Strong model fair false-green rate minus target model fair false-green rate.

### Metric Naming Rules

Every report metric must answer:

- numerator
- denominator
- lane
- pack
- model
- scenario filtering
- whether repeated attempts are attempt-level or scenario-level

No metric should be reported without its denominator.

## Workstream 5: Harness Self-Test Review

### Objective

Review and strengthen the harness tests before running expensive model calls.

### Existing Test Areas To Review

Review `tests/test_harness.py` for:

- scenario generation
- hidden test injection
- database migration
- evaluator ingestion
- trust-gap math
- dashboard multi-DB loading
- value report generation
- ultimate report generation

### Add Tests For Prompt Modes

Required tests:

- sparse prompt does not include expected behavior
- contract-visible prompt includes expected behavior
- audit-visible prompt includes trap/audit notes
- hidden test source is never included in sparse or contract-visible prompt
- prompt mode persists to SQLite
- report grouping by prompt mode is correct

### Add Tests For Scenario Audits

Required tests:

- audit metadata is seeded for all scenarios
- quarantine excludes rows from headline metrics
- accepted sparse scenarios are included in sparse headline metrics
- accepted contract-visible scenarios are excluded from sparse headline metrics
- invalid hidden tests are excluded from model-failure metrics

### Add Tests For False-Green Taxonomy

Required tests:

- raw false-green count is unchanged
- fair false-green count excludes weak and invalid false-greens
- spec-exposure false-greens appear in caveat tables
- no unclassified false-green can appear in final report without warning

### Add Tests For Metrics

Required tests:

- selected-review throughput matches accepted selected patches only
- all-attempt review throughput charges all attempts
- zero-review-minute denominator is safe
- best-of-N scenario success does not double-count attempts
- control comparison uses scenario units when packs have repeated attempts

### Harness Smoke Commands

Run:

```bash
uv run python -m py_compile \
  ci_vibe_lab/scenarios.py \
  ci_vibe_lab/runner.py \
  ci_vibe_lab/db.py \
  ci_vibe_lab/analysis.py \
  ci_vibe_lab/report.py \
  ci_vibe_lab/dashboard.py \
  ci_vibe_lab/evaluator.py \
  tests/test_harness.py

uv run python -m unittest discover -s tests -v
```

## Workstream 6: Scenario Prompt And Hidden-Test Revisions

### Objective

Make scenarios fair without making them toothless.

### Revision Rules

Revise public prompts when:

- hidden contract is reasonable but not sufficiently visible
- scenario title or lede implies less scope than hidden tests require
- a public test creates a misleading narrow target
- scenario metadata says "documented" but no visible document exists

Revise hidden tests when:

- hidden test checks implementation rather than behavior
- hidden test checks unrelated behavior
- hidden test is too brittle to harmless implementation variation
- hidden test cannot be explained as an acceptance contract

Quarantine scenarios when:

- fairness cannot be resolved quickly
- hidden and public contracts conflict
- scenario needs redesign
- evidence from previous runs is too contaminated to reuse

### Likely Revision Examples

#### `batch_splitter_utility`

Current issue:

- Hidden test expects `ValueError` for non-positive batch size.
- Public prompt does not say positive batch size.

Possible fixes:

- Add visible docstring or README saying `batch_size` must be positive.
- Or classify hidden failure as `edge_inference_miss`.
- Or move to contract-visible-only headline until revised.

#### `explicit_validation_matrix`

Current issue:

- Prompt says "documented finite validation rules."
- If no visible document lists the matrix, hidden tests may be underexposed.

Possible fixes:

- Add `docs/validation.md` in scenario repo.
- Public prompt should point to the document.
- Hidden tests can then fairly check all documented rules.

#### `adapter_field_rename`

Current issue:

- New field mapping is public.
- Backward compatibility and optional email preservation are hidden.

Possible fixes:

- Add a visible comment: "Adapter accepts old and new provider payload shapes
  during migration."
- Add fixture with optional email.
- Or classify optional email as weak signal if not added.

#### `logger_warn_migration`

Current issue:

- Public test checks one file.
- Hidden test checks another runtime file.

Recommendation:

- Keep as sparse accepted.
- A mechanical migration should imply repo search.

#### `utcnow_timezone_migration`

Current issue:

- Public test checks one function.
- Hidden test checks another function in same file.

Recommendation:

- Keep as sparse accepted.
- A mechanical migration should cover all target API calls in the relevant
  file.

## Workstream 7: Fresh Run Matrix

### Objective

Run a clean, audited model comparison after harness and scenario fixes.

### Fresh Database Naming

Use new DBs so old results remain preserved:

- `data/fresh-2026-06-20-north-mini-sparse.sqlite`
- `data/fresh-2026-06-20-north-mini-contract.sqlite`
- `data/fresh-2026-06-20-deepseek-sparse.sqlite`
- `data/fresh-2026-06-20-deepseek-contract.sqlite`
- optional: `data/fresh-2026-06-20-glm52-sparse.sqlite`
- optional: `data/fresh-2026-06-20-glm52-contract.sqlite`

### Fresh Runs Directory Naming

Use:

- `runs/fresh-2026-06-20/north-mini/sparse`
- `runs/fresh-2026-06-20/north-mini/contract-visible`
- `runs/fresh-2026-06-20/deepseek/sparse`
- `runs/fresh-2026-06-20/deepseek/contract-visible`

### Minimum Model Set

Run:

- `opencode/north-mini-code-free`
- `deepseek/deepseek-v4-pro`

Optional control:

- `opencode-go/glm-5.2`

### Minimum Pack Set

Run after audit:

- all accepted sparse `ci_forensics`
- all accepted sparse `product_workflows`
- all accepted sparse `data_semantics`
- all accepted sparse `maintenance_value`

Contract-visible lane:

- all scenarios that were accepted sparse
- all scenarios that were contract-visible-only
- all scenarios revised from underexposed to explicit

### Attempt Counts

Use:

- `ci_forensics`: 1 attempt per model per lane
- `product_workflows`: 1 attempt per model per lane
- `data_semantics`: 1 attempt per model per lane
- `maintenance_value`: 3 attempts per model per lane

Reason:

- Most packs test first-pass acceptance behavior.
- Maintenance value explicitly measures cheap repeated attempts and selection.

### Fresh Sparse North Mini Command

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack ci_forensics \
  --model opencode/north-mini-code-free \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --prompt-mode sparse \
  --db data/fresh-2026-06-20-north-mini-sparse.sqlite \
  --runs-dir runs/fresh-2026-06-20/north-mini/sparse
```

Repeat for each pack, adding `--runs 3` for `maintenance_value`.

### Fresh Contract-Visible North Mini Command

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack ci_forensics \
  --model opencode/north-mini-code-free \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --prompt-mode contract_visible \
  --db data/fresh-2026-06-20-north-mini-contract.sqlite \
  --runs-dir runs/fresh-2026-06-20/north-mini/contract-visible
```

Repeat for each pack, adding `--runs 3` for `maintenance_value`.

### Fresh DeepSeek Sparse Command

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack ci_forensics \
  --model deepseek/deepseek-v4-pro \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --prompt-mode sparse \
  --db data/fresh-2026-06-20-deepseek-sparse.sqlite \
  --runs-dir runs/fresh-2026-06-20/deepseek/sparse
```

Repeat for each pack, adding `--runs 3` for `maintenance_value`.

### Fresh DeepSeek Contract-Visible Command

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack ci_forensics \
  --model deepseek/deepseek-v4-pro \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --prompt-mode contract_visible \
  --db data/fresh-2026-06-20-deepseek-contract.sqlite \
  --runs-dir runs/fresh-2026-06-20/deepseek/contract-visible
```

Repeat for each pack, adding `--runs 3` for `maintenance_value`.

### Resume And Timeout Policy

All fresh commands should support:

- `--resume`
- `--skip-timeouts`
- stable `--experiment-id`

If a run times out:

- inspect raw OpenCode output
- classify timeout separately
- do not silently treat timeout as a normal hidden failure

## Workstream 8: Evaluator-Agent Review

### Objective

Run evaluator-agent review over all material false-greens after the fresh run.

### Scope

Review:

- all sparse-lane fair false-greens
- all sparse-lane weak false-greens
- all contract-visible false-greens
- all timeout cases if model produced a partial patch

### Evaluator Model

Use:

- `deepseek/deepseek-v4-pro`

Optional second evaluator:

- GLM or another strong available coding/reasoning model

### Evaluator Requirements

The evaluator must:

- inspect run packet
- inspect model patch
- inspect public and hidden output
- use the workbench
- optionally attempt shadow fix
- produce Pydantic-valid JSON
- quote exact packet evidence
- classify fairness and root cause

### Evaluator Command Template

```bash
uv run ci-vibe-evaluate run \
  --db data/fresh-2026-06-20-north-mini-sparse.sqlite \
  --hidden-only \
  --public-green-only \
  --target-model opencode/north-mini-code-free \
  --model deepseek/deepseek-v4-pro \
  --auto-approve \
  --out runs/evaluator-agent/fresh-2026-06-20-north-mini-sparse \
  --report reports/fresh-2026-06-20-north-mini-sparse-evaluator.md \
  --timeout 300 \
  --stream \
  --loose \
  --budget-minutes 6 \
  --token-budget 9000 \
  --tool-call-budget 30 \
  --shadow-fix-mode optional \
  --shadow-fix-budget-minutes 3 \
  --write-db
```

Repeat for DeepSeek and contract-visible DBs.

### Evaluator Report Requirements

The evaluator summary should show:

- reviewed false-greens
- valid schema count
- invalid schema count
- root cause taxonomy
- fairness taxonomy
- evidence quotes
- shadow-fix success rate
- recommended scenario audit changes

## Workstream 9: Dashboard Updates

### Objective

Make the dashboard useful for comparing sparse and contract-visible lanes.

### Required Controls

Add filters:

- model
- pack
- prompt mode
- audit status
- fairness classification
- false-green type
- latest run per model/scenario/prompt mode
- accepted sparse only
- include/exclude quarantined

### Required KPI Cards

Show:

- public pass rate
- hidden pass rate
- trust gap
- raw false-green rate
- fair false-green rate
- spec-exposure false-green rate
- contract-visible recovery rate
- best-of-3 maintenance success

### Required Tables

Add:

- false-green taxonomy table
- scenario audit table
- sparse versus contract-visible comparison
- model control comparison
- evaluator review table
- artifact index table

### Required Charts

Add:

- hidden pass by model and prompt mode
- false-green type distribution
- sparse-to-contract recovery by pack
- model delta by pack
- scenario-level heatmap

## Workstream 10: Final End Report

### Objective

Produce the final end report only after the harness audit, scenario revisions,
fresh runs, and evaluator reviews are complete.

### Report Filename

Use:

- `reports/north-mini-fresh-eval-final-report-2026-06-20.md`

If work crosses the date boundary, use the actual completion date.

### Required Report Sections

The report must include:

1. Title
2. Technical summary
3. What changed since the earlier report
4. Evidence inventory
5. Harness audit summary
6. Scenario audit summary
7. Metric definitions
8. Sparse-lane scorecard
9. Contract-visible scorecard
10. Sparse-to-contract recovery analysis
11. North Mini capability x-ray
12. DeepSeek control analysis
13. False-green taxonomy
14. Maintenance value analysis
15. Evaluator-agent findings
16. Model-card connection
17. What this eval does differently from SWE-bench and Terminal-Bench
18. What claims are defensible
19. What claims are not defensible
20. Deployment policy
21. Artifact index
22. Reproduction commands
23. Appendix: quarantined scenarios
24. Appendix: old reports and surfacing conditions

### Required Top-Line Claims

The report should answer:

- Is North Mini operationally competent?
- Is the public-green hidden-red trust gap real?
- How much of the trust gap is fair model failure?
- How much is spec-exposure failure?
- Does DeepSeek recover when contracts are visible?
- Are product workflows hard for both models?
- Is maintenance work a useful zone?
- What should a user actually do with this model?

### Required Claim Ledger

Every major claim must have:

- claim
- evidence
- source DB
- artifact path
- confidence
- caveat
- whether it is sparse-lane or contract-visible evidence

### Required Caveats

The final report must state:

- This is not a public leaderboard benchmark.
- Hidden tests are authored acceptance contracts.
- Sparse-prompt results intentionally test under-specified workflows.
- Contract-visible results are cleaner model-capability evidence.
- Multi-seed scaling is still limited.
- Review-hour metrics are secondary economics metrics.
- Stronger model controls are calibration, not definitive ranking.

## Workstream 11: Reproducibility And Artifact Integrity

### Objective

Make every claim inspectable from local artifacts.

### Required Artifact Index Columns

For every run:

- run id
- source DB
- model
- pack
- scenario
- prompt mode
- audit status
- public pass
- hidden pass
- false-green type
- prompt path
- patch path
- public output path
- hidden output path
- OpenCode stdout path
- evaluator review path
- patch SHA256
- prompt SHA256
- hidden output SHA256

### Required Integrity Checks

Before final report:

- verify every artifact path exists
- verify every listed SHA256 can be recomputed
- verify DB row count matches report row count
- verify scenario audit rows exist for every scenario
- verify no unclassified false-green is silently included
- verify quarantined scenarios are excluded from headline metrics

## Workstream 12: Git And Execution Hygiene

### Branching

Continue on:

- `codex/ultimate-eval-report`

Or create a fresh branch if this work should be isolated:

- `codex/harness-audit-fresh-run`

### Commit Plan

Use separate commits:

1. `docs: add harness audit fresh-run plan`
2. `feat: add prompt modes`
3. `feat: add scenario audit taxonomy`
4. `fix: revise underexposed scenarios`
5. `feat: add false-green classification metrics`
6. `feat: update dashboard for prompt lanes`
7. `docs: add fresh final eval report`

### Dirty Tree Rule

Before each major phase:

```bash
git status -sb
```

After each major phase:

```bash
uv run python -m unittest discover -s tests -v
git status -sb
```

Do not mix runtime data commits with source/doc commits. `data/` and `runs/`
remain gitignored.

## Acceptance Criteria

The work is complete only when all conditions are met:

- every scenario has audit metadata
- no unclassified false-green appears in final report
- sparse and contract-visible lanes are both supported
- tests pass
- fresh run DBs exist locally
- evaluator-agent reviews exist for material false-greens
- dashboard can load fresh DBs and filter by prompt mode
- final report includes claim ledger and artifact index
- old reports remain preserved with surfacing conditions
- git worktree is clean after final commit

## Risk Register

### Risk: Prompt Modes Change The Benchmark Too Much

Mitigation:

- preserve sparse lane
- report contract-visible lane separately
- never merge both lanes into one headline number

### Risk: Scenario Audit Becomes Subjective

Mitigation:

- define audit fields
- require notes per scenario
- preserve hidden tests and prompts as evidence
- optionally use evaluator-agent review as a second opinion

### Risk: Fresh Runs Are Expensive Or Slow

Mitigation:

- run audited packs first
- use `--resume`
- use `--skip-timeouts`
- stop after minimum model set before optional GLM control

### Risk: DeepSeek Still Looks Bad

Mitigation:

- classify false-greens
- compare sparse and contract-visible deltas
- avoid broad claims
- report where failures are fair versus underexposed

### Risk: North Mini Looks Better Than Expected

Mitigation:

- keep raw artifacts
- inspect patches
- use hidden acceptance
- compare against controls
- do not infer broad leaderboard ranking

### Risk: Review-Hour Metrics Distract Again

Mitigation:

- keep review metrics secondary
- name denominators explicitly
- do not use them as headline model-capability metrics

## Concrete Execution Order

### Phase 0: Freeze Current Evidence

1. Confirm current branch.
2. Confirm current reports are committed.
3. Confirm current DBs are not modified.
4. Write this plan.

### Phase 1: Harness Audit

1. Review `ci_vibe_lab/runner.py`.
2. Review `ci_vibe_lab/scenarios.py`.
3. Review `ci_vibe_lab/analysis.py`.
4. Review `ci_vibe_lab/report.py`.
5. Review `ci_vibe_lab/dashboard.py`.
6. Review `ci_vibe_lab/evaluator.py`.
7. Review `ci_vibe_lab/db.py`.
8. Record issues in a harness audit report.

### Phase 2: Scenario Audit

1. Generate scenario audit skeleton.
2. Fill audit fields for every scenario.
3. Mark suspect scenarios.
4. Decide revise/accept/quarantine.
5. Commit audit metadata.

### Phase 3: Prompt Modes

1. Implement prompt-mode rendering.
2. Add DB column/migration.
3. Add CLI flag.
4. Add prompt artifact labeling.
5. Add tests.

### Phase 4: Scenario Revisions

1. Revise underexposed prompts.
2. Add visible docs where needed.
3. Revise hidden tests only when invalid or too brittle.
4. Regenerate scenario cards if applicable.
5. Run harness self-tests.

### Phase 5: Metric And Report Refactor

1. Add false-green taxonomy helpers.
2. Add fair false-green metrics.
3. Add contract-visible recovery metrics.
4. Update reports.
5. Update dashboard.
6. Add tests.

### Phase 6: Fresh Runs

1. Run North Mini sparse.
2. Run North Mini contract-visible.
3. Run DeepSeek sparse.
4. Run DeepSeek contract-visible.
5. Optional: run GLM sparse/contract-visible.
6. Inspect timeouts and failed runs.
7. Save commands and DB inventory.

### Phase 7: Evaluator Reviews

1. Identify all material false-greens.
2. Run evaluator agent.
3. Ingest reviews.
4. Validate schema.
5. Summarize root causes.

### Phase 8: Final Report

1. Generate final report.
2. Read the report manually.
3. Verify source DB counts.
4. Verify artifact links.
5. Verify claim ledger.
6. Verify caveats.
7. Commit final report.

## Final Report Decision Rules

Use these rules when writing the final report:

- If sparse false-greens disappear in contract-visible mode, call it a
  spec-exposure issue, not a pure model failure.
- If false-greens remain in contract-visible mode, call it stronger evidence of
  model limitation.
- If DeepSeek and North Mini fail the same fair sparse scenarios, call the task
  family broadly hard under public-test pressure.
- If DeepSeek recovers and North Mini does not, call it model-capability
  separation.
- If a scenario is underexposed, exclude it from headline fair-false-green
  claims.
- If a scenario is invalid, quarantine it.
- If review-hour changes model ranking, explain the denominator before using it.

## One-Line Goal Statement

GOAL STATEMENT: Execute `docs/ultimate-harness-audit-fresh-run-plan-2026-06-20.md` to turn the current vibe-eval harness into an audited two-lane sparse/contract-visible evaluation and produce a fresh defensible final report with classified false-greens, clean metrics, full artifacts, and no overstated model claims.
