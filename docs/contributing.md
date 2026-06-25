# Contributing

## Branches

- `main`: current supported code, configs, frozen public datasets, canonical publication, current documentation, always releasable.
- `develop`: integrated next-release work; may contain unfinished code but must pass CI.
- `feature/*`: temporary implementation branches from `develop`; merge back to `develop`; delete after merge.
- Hotfix flow: `main -> hotfix/* -> main -> develop`.

Do not use `develop` as a junk drawer. Runtime databases, raw worktrees, session notes, and scratch reports remain ignored or local unless intentionally promoted into a release.

## Pull Requests

PRs should state:

- what changed
- why it changed
- which evidence or behavior is affected
- which verification commands passed

Use normal merge commits for release-history PRs when the commit sequence is meaningful.

## Evidence Rules

- Do not expose hidden tests to the model-under-test path before the agent exits.
- Do not weaken hidden tests to improve scores.
- Do not count provider/config/no-output failures as semantic model failures.
- Do not merge sparse and contract-visible lanes by default.
- Do not present partial matrix results as a public benchmark leaderboard.

## Data Rules

- Keep mutable run state out of Git: `data/matrix/`, `runs/`, raw provider streams, generated worktrees.
- Public evidence belongs under `data/releases/` with schema, provenance, checksums, and verifiers.
- SQLite is the release query layer; CSVs are exported parity artifacts.

## Required Checks

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

For ordinary code-only changes, run the smallest relevant subset plus unit tests. For release, publication, or data changes, run the full set.
