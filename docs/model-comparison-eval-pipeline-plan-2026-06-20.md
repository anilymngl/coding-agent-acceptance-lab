# Model Comparison Eval Pipeline Plan

Date: 2026-06-20

## Purpose

The current harness can already run one OpenCode model against one challenge
set and produce rich artifacts. That is enough for single-model investigation,
but it is too manual for repeated comparison work.

The next product step is a general model-comparison evaluation pipeline:

- easy to trigger
- config-driven
- multi-model
- multi-pack
- multi-lane
- reproducible after interruption
- report-ready
- dashboard-ready
- honest about evidence quality

The goal is not to create a public leaderboard prematurely. The goal is to make
model comparison operationally easy while preserving the core discipline of this
project: public pass is not acceptance, hidden tests must be auditable, runtime
failures must not be confused with semantic failures, and every claim must link
back to inspectable artifacts.

## Product Goal

Build a one-command workflow that can answer:

> Given a set of models, packs, and prompt lanes, how do these coding agents
> compare on visible CI repair, hidden acceptance, trust gap, runtime
> reliability, false-green behavior, and artifact quality?

The user should be able to run:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-maintenance.json \
  --out reports/local-gemma4-maintenance-leaderboard-2026-06-20.md
```

Then inspect results in Streamlit:

```bash
CI_VIBE_DB="data/matrix/local-gemma4-maintenance/**/*.sqlite" \
  uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

This is the desired user experience: the user chooses models and packs in a
small config file, runs one command, and receives a comparison report with
artifact links and caveats.

## Why This Matters

### The Current Manual Flow Is Too Fragile

Right now, running a comparison requires manually composing repeated commands:

- choose model
- choose pack
- choose prompt mode
- choose DB path
- choose runs directory
- repeat for every cell
- remember which cells are comparable
- generate reports by hand

This invites subtle mistakes:

- mixing old and fresh DBs accidentally
- comparing sparse rows against contract-visible rows
- counting no-output timeouts as model failures
- forgetting `--first-output-timeout`
- forgetting `--delay-seconds`
- rerunning into an old DB with a different experimental meaning
- ranking partial cells against complete cells

A matrix runner and leaderboard report should make the safe path the easy path.

### Local Models Need Special Runtime Accounting

Local Ollama models, especially `ollama/gemma4:31b`, can be slow to load. A
successful local smoke took 224.8 seconds before completion. A 120-second
first-output guard was too strict for that model, while a 300-second guard was
usable.

The pipeline must therefore separate:

- model capability
- agent behavior
- local runtime latency
- provider/config errors
- no-output stalls

Without this separation, local model evaluation becomes misleading.

### Comparison Is Useful Only If Evidence Health Is Visible

A simple table like "Model A: 70%, Model B: 60%" is not enough. The report must
show coverage and validity:

- how many scenarios were attempted
- how many rows are completed
- how many rows are runtime failures
- which packs/lanes are missing
- whether the model saw sparse or contract-visible prompts
- whether false-greens are fair, weak, or invalid
- whether artifacts are complete

The comparison should reward good evidence, not only high pass rates.

## Non-Goals

This plan should not create:

- a public benchmark leaderboard
- a single scalar model ranking
- a replacement for hidden-test audit
- a replacement for evaluator-agent diagnosis
- a hosted deployment
- a web product
- a new scenario format
- a new model runner independent of OpenCode

The first implementation should reuse the existing runner, DB schema, artifacts,
dashboard, and report machinery.

## Design Principles

### Keep The Existing Runner As The Execution Primitive

`ci-vibe-run run` already owns the actual challenge execution contract:

- generates disposable worktree
- records prompt
- calls OpenCode
- captures stdout/stderr
- runs public tests
- injects hidden tests
- runs hidden tests
- captures patch
- writes SQLite row
- writes artifacts

The matrix runner should orchestrate it. It should not duplicate it.

### Make Matrix Cells Explicit

Every result should belong to a matrix cell:

