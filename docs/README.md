# Documentation Index

Start here when picking up this repo.

## Current State

The project began as a North Mini Code trust-gap investigation. The reusable,
config-driven, multi-model comparison pipeline now exists and has produced its
first local two-model evidence set.

The implemented workflow is:

- one config defines models, packs, prompt lanes, timeouts, and output paths
- one command previews/runs a model matrix
- one report compares models without mixing runtime failures into model
  semantic failures
- Streamlit can load the generated DB set for interactive inspection

Historical design context:

- `model-comparison-eval-pipeline-plan-2026-06-20.md`
- `benchmark-quality-hardening-plan-2026-06-20.md`

The plan's ultimate goal prompt is implemented for the current scope. Treat the
plan as design history plus backlog, not as the current next task.

## Detailed Goals Status

Goal 1: reusable comparison machinery
complete for the first product slice. The repo has `ci-vibe-matrix`, JSON
matrix validation/planning, deterministic DB/run-dir expansion, run orchestration,
resume/status/DB listing, evaluator batch review, generic leaderboard reporting,
integrity verification, and a dashboard Matrix tab.

Goal 2: first real multi-model evidence
complete for `maintenance_value`, sparse prompt mode, pass@1. The completed
local matrix compares `ollama/gemma4:e4b` and `ollama/gemma4:31b`; 31b matches
North Mini at 7/10 hidden, e4b lands at 5/10 hidden, and all three show a 30%
trust gap on the same scenario class.

Remaining evidence goals:

- run `contract_visible` maintenance lanes to test whether explicit acceptance
  criteria reduce the sparse trust gap
- add broader packs, especially `ci_forensics` and `product_workflows`
- run pass@3 / repeated-attempt consistency analysis

## Matrix Quickstart

The reusable matrix pipeline is the safe path for multi-model, multi-pack, and
multi-lane comparisons. Use the small Gemma 4 smoke config before launching new
large local model work:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-e4b-smoke.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-e4b-smoke.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-e4b-smoke.json
```

For the benchmark-quality hardening goal's local smallest-two Gemma lane, smoke
12B before running the full e4b/12B matrix:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-12b-smoke.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-12b-smoke.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-12b-smoke.json --stop-on-failure

uv run ci-vibe-matrix validate configs/matrix/local-gemma4-smallest-two.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-smallest-two.json
```

Current local status: on 2026-06-20, Ollama was upgraded to `0.30.10`,
`gemma4:12b` pulled successfully, and OpenCode listed `ollama/gemma4:12b`.
The first matrix smoke produced an empty patch, but a diagnostic rerun passed
public and hidden acceptance. The sparse `local-gemma4-smallest-two` lane has
now run: e4b is complete, while 12B is mixed because
`explicit_validation_matrix` hit the 900s agent timeout. Treat that as local
runtime evidence, not a semantic model failure or false-green.

If 12B becomes non-viable, use the Qwen3.6 fallback config as a separate local
runtime lane, not as part of the Gemma-only matrix:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-e4b-qwen36-fallback.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-e4b-qwen36-fallback.json
```

Inspect the completed two-model local maintenance matrix:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-two-model.json
uv run ci-vibe-matrix status configs/matrix/local-gemma4-two-model.json
uv run ci-vibe-matrix dbs configs/matrix/local-gemma4-two-model.json
```

Preview before launching or refreshing model work:

```bash
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-two-model.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-two-model.json --dry-run --resume
```

Run the configured cells through the existing `ci-vibe-run` execution contract
only when intentionally creating fresh evidence:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-two-model.json --resume
```

Generate the comparison evidence report:

```bash
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-two-model.json \
  --out reports/leaderboard-local-gemma4-two-model.md \
  --include-artifact-index
