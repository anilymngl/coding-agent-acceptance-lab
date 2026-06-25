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

- The North Mini evidence pack and reports exist, and the broader reusable,
  config-driven **multi-model comparison pipeline** is now implemented.
- The implementation plan is preserved as historical design context:
  `docs/model-comparison-eval-pipeline-plan-2026-06-20.md`.
- **Research exhibit published**: `publishables/` — self-contained HTML suite
  (pass@3 paper, evidence index, evaluator findings, scenario catalog, harness
  inventory). Open `publishables/index.html` in a browser.
- **Laguna XS.2 vs North Mini comparison** completed (pass@3, 33 scenarios).
  Config: `configs/matrix/laguna-xs2-vs-north-mini.json`. Reports:
  `reports/laguna-xs2-vs-north-mini-first-comparison.md`,
  `reports/laguna-xs2-vs-north-mini-leaderboard.md`,
  `reports/laguna-xs2-vs-north-mini-integrity.md`.
- Local Ollama/Gemma 4 support is configured through repo-root `opencode.json`.
- **Gemma 4 two-model matrix completed** (`configs/matrix/local-gemma4-two-model.json`):
  e4b 5/10 hidden, 31b 7/10 hidden on `maintenance_value` sparse.
  Same 30% trust gap as North Mini. Integrity passed with 120/120 artifacts.
  Analysis: `reports/gemma4-matrix-analysis-2026-06-20.md`.
- **Gemma 4 smallest-two sparse lane ran** (`configs/matrix/local-gemma4-smallest-two.json`):
  e4b sparse is complete; 12B sparse is mixed because
  `explicit_validation_matrix` hit a 900s `agent_timeout`. Integrity passed
  with 120/120 artifacts. Reports:
  `reports/leaderboard-local-gemma4-smallest-two.md` and
  `reports/integrity-local-gemma4-smallest-two.md`.
- `ollama/qwen3.6:27b` is configured only as a separate fallback lane
  (`configs/matrix/local-gemma4-e4b-qwen36-fallback.json`) if 12B is rejected
  as non-viable. Do not merge Qwen rows into Gemma-only claims.
- The harness now passes repo-root OpenCode config to generated worktrees via
  `OPENCODE_CONFIG`; keep that behavior.
- **Rate-limit backoff**: `--backoff-multiplier` and `--backoff-ceiling` flags
  control exponential backoff on consecutive rate-limit hits. Provider error
  markers extended with rate-limit signals (429, too many requests, etc.).
- **Model summary capture**: `model_summary` column (last text event from
  OpenCode JSONL stdout) stored in DB and surfaced in evaluator workbench.
- **Stale `challenges/` directory**: archived to `.archive/challenges/` and
  gitignored. The harness uses inline scenario strings in `scenarios.py`, not
  disk files. Only 7 of 37 scenarios existed there; it was an early manual-test
  concept never fully populated.

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
- `ci_vibe_lab/matrix.py` — matrix config expansion, run orchestration,
  rate-limit detection, inter-cell delay.
- `ci_vibe_lab/generate_evaluator_report.py` — generates evaluator-findings
  HTML from reviewed runs.
- `ci_vibe_lab/generate_gallery.py` — generates evidence-index HTML from DB.
- `check-opencode.sh` — one-shot health check for the full stack: Ollama runtime
  (processes, loaded/installed models, config-vs-disk coverage), OpenCode
  (web daemon, active agents, MCP servers, session/cost stats from
  `opencode.db`), and the eval harness (per-cell matrix progress bars,
  per-scenario run outcomes, false-green/timeout/trust-gap scores, evaluator
  coverage, disk usage, and log health). Flags stale runs, missing models, and
  unreviewed false-greens. Modes: `--quiet` (problems only), `--watch`
  (auto-refresh 5s), `--follow` (live log tail), `--deep` (per-model spend +
  matrix status tables), `--integrity` (runs `ci-vibe-report integrity` per
  config), `--raw` (unfiltered log). Runs in <1s by default; only `--integrity`
  invokes Python.
- `app/` — application modules (e.g. `dates.py` timezone-aware invoice dates).
- `publishables/` — self-contained HTML research exhibit (index, paper_v2,
  evidence-index, evaluator-findings, scenario-catalog, harness-built-target).