```text
matrix_id + model_alias + model_id + pack + prompt_mode + attempt_policy
```

This prevents accidental comparisons between unrelated runs.

### Use Deterministic Paths

Each cell should have predictable storage:

```text
data/matrix/<matrix_id>/<model_alias>/<pack>-<prompt_mode>.sqlite
runs/matrix/<matrix_id>/<model_alias>/<pack>/<prompt_mode>/
```

Example:

```text
data/matrix/local-gemma4-maintenance/gemma4-31b/maintenance_value-sparse.sqlite
runs/matrix/local-gemma4-maintenance/gemma4-31b/maintenance_value/sparse/
```

### Separate Capability From Reliability

The report must show two views:

1. **Completed-attempt capability**
   - excludes provider/config/no-output runtime failures
   - answers: when the model actually produced a patch attempt, how good was it?

2. **Operational reliability**
   - includes runtime failures
   - answers: how often does this model/runner combination produce a usable run?

Both matter. They must not be mixed into one opaque score.

### Treat Contract Lanes As First-Class

Sparse and contract-visible lanes must be comparable but not merged by default:

- sparse lane: tests behavior under weak specs and visible CI pressure
- contract-visible lane: tests whether explicit acceptance criteria reduce the
  trust gap

A model that fails sparse but succeeds contract-visible is not simply weak. It
may need clearer acceptance contracts. A model that fails contract-visible has a
stronger capability failure signal.

### Make Artifacts A Product Feature

Every row should have clickable artifact paths in reports and dashboard:

- prompt
- OpenCode stdout JSONL
- OpenCode stderr
- public output
- hidden output
- patch
- worktree

The report should not require trust in summary tables. A skeptical reader should
be able to jump from a metric to the raw evidence.

## Target User Experience

### Basic Flow

1. User creates or edits one JSON config.
2. User runs `uv run ci-vibe-matrix plan <config>` to preview commands.
3. User runs `uv run ci-vibe-matrix run <config>` to execute all cells.
4. User runs `uv run ci-vibe-report leaderboard --matrix <config> --out <report>`.
5. User opens Streamlit with the generated DB set.
6. User inspects false-greens and runtime failures.

### Desired Commands

Preview:

```bash
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-maintenance.json
```

Run:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json
```

Resume:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json --resume
```

Skip prior timeouts:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json --resume --skip-timeouts
```

Generate comparison:

```bash
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-maintenance.json \
  --out reports/local-gemma4-maintenance-leaderboard-2026-06-20.md \
  --include-artifact-index
```

Open dashboard:

```bash
CI_VIBE_DB="$(uv run ci-vibe-matrix dbs configs/matrix/local-gemma4-maintenance.json)" \
  uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

## Configuration Design

### File Format

Use YAML if a lightweight dependency is acceptable. If dependency minimization
is preferred, use JSON first and add YAML later.

Recommendation:

- MVP: JSON, no new dependency
- Later: YAML support using `pyyaml`

Because the project currently has only `pydantic` as a required dependency,
the first implementation should support JSON configs. A YAML example may be
documented only after adding `pyyaml`.

### Matrix Config Shape

Example JSON:

```json
{
  "matrix_id": "local-gemma4-maintenance-2026-06-20",
  "description": "Gemma 4 local smoke-to-maintenance comparison",
  "output_root": "data/matrix/local-gemma4-maintenance-2026-06-20",
  "runs_root": "runs/matrix/local-gemma4-maintenance-2026-06-20",
  "defaults": {
    "agent": "build",
    "auto_approve": true,
    "timeout": 900,
    "first_output_timeout": 300,
    "delay_seconds": 30,
    "runs": 1,
    "prompt_modes": ["sparse"],
    "packs": ["maintenance_value"]
  },
  "models": [
    {
      "alias": "gemma4-31b",
      "id": "ollama/gemma4:31b",
      "runtime": "ollama",
      "notes": "Installed local Gemma 4 31B, high first-token latency."
    }
  ],
  "packs": {
    "maintenance_value": {
      "runs": 1,
      "prompt_modes": ["sparse", "contract_visible"]
    }
  }
}
```

