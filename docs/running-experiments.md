# Running Experiments

Use `uv` for all Python commands.

## Setup

```bash
uv venv
source .venv/bin/activate
uv sync --extra app
```

## No-Model Checks

```bash
uv run python -m unittest discover -s tests -v
uv run ci-vibe-run list
uv run ci-vibe-run list --pack maintenance_value
```

## Harness Smoke Without Model Tokens

```bash
uv run ci-vibe-run run \
  --challenge dependency_api_change \
  --no-opencode \
  --db /tmp/ci-vibe-smoke.sqlite \
  --runs-dir /tmp/ci-vibe-smoke-runs
```

Inspect the latest stored run:

```bash
uv run ci-vibe-run inspect \
  --db /tmp/ci-vibe-smoke.sqlite \
  --latest \
  --full
```

## Matrix Workflow

Validate and inspect a matrix before running it:

```bash
uv run ci-vibe-matrix validate configs/matrix/laguna-xs2-vs-north-mini.json
uv run ci-vibe-matrix plan configs/matrix/laguna-xs2-vs-north-mini.json
uv run ci-vibe-matrix status configs/matrix/laguna-xs2-vs-north-mini.json
uv run ci-vibe-matrix dbs configs/matrix/laguna-xs2-vs-north-mini.json
```

Run only when intentionally creating fresh evidence:

```bash
uv run ci-vibe-matrix run configs/matrix/laguna-xs2-vs-north-mini.json --resume
```

Do not refresh completed matrices casually. Fresh runs change evidence provenance and require a new release-data decision.

## Reports And Integrity

Generate matrix reports from configured DBs:

```bash
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/laguna-xs2-vs-north-mini.json \
  --out /tmp/leaderboard.md \
  --include-artifact-index

uv run ci-vibe-report integrity \
  --matrix configs/matrix/laguna-xs2-vs-north-mini.json \
  --out /tmp/integrity.md
```

Generated scratch reports belong outside the public tree unless they are intentionally promoted into a release.

## Public Release Verification

```bash
uv run python scripts/build_release_data.py --check
uv run python scripts/verify_release_data.py
uv run python scripts/build_scenario_catalog.py
git diff --exit-code publishables/scenario-catalog.html
uv run python scripts/verify_publishables.py
uv run python scripts/build_pages_site.py
uv run python scripts/validate_pages_site.py
```

## Dashboard

```bash
uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

## Health Check

```bash
./check-opencode.sh
./check-opencode.sh --quiet
./check-opencode.sh --watch
./check-opencode.sh --integrity
```