- `presentation/` — slide decks and LinkedIn posts for research findings.
- `docs/` — methodology and implementation plans. Start with `docs/README.md`.
- `reports/` — generated reports. Start with `reports/REPORTS.md`.
- `configs/matrix/` — model comparison matrix definitions.
- `.opencode/skills/` — agent skills (signal, signal-presentation-opencode,
  create-presentation).
- `.archive/` — gitignored historical artifacts (stale challenges directory).
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
- Each pass@k attempt is an independent fresh start (new worktree, no memory of prior attempts), not an iterative refinement on top of the previous attempt.
- Stale `challenges/` directory is archived to `.archive/challenges/` (gitignored); do not restore it.

## Current Detailed Goals

Goal 1: reusable comparison machinery
done for the current scope. `ci-vibe-matrix`, matrix config validation/planning,
run orchestration, status/DB listing, evaluator batch review, generic leaderboard
reporting, integrity verification, and the dashboard Matrix tab all exist.

Goal 2: first real multi-model evidence
done for sparse `maintenance_value` pass@1. Gemma 4 e4b and 31b both completed
the 10-scenario sparse lane, reports are generated, and integrity is verified.
Do not rerun this full sparse matrix unless intentionally refreshing evidence.

Goal 3: research exhibit (publishables/)
done. Self-contained HTML suite with pass@3 paper (Laguna XS.2 vs North Mini),
evidence index, evaluator findings, scenario catalog, harness inventory, and
cross-linked navigation. Open `publishables/index.html`.

Next evidence work:

- run `contract_visible` maintenance lanes to measure how much explicit
  acceptance criteria reduce sparse trust gaps
- evaluator-review the 3 false-greens in
  `reports/leaderboard-local-gemma4-smallest-two.md` before using them in a
  public-facing research report
- expand matrix coverage to `ci_forensics` and `product_workflows`
- run pass@3 / repeated-attempt consistency analysis

Runtime command recipes live in `docs/README.md`. Use
`configs/matrix/local-gemma4-two-model.json` when inspecting the completed
e4b/31B sparse matrix, and `configs/matrix/local-gemma4-smallest-two.json` for
the newer e4b/12B sparse evidence.

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

# Health check (Ollama + OpenCode + eval harness in one screen)
./check-opencode.sh              # snapshot
./check-opencode.sh --watch      # live tracker, refreshes every 5s
./check-opencode.sh --quiet      # problems only
./check-opencode.sh --integrity  # add evidence-integrity gate (slow)
```

## Progressive Disclosure

- Current docs orientation: `docs/README.md`
- Research exhibit: `publishables/README.md`
- Challenge design: `docs/challenge-design.md`
- Fresh-run harness audit: `reports/north-mini-fresh-run-harness-audit-2026-06-20.md`
- Gemma 4 local lane: `docs/local-ollama-opponents.md`
- Multi-model pipeline plan: `docs/model-comparison-eval-pipeline-plan-2026-06-20.md`
- Historical report index: `reports/REPORTS.md`
- Laguna XS.2 vs North Mini: `reports/laguna-xs2-vs-north-mini-first-comparison.md`
- Handover notes: `docs/handover-session-2026-06-21.md`
- Scenario source of truth: `ci_vibe_lab/scenarios.py`

## Public Release Rules

Sources of truth:

- Scenario contracts: `ci_vibe_lab/scenarios.py`
- Attempt evidence: `data/releases/v1/*.sqlite`
- Publication summaries: `publishables/data/*.json`
- Generated publication: `publishables/*.html`
- Pages staging: `.pages-site/`

Generated-file rules:

- Never manually edit generated catalog output.
- Never manually edit derived release CSVs or release cells.
- Regenerate through scripts and verify clean regeneration before committing.
- Never edit `.pages-site/` by hand.

Data rules:

- Never commit mutable local matrix DBs.
- Never commit raw `runs/` artifacts.
- Public evidence belongs only under `data/releases/`.
- Every release needs provenance and checksums.
- Every published number must recompute from public data.

Publication rules:

- No new claim without evidence.
- No manual metric edits.
- Preserve provider and route attribution.
- Preserve incomplete-cell denominators.
- Evaluator evidence is diagnostic, not external truth.

Security rules:

- No secrets, private provider payloads, client material, or local absolute paths.
- Review staged diffs before commits.
- Pages uses a curated generated artifact.