### Required Fields

`matrix_id`:

- stable identifier for this comparison run
- used in reports and path generation
- must be filesystem-safe

`models`:

- list of model objects
- each must have `alias` and `id`
- `alias` is used for paths and report labels
- `id` is passed directly to OpenCode as `--model`

`packs`:

- list or mapping of challenge packs
- mapping form allows per-pack attempt overrides

`prompt_modes`:

- `sparse`
- `contract_visible`
- optionally `audit_visible`, but not for headline comparisons

### Model Config Fields

Each model should support:

```json
{
  "alias": "gemma4-31b",
  "id": "ollama/gemma4:31b",
  "runtime": "ollama",
  "enabled": true,
  "agent": "build",
  "timeout": 900,
  "first_output_timeout": 300,
  "delay_seconds": 30,
  "environment": {
    "OPENCODE_CONFIG": "opencode.json"
  },
  "notes": "Local 31B model; first valid smoke took 224.8s."
}
```

Rationale:

- local models need different first-output thresholds
- hosted models may need lower delay
- some models may need a different OpenCode agent
- disabled models let users preserve config without running everything

### Pack Config Fields

Each pack should support:

```json
{
  "runs": 1,
  "prompt_modes": ["sparse", "contract_visible"],
  "challenge": "all"
}
```

For maintenance:

```json
{
  "runs": 3,
  "prompt_modes": ["sparse", "contract_visible"],
  "challenge": "all"
}
```

Rationale:

- most packs measure pass@1 behavior
- maintenance may intentionally measure repeated cheap attempts
- prompt modes may differ per pack

### Path Derivation

For each cell:

```text
db = <output_root>/<model_alias>/<pack>-<prompt_mode>.sqlite
runs_dir = <runs_root>/<model_alias>/<pack>/<prompt_mode>
experiment_id = <matrix_id>-<model_alias>-<pack>-<prompt_mode>
```

The matrix runner should print every derived path before executing.

## CLI Design

### New Command

Add a new console script:

```toml
ci-vibe-matrix = "ci_vibe_lab.matrix:main"
```

### Subcommands

`validate`:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-maintenance.json
```

Checks:

- JSON parses
- matrix id is valid
- models have aliases and ids
- packs exist
- prompt modes are valid
- output paths are derivable
- no two cells write to same DB unless intentionally allowed

`plan`:

```bash
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-maintenance.json
```

Prints:

- matrix id
- cell count
- generated DB paths
- generated runs dirs
- exact `ci-vibe-run run ...` commands
- estimated maximum attempts
- runtime guard settings

`run`:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json
```

Executes cells by invoking existing runner logic or subprocessing
`ci-vibe-run run`.

Preferred implementation:

- call `ci_vibe_lab.runner.run_scenarios()` in-process only if argument
  construction stays clean
- otherwise use `subprocess.run(["uv", "run", "ci-vibe-run", "run", ...])`
  for isolation and command transparency

MVP recommendation:

- subprocess the existing CLI
- log exact command to a matrix run log
- avoid duplicating runner code

`dbs`:

```bash
uv run ci-vibe-matrix dbs configs/matrix/local-gemma4-maintenance.json
```

Prints comma-separated DB paths for dashboard use.

`status`:

```bash
uv run ci-vibe-matrix status configs/matrix/local-gemma4-maintenance.json
```

Summarizes:

- cell DB exists or missing
- row count
- valid completed rows
- timeout rows
- provider/config error rows
- latest started/ended time

### Run Flags

Matrix runner should expose:

- `--resume`
- `--skip-timeouts`
- `--dry-run`
- `--only-model <alias>`
- `--only-pack <pack>`
- `--only-prompt-mode <mode>`
- `--max-cells <n>`
- `--stop-on-failure`

Rationale:

- local models are slow
- interruption is normal
- users need a way to test one cell before launching the full matrix

