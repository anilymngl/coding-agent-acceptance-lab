# Public Research Data Release v1

This directory contains deterministic, sanitized release data for the coding-agent acceptance study.

Operational databases under `data/matrix/` and raw run artifacts under `runs/` remain private mutable execution state. This release directory is the public recomputation layer.

Run:

```bash
uv run python scripts/verify_release_data.py
```

The verifier recomputes the published Study B metrics from `study-b.sqlite`, checks CSV parity, and compares the release data to the publication JSON/HTML.

Licensing: code is MIT; public research data and documentation are CC BY 4.0 unless otherwise stated.