```

The report keeps completed-attempt capability metrics separate from operational
reliability metrics. Do not treat no-output timeouts, provider/config failures,
or missing cells as semantic model failures.

For Ollama cells, `ci-vibe-matrix run` prewarms the model before invoking
`ci-vibe-run`. The warmup duration is written to `matrix-run.log`; it is not
part of the run row's `duration_seconds` or first-output timeout.

## Key Docs

### `model-comparison-eval-pipeline-plan-2026-06-20.md`

The product/engineering plan that drove the matrix implementation. It specifies
the `ci-vibe-matrix` CLI, JSON matrix config shape, generic leaderboard report,
dashboard UX, evidence status classification, tests, acceptance criteria, and
final handoff prompt.

### `benchmark-quality-hardening-plan-2026-06-20.md`

The next quality plan. It turns the current trust-gap microscope into a more
auditable benchmark-quality evidence system by adding contract-visible lanes,
interval smoke tests, external scenario audits, evaluator agreement, pass@3
variance, the local Ollama Gemma 4 e4b/12B matrix, a research report, a
LinkedIn-postable `reports/post.md`, and stricter claim ledgers.

### `ultimate-harness-audit-fresh-run-plan-2026-06-20.md`

The earlier full harness-audit and fresh-run plan. It explains why the eval needs
two lanes:

- sparse behavior microscope
- contract-visible capability lane

Keep its fairness/audit principles. Do not treat every hidden failure as a valid
model failure without checking whether the contract was visible enough.

### `local-ollama-opponents.md`

The local Gemma 4 lane. Current completed evidence:

- config: `../configs/matrix/local-gemma4-two-model.json`
- report: `../reports/gemma4-matrix-analysis-2026-06-20.md`
- integrity: `../reports/integrity-local-gemma4-two-model.md`
- result: e4b 5/10 hidden, 31b 7/10 hidden on `maintenance_value` sparse
- trust gap: 30% for both Gemma 4 rows and North Mini reference

Earlier valid local smoke:

- model: `ollama/gemma4:31b`
- DB: `data/local-ollama-gemma4-31b-smoke.sqlite`
- run: `20260620T113108Z-docs_cli_sync-b3b1c215`
- result: OpenCode exit `0`, public pass, hidden pass
- duration: 224.8 seconds

Use `--first-output-timeout 300` for `gemma4:31b`.

### `challenge-design.md`

The methodology document. Read this before editing scenarios, hidden tests, or
interpretation language.

Core idea:

- public tests measure visible CI repair
- hidden tests measure acceptance repair
- public-green/hidden-red is the trust-gap signal

## Report Docs

Start with:

- `../reports/REPORTS.md`

Important current reports:

- `../reports/north-mini-ultimate-eval-report-2026-06-20.md`
- `../reports/gemma4-matrix-analysis-2026-06-20.md`
- `../reports/leaderboard-local-gemma4-two-model.md`
- `../reports/integrity-local-gemma4-two-model.md`
- `../reports/north-mini-fresh-run-harness-audit-2026-06-20.md`
- `../reports/north-mini-code-evidence-pack-2026-06-20.md`

The fresh-run harness audit is especially important because it separates real
model behavior from OpenCode/provider no-output stalls.

## Current Implementation Status

Done:

- prompt modes: `sparse`, `contract_visible`, `audit_visible`
- scenario audit metadata
- evaluator-agent persistence and Pydantic validation
- dashboard filters for prompt mode and audit status
- runner progress flushing
- runner delay between attempts
- first-output timeout classification
- repo-root OpenCode config propagation into generated worktrees
- Gemma 4-only local Ollama config in `opencode.json`
- valid `ollama/gemma4:31b` smoke
- detailed model-comparison pipeline plan
- `ci-vibe-matrix` JSON config validation, planning, status, DB listing, and run orchestration
- `ci-vibe-report leaderboard` matrix evidence report with evaluator review coverage
- `ci-vibe-matrix evaluate` subcommand for batch evaluator reviews over matrix false-greens
- `ci-vibe-report integrity` subcommand for SHA256 artifact and audit verification
- dashboard Matrix tab with evidence health, scorecards, false-green inbox, and evaluator coverage
- initial `configs/matrix/local-gemma4-maintenance.json`
- small `configs/matrix/local-gemma4-e4b-smoke.json` with Ollama warmup
- small `configs/matrix/local-gemma4-12b-smoke.json` for the next local lane;
  first run completed but failed public/hidden with an empty patch, while a
  direct rerun passed public and hidden
- `configs/matrix/local-gemma4-smallest-two.json` for e4b/12B sparse plus
  `contract_visible`
- `configs/matrix/local-gemma4-e4b-qwen36-fallback.json` as the Qwen3.6
  fallback lane if Gemma 4 12B is not viable
- completed `configs/matrix/local-gemma4-two-model.json` sparse maintenance matrix
- sparse `configs/matrix/local-gemma4-smallest-two.json` run: e4b complete,
  12B mixed with one `agent_timeout`
- Gemma 4 matrix analysis, leaderboard, and integrity reports

Not done:

- contract-visible prompt lane matrix runs
- broader pack coverage in matrix (ci_forensics, product_workflows)
- pass@3 consistency analysis

## Operational Rules

- Use `uv run` for project commands.
- Keep `data/` and `runs/` out of git.
- Do not rewrite or delete historical DBs/runs.
- Do not expose hidden tests before the model exits.
- Do not count provider/config/no-output failures as semantic model failures.
- Do not count no-output timeouts as false-greens.
- Keep sparse and contract-visible lanes separate by default.