## Report Design

### New Report Command

Add:

```bash
uv run ci-vibe-report leaderboard \
  --db data/matrix/.../gemma4-31b/maintenance_value-sparse.sqlite \
  --db data/matrix/.../gemma4-31b/maintenance_value-contract_visible.sqlite \
  --out reports/model-leaderboard.md
```

Also support:

```bash
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-maintenance.json \
  --out reports/local-gemma4-maintenance-leaderboard.md
```

### Report Title

Use:

```text
# Model Comparison Evidence Report
```

Avoid:

```text
# Best Model Leaderboard
```

Reason:

The current benchmark is a behavior microscope. The report can include a
leaderboard-shaped table, but it must not imply public benchmark validity unless
coverage and audit standards are met.

### Report Sections

1. Executive Summary
2. Matrix Definition
3. Evidence Health
4. Completed-Attempt Scorecard
5. Operational Reliability Scorecard
6. Pack And Lane Breakdown
7. False-Green Breakdown
8. Runtime Failure Inbox
9. Scenario-Level Comparison
10. Artifact Index
11. What Can Be Defended
12. What Cannot Be Defended
13. Next Runs

### Evidence Health Table

Columns:

```text
Model | Pack | Lane | Expected Scenarios | Rows | Valid Completed | Runtime Failures | Missing Coverage | Evidence Status
```

Evidence statuses:

- `complete`
- `partial`
- `runtime_stalled`
- `missing`
- `mixed`
- `legacy`

### Completed-Attempt Scorecard

Rows:

```text
Model | Pack | Lane | Valid Rows | Public Pass | Hidden Pass | Trust Gap | False-Green Rate
```

Definition:

- only rows where OpenCode produced a meaningful completed attempt
- excludes provider/config/no-output runtime failures
- may include public-red completed attempts

### Operational Reliability Scorecard

Rows:

```text
Model | Pack | Lane | Total Rows | Completed | Timeout | No-Output Timeout | Provider/Config Error | Completion Rate
```

Why:

A model that is excellent when it runs but fails to run half the time is a
different operational choice than a model that is slightly weaker but reliable.

### False-Green Breakdown

Rows:

```text
Model | Pack | Lane | Scenario | Run ID | Fairness Classification | Missed Contract | Artifact Link
```

For MVP:

- use existing scenario audit metadata if present
- otherwise mark fairness as `unclassified`

Future:

- attach evaluator-agent review summaries

### Runtime Failure Inbox

Rows:

```text
Model | Pack | Lane | Scenario | Run ID | Failure Type | Duration | Stderr Summary | Stdout Bytes
```

Failure type rules:

- `provider_or_config_error` if OpenCode stdout/stderr contains
  `ProviderModelNotFoundError`, `APIError`, `does not support tools`, auth
  errors, or connection errors
- `no_output_timeout` if exit `124`, stdout length `0`, and stderr contains
  `produced no stdout/stderr`
- `agent_timeout` if exit `124` and stdout length is greater than `0`
- `runner_error` for other nonzero non-public-test failures

### Scenario-Level Comparison

Rows:

```text
Scenario | Pack | Lane | Model A Outcome | Model B Outcome | Model C Outcome | Notes
```

Outcomes:

- `hidden_pass`
- `false_green`
- `public_red`
- `agent_timeout`
- `no_output_timeout`
- `provider_error`
- `missing`

This is more useful than aggregate ranking because it shows whether models fail
on the same contracts.

### Artifact Index

For each row:

```text
Run ID | Model | Pack | Lane | Prompt | Patch | Public | Hidden | OpenCode stdout | OpenCode stderr
```

If the report is Markdown, use absolute or repo-relative paths consistently.

## Dashboard UX Plan

The dashboard should eventually have a dedicated "Matrix" or "Leaderboard" tab.

### Sidebar Filters

Add:

- matrix id
- model
- pack
- prompt mode
- evidence status
- completed-only toggle
- include runtime failures toggle
- latest per model/scenario/lane toggle

