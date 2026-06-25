# AGENTS.md

## Purpose

This repository is a coding-agent acceptance harness. The core question is:

> Did the agent actually fix the problem, or did it only make visible CI green?

Each scenario has public tests visible to the model and hidden acceptance tests injected after the model exits. `public_pass=1` and `hidden_pass=0` is a **false-green**. The main metric is the **trust gap**: public pass rate minus hidden pass rate.

This is a behavior microscope, not a public leaderboard. Preserve evidence quality, caveats, and denominators when comparing models.

## Architecture Boundaries

- `ci_vibe_lab/scenarios.py` is the scenario source of truth.
- `ci_vibe_lab/runner.py` owns the single-run lifecycle: write scenario, baseline, agent, public tests, patch capture, hidden tests, persistence.
- `ci_vibe_lab/matrix.py` owns matrix expansion and orchestration.
- `ci_vibe_lab/evaluator.py` owns evaluator workbench generation and review schema validation.
- `data/releases/v1/` is the public reproducibility layer.
- `publishables/` is the canonical publication source.
- `.pages-site/` is a generated deployment artifact and is ignored.

## Sources Of Truth

- Scenario contracts and hidden tests: `ci_vibe_lab/scenarios.py`
- Matrix definitions: `configs/matrix/*.json`
- Public empirical data: `data/releases/v1/*.sqlite`
- Release schema and provenance: `data/releases/v1/schema.sql`, `data/releases/v1/provenance.json`
- Publication summaries: `publishables/data/*.json`
- Publication pages: six canonical HTML pages under `publishables/`
- Repository structure rationale: `docs/repository-map.md`

## Branch Policy

- `main`: current supported code, configs, frozen public datasets, canonical publication, current docs, always releasable.
- `develop`: integrated next-release work; must still pass CI; no runtime databases, raw worktrees, session handovers, or generated reports unless intended for the next release.
- `feature/*`: temporary branches from `develop`; merge back to `develop`; delete after merge.
- Hotfix flow: `main -> hotfix/* -> main -> develop`.
- Keep `main` as the GitHub default branch.

## Generated-File Rules

- Never manually edit `publishables/scenario-catalog.html`; regenerate with `uv run python scripts/build_scenario_catalog.py`.
- Never manually edit release CSVs, release cells, or derived publication JSON to change metrics.
- Never manually edit `.pages-site/`; build it with `uv run python scripts/build_pages_site.py`.
- If generated output changes, run the matching verifier before committing.

## Data Rules

- Do not commit mutable local matrix DBs under `data/matrix/`.
- Do not commit raw `runs/` artifacts, provider streams, generated worktrees, prompts, or stdout/stderr captures.
- Public evidence belongs under `data/releases/` with schema, provenance, checksums, and verification.
- Do not count provider/config/no-output failures as semantic model failures.
- Do not count no-output timeouts as false-greens.
- Do not merge sparse and contract-visible lanes by default.

## Security Rules

- No secrets, private provider payloads, local absolute paths, or client material.
- Run `gitleaks git . --redact` before release-sensitive PRs.
- Review staged diffs before committing.
- GitHub Pages must deploy only the curated `.pages-site` artifact.

## Required Commands

```bash
uv run python scripts/build_release_data.py --check
uv run python scripts/verify_release_data.py
uv run python scripts/build_scenario_catalog.py
git diff --exit-code publishables/scenario-catalog.html
uv run python scripts/verify_publishables.py
uv run python scripts/build_pages_site.py
uv run python scripts/validate_pages_site.py
uv run python -m unittest discover -s tests -v
gitleaks git . --redact
```

Use `uv` / `uv run` for project Python commands.

## Definition Of Done

- Public tests and hidden-test methodology are not weakened.
- Central published numbers recompute from `data/releases/v1/`.
- Publication JSON and HTML match release data.
- Scenario catalog regenerates cleanly.
- Pages artifact validates.
- Unit tests pass.
- Security scan passes.
- Documentation describes the current supported system, not session history.
