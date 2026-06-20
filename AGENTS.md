# AGENTS.md

## Purpose

This repo is a coding-agent evaluation harness. The core question is:

> Did the model actually fix the problem, or did it only make visible CI green?

Each scenario has public tests visible to the model and hidden acceptance tests
injected after the model exits. `public_pass=1` and `hidden_pass=0` is a
**false-green**. The main metric is the **trust gap**: public pass rate minus
hidden pass rate.

This is a behavior microscope, not a public leaderboard. Preserve evidence
quality and caveats when comparing models.

## Current State

- The North Mini evidence pack and reports exist, but the current product
  direction is broader: a reusable, config-driven **multi-model comparison
  pipeline**.
- The implementation plan for that next phase is
  `docs/model-comparison-eval-pipeline-plan-2026-06-20.md`.
- Local Ollama/Gemma 4 support is configured through repo-root `opencode.json`.
- `ollama/gemma4:31b` has one valid local smoke:
  `data/local-ollama-gemma4-31b-smoke.sqlite`,
  run `20260620T113108Z-docs_cli_sync-b3b1c215`,
  public pass and hidden pass in 224.8s.
- The harness now passes repo-root OpenCode config to generated worktrees via
  `OPENCODE_CONFIG`; keep that behavior.

## What Lives Here

- `ci_vibe_lab/runner.py` — core run pipeline:
  write scenario -> baseline -> OpenCode -> public -> patch -> hidden -> persist.
- `ci_vibe_lab/scenarios.py` — scenario definitions, hidden tests, prompt modes,
  and pack metadata.
- `ci_vibe_lab/analysis.py` — trust-gap, false-green, and value metrics.
- `ci_vibe_lab/report.py` — Markdown reports including `leaderboard` with
  evaluator review coverage and `integrity` for SHA256 artifact verification.
- `ci_vibe_lab/integrity.py` — artifact path, SHA256 hash, and audit-coverage
  verification for pre-report integrity gates.
- `ci_vibe_lab/evaluator.py` — evaluator-agent workbench and Pydantic review schema.
- `ci_vibe_lab/dashboard.py` — Streamlit dashboard with Matrix tab.
- `docs/` — methodology and implementation plans. Start with `docs/README.md`.
- `reports/` — generated reports. Start with `reports/REPORTS.md`.
- `data/` and `runs/` — gitignored runtime evidence. Do not commit them.

## Project Rules

- Always use `uv` / `uv run` for project Python commands.
- Do not expose hidden tests to the model-under-test path before OpenCode exits.
- Do not weaken hidden tests just to improve scores. Audit and classify instead.
- Do not count provider/config/no-output failures as semantic model failures.
- Do not count no-output timeouts as false-greens.
- Do not merge sparse and contract-visible lanes by default.
- Do not present partial matrix results as a public benchmark leaderboard.
- Keep raw artifacts as source evidence; SQLite is the query/index layer.
- Prefer adding pointers to docs over duplicating long explanations here.

## Current Next Task

The matrix pipeline, leaderboard report with evaluator coverage, integrity
verification, matrix evaluator integration, and dashboard Matrix tab are done.
The next substantial work is running the full Gemma 4 maintenance matrix and
generating the final multi-model comparison report from real evidence.

Runtime workflow:

```bash
# Preview and run a matrix
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-maintenance.json
uv run ci-vibe-matrix run configs/matrix/local-gemma4-maintenance.json

# Run evaluator reviews over false-greens
uv run ci-vibe-matrix evaluate configs/matrix/local-gemma4-maintenance.json --loose

# Generate the comparison report with evals
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-maintenance.json \
  --out reports/leaderboard-local-gemma4-maintenance.md \
  --include-artifact-index

# Verify artifact integrity
uv run ci-vibe-report integrity \
  --matrix configs/matrix/local-gemma4-maintenance.json \
  --out reports/integrity-local-gemma4-maintenance.md

# Inspect in the dashboard
CI_VIBE_DB="$(uv run ci-vibe-matrix dbs configs/matrix/local-gemma4-maintenance.json)" \
  uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

## Build, Test, Verify

```bash
# Environment
uv venv
source .venv/bin/activate
uv sync --extra app

# Full no-model test suite
uv run python -m unittest discover -s tests -v

# List scenarios
uv run ci-vibe-run list
uv run ci-vibe-run list --pack maintenance_value

# Harness-only smoke, no model tokens
uv run ci-vibe-run run \
  --challenge dependency_api_change \
  --no-opencode \
  --db /tmp/ci-vibe-smoke.sqlite \
  --runs-dir /tmp/ci-vibe-smoke-runs

# Inspect a stored run
uv run ci-vibe-run inspect \
  --db /tmp/ci-vibe-smoke.sqlite \
  --latest \
  --full

# Local Gemma 4 smoke path
uv run ci-vibe-run run \
  --challenge docs_cli_sync \
  --model ollama/gemma4:31b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 300 \
  --prompt-mode sparse \
  --db data/local-ollama-gemma4-31b-smoke.sqlite \
  --runs-dir runs/local-ollama/gemma4-31b/smoke

# Dashboard
uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

## Progressive Disclosure

- Current docs orientation: `docs/README.md`
- Challenge design: `docs/challenge-design.md`
- Fresh-run harness audit: `reports/north-mini-fresh-run-harness-audit-2026-06-20.md`
- Gemma 4 local lane: `docs/local-ollama-opponents.md`
- Multi-model pipeline plan: `docs/model-comparison-eval-pipeline-plan-2026-06-20.md`
- Historical report index: `reports/REPORTS.md`
- Scenario source of truth: `ci_vibe_lab/scenarios.py`