### Top KPI Cards

Cards:

- Valid completed rows
- Hidden pass rate
- Trust gap
- False-green rate
- Runtime failure rate
- No-output timeout rate

### Main Views

1. Evidence health grid
2. Model comparison table
3. Pack/lane breakdown
4. Scenario comparison heatmap
5. Failure inbox
6. Artifact inspector

### UI Principles

- Never show aggregate hidden pass without coverage count.
- Never merge sparse and contract-visible by default.
- Make runtime failures visually distinct from semantic failures.
- Make artifact inspection one click from any suspicious row.
- Use compact operational dashboard styling, not a marketing page.

## Data Model Additions

The current `runs` table can support the MVP without migration because DB paths
encode matrix identity. But for a cleaner long-term pipeline, add optional run
columns:

- `matrix_id`
- `model_alias`
- `evidence_status`
- `runtime_failure_type`

### MVP Recommendation

Do not migrate immediately. Derive these fields in report code:

- `matrix_id` from config or path
- `model_alias` from config mapping
- `evidence_status` from row fields
- `runtime_failure_type` from exit code/stdout/stderr

### Later Migration

Add columns once the shape stabilizes and dashboard filtering needs native DB
fields.

## Evidence Classification Rules

### Completed Attempt

A row is completed if:

- `opencode_exit_code == 0`
- OpenCode stdout exists or a patch exists
- public/hidden tests were executed

### Public Red

A completed attempt where:

- `public_pass == 0`
- `opencode_exit_code == 0`

This is a valid model failure, not a runtime failure.

### False-Green

A completed attempt where:

- `public_pass == 1`
- `hidden_pass == 0`

This is the central trust-gap signal.

### Hidden Pass

A completed attempt where:

- `public_pass == 1`
- `hidden_pass == 1`

### Provider Or Config Error

A row where:

- OpenCode exits nonzero before producing a useful agent run
- output mentions provider/model/auth/tool support/config errors
- no meaningful patch is produced

Examples already observed:

- `ProviderModelNotFoundError`
- `Model not found`
- `does not support tools`

### No-Output Timeout

A row where:

- `opencode_exit_code == 124`
- `opencode_stdout` length is `0`
- stderr contains `produced no stdout/stderr`

### Agent Timeout

A row where:

- `opencode_exit_code == 124`
- `opencode_stdout` length is greater than `0`

This means the agent started working but did not finish under the timeout.

## Implementation Phases

### Phase 1: Matrix Config And Planner

Deliverables:

- `ci_vibe_lab/matrix.py`
- `ci-vibe-matrix` console script
- JSON config parser
- Pydantic config models
- `validate`, `plan`, and `dbs` subcommands
- tests for config parsing and command expansion

Why first:

This creates the user-facing shape without spending model time.

Acceptance:

- invalid configs fail clearly
- valid configs produce deterministic cells
- `dbs` prints dashboard-compatible DB path list
- no model calls are made

### Phase 2: Matrix Runner

Deliverables:

- `run` subcommand
- subprocess execution of `uv run ci-vibe-run run ...`
- `--resume`
- `--skip-timeouts`
- `--dry-run`
- `--only-model`
- `--only-pack`
- `--only-prompt-mode`
- per-cell logging

Why second:

This turns the plan into operational automation while preserving the existing
runner contract.

Acceptance:

- one Gemma 4 sparse maintenance matrix cell can run end to end
- interruption can be resumed
- paths are deterministic
- logs show exact commands

### Phase 3: Generic Leaderboard Report

Deliverables:

- `ci-vibe-report leaderboard`
- accepts `--matrix` or repeated `--db`
- evidence health table
- completed-attempt scorecard
- operational reliability scorecard
- scenario-level comparison
- artifact index
- tests with fixture DB rows

Why third:

The user needs comparison output before dashboard polish.

Acceptance:

