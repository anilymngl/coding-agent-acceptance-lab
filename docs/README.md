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

Not done:

- `ci-vibe-matrix`
- JSON matrix config parser
- generic `ci-vibe-report leaderboard`
- dashboard matrix/leaderboard tab
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
