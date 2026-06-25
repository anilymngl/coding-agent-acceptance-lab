# Data Dictionary

Public release data lives under `data/releases/v1/`.

## Files

| Path | Description |
|---|---|
| `study-a.sqlite` | Breadth study release database |
| `study-b.sqlite` | Canonical 391-retained-attempt depth study database |
| `evaluator-reviews.sqlite` | Structured evaluator review diagnostics |
| `supporting-gemma.sqlite` | Separate supporting local Gemma evidence |
| `exports/*.csv` | CSV exports of release tables |
| `schema.sql` | Release database schema |
| `provenance.json` | Source, boundary, route, and release metadata |
| `checksums.sha256` | File-level SHA256 checksums |

## Common Attempt Fields

| Field | Meaning |
|---|---|
| `attempt_id` | Stable attempt identifier |
| `scenario_id` | Scenario key from `ci_vibe_lab/scenarios.py` |
| `pack` | Scenario pack, such as `ci_forensics` or `product_workflows` |
| `system_id` | System row label used for analysis |
| `model` | Model identifier |
| `provider` | Provider or gateway name |
| `route` | Route used for this attempt |
| `prompt_lane` | `sparse`, `contract_visible`, or `audit_visible` |
| `attempt_index` | Attempt number within a planned cell |
| `planned` | Whether the attempt was planned |
| `retained` | Whether the attempt is included in semantic analysis |
| `exclusion_reason` | Reason an attempt is excluded, if any |
| `public_pass` | Visible test result |
| `hidden_pass` | Hidden acceptance result |
| `false_green` | `1` when public passed and hidden failed |
| `duration_seconds` | Run duration |
| `patch_sha256` | Hash of captured patch content |
| `source_id` | Source database group |
| `started_at` | Attempt start timestamp |

## Cell Fields

| Field | Meaning |
|---|---|
| `planned_attempts` | Planned attempts for the scenario/system/lane cell |
| `retained_attempts` | Attempts retained after operational exclusions |
| `public_passes` | Retained attempts where visible tests passed |
| `hidden_passes` | Retained attempts where hidden tests passed |
| `false_greens` | Retained public-green / hidden-red attempts |
| `any_hidden_pass` | Whether at least one retained attempt passed hidden tests |
| `all_retained_hidden_pass` | Whether all retained attempts passed hidden tests |
| `cell_status` | Complete, partial, or audited status marker |

## Recompute Contract

Every central published number must recompute from release data:

```bash
uv run python scripts/verify_release_data.py
```

The verifier checks SQLite integrity, CSV parity, publication JSON parity, and publication HTML parity.