- reports do not mix runtime failures into false-green metrics
- partial coverage is labeled
- sparse and contract-visible rows are separated
- artifact paths appear in the report

### Phase 4: Dashboard Matrix Tab

Deliverables:

- matrix/leaderboard section in Streamlit
- evidence-status filters
- model/pack/lane selectors
- scenario comparison table
- runtime failure inbox
- artifact detail links

Why fourth:

The dashboard should reflect stable metrics after CLI/report semantics settle.

Acceptance:

- user can load all matrix DBs
- user can filter to completed-only
- user can inspect false-green rows
- user can distinguish local runtime failures from model semantic failures

### Phase 5: Evaluator Integration

Deliverables:

- matrix-aware evaluator run selection
- evaluate all completed public-green/hidden-red rows for selected models
- evaluator review status in leaderboard report
- optional evaluator agreement column

Why fifth:

Evaluator-agent diagnosis is valuable but expensive. It should run after the
basic matrix comparison identifies material false-greens.

Acceptance:

- all material false-greens can be batched into evaluator workbenches
- report shows evaluator verdict coverage

## First Config To Add

Create:

```text
configs/matrix/local-gemma4-maintenance.json
```

Contents:

```json
{
  "matrix_id": "local-gemma4-maintenance-2026-06-20",
  "description": "Gemma 4 local maintenance-value comparison smoke.",
  "output_root": "data/matrix/local-gemma4-maintenance-2026-06-20",
  "runs_root": "runs/matrix/local-gemma4-maintenance-2026-06-20",
  "defaults": {
    "agent": "build",
    "auto_approve": true,
    "timeout": 900,
    "first_output_timeout": 300,
    "delay_seconds": 30,
    "runs": 1,
    "prompt_modes": ["sparse"],
    "packs": ["maintenance_value"]
  },
  "models": [
    {
      "alias": "gemma4-31b",
      "id": "ollama/gemma4:31b",
      "runtime": "ollama",
      "notes": "Local Gemma 4 31B. Valid smoke docs_cli_sync passed in 224.8s."
    }
  ],
  "packs": {
    "maintenance_value": {
      "runs": 1,
      "prompt_modes": ["sparse"]
    }
  }
}
```

After that works, add:

```json
"prompt_modes": ["sparse", "contract_visible"]
```

Then optionally add hosted DBs to the report as historical comparison inputs,
without rerunning hosted models.

## First Real Run Recommendation

Do not start with all packs. Start with:

- model: `ollama/gemma4:31b`
- pack: `maintenance_value`
- lane: `sparse`
- runs: `1`
- timeout: `900`
- first-output-timeout: `300`
- delay: `30`

Reason:

- Gemma 4 31B has proven it can complete one smoke.
- Maintenance tasks are practical and bounded.
- Sparse first shows natural behavior under visible CI pressure.
- One attempt controls runtime cost.

If this works, run the same pack with `contract_visible`.

## Testing Plan

### Unit Tests

Add tests for:

- matrix config validation
- model alias slug validation
- pack validation
- prompt-mode validation
- deterministic DB path derivation
- command expansion
- `dbs` output
- evidence-status classification
- leaderboard metric calculations
- runtime failure classification
- sparse/contract separation

### CLI Smoke Tests

No-model matrix smoke:

```bash
uv run ci-vibe-matrix run configs/matrix/no-model-smoke.json --dry-run
```

Config validation:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-maintenance.json
```

Plan preview:

```bash
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-maintenance.json
```

Report fixture:

```bash
uv run ci-vibe-report leaderboard \
  --db data/local-ollama-gemma4-31b-smoke.sqlite \
  --out /tmp/gemma4-smoke-leaderboard.md
