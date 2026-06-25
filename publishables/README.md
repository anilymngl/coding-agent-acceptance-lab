# Publishables

Canonical HTML source for the public research site.

The supported public site contains exactly six HTML pages:

| File | Role |
|---|---|
| `index.html` | Entry point, thesis, and navigation |
| `paper.html` | Canonical technical report |
| `harness-built-target.html` | Harness inventory and system flow |
| `scenario-catalog.html` | Inspectable scenario catalog |
| `evidence-index.html` | Study B evidence matrix |
| `evaluator-findings.html` | Reviewed false-green diagnostics |

Machine-readable publication summaries live in `data/`.

## Build And Verify

Regenerate the scenario catalog before release checks:

```bash
uv run python scripts/build_scenario_catalog.py
git diff --exit-code publishables/scenario-catalog.html
```

Verify publication consistency:

```bash
uv run python scripts/verify_publishables.py
```

Build the curated Pages artifact:

```bash
uv run python scripts/build_pages_site.py
uv run python scripts/validate_pages_site.py
```

Do not edit `.pages-site/` by hand.

## Data Boundary

The empirical source is `data/releases/v1/`. The JSON files in `publishables/data/` are publication summaries and must match the release data.
