# AGENTS.md

## Purpose

A coding-agent evaluation harness. The central question: does the model
actually fix the problem, or does it just make CI green? Every scenario has
public tests (visible to the model) and hidden tests (injected after the
agent exits). A pass on public and a fail on hidden is a **false-green**.
The headline metric is the **trust gap** — public pass rate minus hidden
pass rate.

This is a behavior microscope, not a leaderboard benchmark. Treat results as
directional, not statistically stable.

## What Lives Here

- `ci_vibe_lab/` — the harness. Source of truth for runner, scenarios,
  evaluator, analysis, reports, dashboard.
- `challenges/` — standalone challenge directories with CHALLENGE.md cards
  for manual or automated evaluation. All are also registered in
  `ci_vibe_lab/scenarios.py`.
- `docs/challenge-design.md` — eval philosophy, pivots, and glimpses. Read
  this before editing scenarios or interpreting results.
- `reports/` — generated Markdown reports. Index in `reports/REPORTS.md`.
  The opinionated analysis is `reports/north-mini-analysis.md`.
- `data/` — SQLite result DBs. Gitignored. `results.sqlite` is canonical.
- `runs/` — worktrees, per-run artifacts, evaluator review dirs. Gitignored.

## Project Rules

- Scenarios are authored, not harvested. Each one has a `trap` (the tempting
  wrong path), `expected_behavior`, `success_signals`, and `failure_modes`.
  Hidden tests must check behavior, not pin a specific implementation. See
  `docs/challenge-design.md` before adding scenarios.
- The runner injects hidden tests only after the agent exits. Never expose
  hidden test source to the model-under-test path.
- The evaluator gets the answer key in `EVALUATION_PACKET.md`. It can validate
  a patch against intent but cannot audit test fairness. Keep this limit in
  mind when reading evaluator verdicts.
- Evidence quotes in evaluator reviews must be exact substrings of the
  evaluation packet. The harness validates this. Do not relax it.
- `data/` and `runs/` are gitignored runtime state. Never commit them.
- `north_mini_analysis.md` at repo root mirrors `reports/north-mini-analysis.md`.
  Prefer editing the one in `reports/` and syncing the root copy.

## How To Work

- Run the harness with `uv run`. The project uses `uv` for environment and
  dependency management, not raw pip.
- Three CLI entrypoints: `ci-vibe-run` (runner), `ci-vibe-report` (reports),
  `ci-vibe-evaluate` (evaluator agent). All accept `--help`.
- Use `--no-opencode` for harness-only smoke tests that record baseline and
  post-test state without spending model tokens.
- Use `--resume` to skip (scenario, attempt) pairs already in the DB. Safe
  to re-run the same command after an interruption.
- Use `--skip-timeouts` to skip scenarios that previously timed out
  (exit code 124).
- Experiment IDs are printed at the start of every run. Reattach with
  `--experiment-id` to continue a specific experiment.
- When comparing models, compare false-green rates, not absolute hidden
  pass rates. The trust gap is the deployment-changing number.

## Build, Test, Verify

```bash
# Environment
uv venv
source .venv/bin/activate
uv sync --extra app

# Harness self-tests (no model tokens needed)
uv run python -m unittest discover -s tests -v

# List challenges
uv run python -m ci_vibe_lab.runner list
uv run python -m ci_vibe_lab.runner list --pack product_workflows

# Prepare one challenge repo for inspection
uv run python -m ci_vibe_lab.runner prepare \
  --challenge timezone_ci_only \
  --out /tmp/timezone-ci-only

# Smoke-test the harness without a model
uv run ci-vibe-run run --challenge dependency_api_change --no-opencode \
  --db /tmp/ci-vibe-smoke.sqlite --runs-dir /tmp/ci-vibe-smoke-runs
uv run ci-vibe-run inspect --db /tmp/ci-vibe-smoke.sqlite --latest --full

# Run a model through challenges
uv run ci-vibe-run run \
  --challenge all --pack ci_forensics \
  --model "provider/model" --agent build --auto-approve

# Inspect a run
uv run ci-vibe-run inspect --db data/results.sqlite --latest --full

# Reports
uv run ci-vibe-report xray --db data/results.sqlite \
  --model opencode/north-mini-code-free --out reports/xray.md
uv run ci-vibe-report value --db data/maintenance-value-north-mini.sqlite \
  --model opencode/north-mini-code-free --pack maintenance_value \
  --out reports/maintenance-value.md

# Evaluator agent over hidden failures
uv run ci-vibe-evaluate run \
  --db data/results.sqlite --hidden-only --public-green-only \
  --target-model opencode/north-mini-code-free \
  --model deepseek/deepseek-v4-pro --auto-approve \
  --out runs/evaluator-agent/deepseek-reviews

# Dashboard
uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

The model under test requires the OpenCode CLI installed and configured:

```bash
opencode providers
opencode models
```

The `--model` string must match a `provider/model` name from `opencode models`.

## Progressive Disclosure

- Eval philosophy, pivots, and glimpses: `docs/challenge-design.md`
- Opinionated analysis and deployment policy: `reports/north-mini-analysis.md`
- Reports index: `reports/REPORTS.md`
- Scenario definitions and metadata: `ci_vibe_lab/scenarios.py`
- Runner pipeline (write → baseline → agent → public → patch → hidden → persist):
  `ci_vibe_lab/runner.py`
- Evaluator workbench and shadow-fix flow: `ci_vibe_lab/evaluator.py`
- Trust gap and value metrics: `ci_vibe_lab/analysis.py`
- SQLite schema and migrations: `ci_vibe_lab/db.py`
- Dashboard tabs: `ci_vibe_lab/dashboard.py`