```

### Regression Tests

Always run:

```bash
uv run python -m unittest discover -s tests -v
```

## Failure Modes To Design For

### Model Not Found

Symptom:

- `ProviderModelNotFoundError`
- `Model not found`

Treatment:

- classify as `provider_or_config_error`
- do not count as false-green
- show under runtime failure inbox

### Tools Unsupported

Symptom:

- output says model does not support tools

Treatment:

- classify as `provider_or_config_error`
- mark model as incompatible with OpenCode agent loop
- do not run full matrix unless another agent mode is intentionally tested

### Slow First Token

Symptom:

- no output before first-output timeout

Treatment:

- classify as `no_output_timeout`
- for local 31B models, increase first-output timeout only if there is prior
  evidence that a longer window helps

### Agent Loop Timeout

Symptom:

- stdout contains tool calls
- exit `124`

Treatment:

- classify as `agent_timeout`
- count in operational reliability
- do not count as false-green

### Public Red

Symptom:

- OpenCode exit `0`
- public tests still fail

Treatment:

- classify as completed model failure
- count in completed-attempt capability
- not a false-green

### False-Green

Symptom:

- public pass
- hidden fail

Treatment:

- classify as trust-gap evidence
- attach scenario audit status
- evaluator-agent review if material

## UX Details

### Config File Naming

Use readable names:

```text
configs/matrix/local-gemma4-maintenance.json
configs/matrix/north-vs-deepseek-product.json
configs/matrix/full-two-lane-smoke.json
```

### Report Naming

Use:

```text
reports/model-comparison-<matrix_id>.md
reports/leaderboard-<matrix_id>.md
```

### Dashboard Loading

The matrix command should make dashboard launch easy:

```bash
CI_VIBE_DB="$(uv run ci-vibe-matrix dbs configs/matrix/local-gemma4-maintenance.json)" \
  uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

If shell globbing is unreliable, `dbs` should print the exact comma-separated DB
list from the config.

### Human-Readable Labels

Reports should show both:

- alias: `gemma4-31b`
- model id: `ollama/gemma4:31b`

Aliases are for readability. Model IDs are for reproducibility.

## Constraints

### Engineering Constraints

- Use `uv run` for commands.
- Keep current `ci-vibe-run` behavior stable.
- Do not make matrix runner mutate scenarios.
- Do not delete old DBs or runs.
- Do not require network for local report generation.
- Do not add heavy dependencies unless justified.
- Use JSON first to avoid a YAML dependency.
- Keep artifacts on disk as source of truth.
- SQLite is the index/query layer, not the evidence source.

### Evaluation Constraints

- Do not rank models without coverage counts.
- Do not merge prompt lanes by default.
- Do not count provider errors as model semantic failures.
- Do not count no-output timeouts as false-greens.
- Do not hide public-red failures.
- Do not claim general coding-model superiority from one pack.
- Do not compare local and hosted models without runtime caveats.

### UX Constraints

- One config should be enough to rerun a matrix.
- Reports should state exactly what was run.
- Commands should be copy-pasteable.
- Failure states should be understandable without reading code.
- Artifact links should be present for audit.
- The dashboard should not require manual DB guessing.

## Acceptance Criteria

The project reaches the intended state when:

- a user can define multiple models in one config
- a user can preview the matrix before running
- a user can run all cells with one command
- a user can resume after interruption
- a user can print all DB paths for dashboard use
- a generic report compares arbitrary models
- report separates completed-attempt metrics from runtime reliability
- report separates sparse and contract-visible lanes
- report includes artifact links
- local Gemma 4 can be included as a first-class model
- old hosted DBs can be included as historical comparison inputs
- unit tests cover config expansion and metric classification
- full test suite passes
- git worktree is clean

## Implementation Order

1. Add matrix config models and `ci-vibe-matrix validate`.
2. Add cell expansion and `ci-vibe-matrix plan`.
3. Add `ci-vibe-matrix dbs`.
4. Add `ci-vibe-matrix run --dry-run`.
5. Add real matrix execution by subprocessing `ci-vibe-run`.
6. Add `ci-vibe-report leaderboard`.
7. Add tests for report classification.
8. Add `configs/matrix/local-gemma4-maintenance.json`.
9. Add README quickstart.
10. Run a Gemma 4 sparse maintenance matrix cell.
11. Generate first leaderboard report.
12. Add dashboard enhancements after report semantics are stable.

