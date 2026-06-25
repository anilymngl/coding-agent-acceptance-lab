# Documentation Index

Start here when modifying the repository.

## Current Docs

| Document | Purpose |
|---|---|
| [architecture.md](architecture.md) | Harness components, data flow, and ownership boundaries |
| [methodology.md](methodology.md) | Public/hidden acceptance methodology and interpretation rules |
| [challenge-design.md](challenge-design.md) | Scenario design principles and challenge anatomy |
| [running-experiments.md](running-experiments.md) | Local command recipes for smoke runs, matrix runs, reports, and Pages staging |
| [data-dictionary.md](data-dictionary.md) | Public release database and CSV field meanings |
| [public-release-model.md](public-release-model.md) | Data boundaries, branches, and publication layers |
| [contributing.md](contributing.md) | Branch policy, PR expectations, and development rules |
| [repository-map.md](repository-map.md) | Retained and removed public-tree path rationale |

## Canonical Sources

- Scenario definitions: `ci_vibe_lab/scenarios.py`
- Release data: `data/releases/v1/`
- Publication source: `publishables/`
- Curated Pages build: `.pages-site/`
- Release audit: `reports/final-public-release-audit.md`

## Quick Verification

```bash
uv run python scripts/verify_release_data.py
uv run python scripts/verify_publishables.py
uv run python scripts/build_pages_site.py
uv run python scripts/validate_pages_site.py
uv run python -m unittest discover -s tests -v
```
