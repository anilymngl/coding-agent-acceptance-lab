# Documentation Index

Start here when picking up this repo.

## Current Direction

The project began as a North Mini Code trust-gap investigation. The current
next phase is broader: build a reusable, config-driven, multi-model comparison
pipeline for coding-agent evals.

The implementation target is:

- one config defines models, packs, prompt lanes, timeouts, and output paths
- one command previews/runs a model matrix
- one report compares models without mixing runtime failures into model
  semantic failures
- Streamlit can load the generated DB set for interactive inspection

Read:

- `model-comparison-eval-pipeline-plan-2026-06-20.md`

The ultimate goal prompt for the next implementation agent is at the end of
that file.

## Matrix Quickstart

The reusable matrix pipeline is the safe path for multi-model, multi-pack, and
multi-lane comparisons. Start by validating and previewing the small Gemma 4
smoke config before launching the 31B maintenance lane:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-e4b-smoke.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-e4b-smoke.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-e4b-smoke.json
```

Then validate and preview the broader local maintenance config:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-maintenance.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-maintenance.json
```

Run the configured cells through the existing `ci-vibe-run` execution contract:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json
```

Resume or inspect without launching new model work:

```bash
uv run ci-vibe-matrix status configs/matrix/local-gemma4-maintenance.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json --dry-run --resume
uv run ci-vibe-matrix dbs configs/matrix/local-gemma4-maintenance.json
```

Generate the comparison evidence report:

```bash
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-maintenance.json \
  --out reports/leaderboard-local-gemma4-maintenance-2026-06-20.md \
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

The current product/engineering plan. It specifies the future `ci-vibe-matrix`
CLI, JSON matrix config shape, generic leaderboard report, dashboard UX, evidence
status classification, tests, acceptance criteria, and final handoff prompt.

### `ultimate-harness-audit-fresh-run-plan-2026-06-20.md`

The earlier full harness-audit and fresh-run plan. It explains why the eval needs
two lanes:

- sparse behavior microscope
- contract-visible capability lane

Keep its fairness/audit principles. Do not treat every hidden failure as a valid
model failure without checking whether the contract was visible enough.

### `local-ollama-opponents.md`

The local Gemma 4 lane. Current valid local smoke:

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

Not done:

- full Gemma 4 maintenance matrix run
- final multi-model comparison report

## Operational Rules

- Use `uv run` for project commands.
- Keep `data/` and `runs/` out of git.
- Do not rewrite or delete historical DBs/runs.
- Do not expose hidden tests before the model exits.
- Do not count provider/config/no-output failures as semantic model failures.
- Do not count no-output timeouts as false-greens.
- Keep sparse and contract-visible lanes separate by default.