## Open Questions

1. Should matrix config be JSON only initially, or should the project add YAML?
2. Should matrix IDs be user-provided only, or auto-generated when omitted?
3. Should reports include old DBs by default, or only explicit DBs?
4. Should `audit_visible` be allowed in matrix configs but excluded from
   headline reports?
5. Should local models default to `--first-output-timeout 300` while hosted
   models default to `120`?
6. Should matrix runner stop after the first provider/config error for a model?

Recommended defaults:

- JSON only first.
- Require explicit `matrix_id`.
- Reports use explicit DBs or config only.
- Allow `audit_visible`, but label it non-headline.
- Let model config override `first_output_timeout`.
- Continue after provider/config error unless `--stop-on-failure` is set.

## Ultimate Goal Prompt

Use this prompt to hand the next implementation phase to an agent:

```text
You are working in /Users/anilyamangil/Projects/north-mini-test on the CI Vibe Lab harness.

Implement the general model-comparison evaluation pipeline described in
docs/model-comparison-eval-pipeline-plan-2026-06-20.md.

The goal is to make multi-model, multi-pack, multi-lane coding-agent evaluation
easy to trigger and defensible to report. Preserve the existing ci-vibe-run
semantics and build on top of them.

Implement, in order:

1. Add a new ci-vibe-matrix CLI backed by ci_vibe_lab/matrix.py.
2. Support JSON matrix configs with Pydantic validation.
3. Add validate, plan, dbs, status, and run subcommands.
4. Expand configs into deterministic cells:
   model alias x pack x prompt mode.
5. Derive deterministic DB paths and runs directories:
   data/matrix/<matrix_id>/<model_alias>/<pack>-<prompt_mode>.sqlite
   runs/matrix/<matrix_id>/<model_alias>/<pack>/<prompt_mode>
6. Execute cells by subprocessing the existing ci-vibe-run run command.
7. Support --dry-run, --resume, --skip-timeouts, --only-model, --only-pack,
   --only-prompt-mode, --max-cells, and --stop-on-failure.
8. Add a generic ci-vibe-report leaderboard command that accepts either
   --matrix <config> or repeated --db inputs.
9. In the leaderboard report, separate completed-attempt capability metrics from
   operational reliability metrics.
10. Classify rows into hidden_pass, false_green, public_red, agent_timeout,
    no_output_timeout, provider_or_config_error, runner_error, and missing.
11. Keep sparse and contract_visible lanes separate by default.
12. Include evidence health, model/pack/lane scorecards, runtime failure inbox,
    scenario-level comparison, and artifact index.
13. Add configs/matrix/local-gemma4-maintenance.json using ollama/gemma4:31b,
    timeout 900, first_output_timeout 300, delay_seconds 30, maintenance_value,
    sparse lane first.
14. Update README with the matrix quickstart.
15. Add unit tests for config validation, command expansion, DB path generation,
    evidence classification, and leaderboard rendering.
16. Run uv run python -m unittest discover -s tests -v.
17. Keep git clean and commit the implementation in coherent commits.

Important constraints:

- Always use uv run for Python/project commands.
- Do not delete or rewrite existing historical DBs or run artifacts.
- Do not count provider/config/no-output failures as semantic model failures.
- Do not count no-output timeouts as false-greens.
- Do not merge sparse and contract-visible lanes by default.
- Do not present this as a public benchmark leaderboard.
- Every report claim must be backed by SQLite rows and artifact paths.

The desired user experience is:

uv run ci-vibe-matrix plan configs/matrix/local-gemma4-maintenance.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-maintenance.json \
  --out reports/leaderboard-local-gemma4-maintenance-2026-06-20.md \
  --include-artifact-index

When complete, the repo should let a user compare models through a small config
file, inspect all raw artifacts, and read a report that clearly distinguishes
model capability, hidden-contract trust gap, and operational runtime reliability.
```
