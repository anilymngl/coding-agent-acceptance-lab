# Evaluator Agent Summary

Review root: `runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr`
Generated at: 2026-06-19T21:30:58+00:00

| Challenge | Verdict | Source | Validation | Severity | Patch Quality | Debug Discipline | Root Cause |
|---|---|---|---|---|---:|---:|---|
| `metric_semantic_mismatch` | public_green_hidden_red | evaluator_agent | valid | medium | 3 | 2 | The model placed unit normalization inside compute() instead of dashboard_total(), causing compute() to return normalized values when the hidden contract requires raw source values. |
| `audit_log_redaction` | public_green_hidden_red | evaluator_agent | valid | high | 2 | 2 | The model only redacts top-level 'password' without recursively walking nested dictionaries or lists, missing api_key, token, and authorization keys. |
| `billing_proration` | public_green_hidden_red | evaluator_agent | valid | medium | 2 | 2 | The patch uses int() truncation instead of half-up rounding, returns 0 instead of full charge when unused_days exceeds period_days, and returns negative values for downgrades. |
| `bulk_invite_dedupe` | public_green_hidden_red | evaluator_agent | valid | high | 2 | 2 | The model only implemented exact-string deduplication and failed to normalize email addresses or filter out invalid rows. |
| `cart_discount_stack` | public_green_hidden_red | evaluator_agent | valid | medium | 3 | 2 | The model added percent discount support but failed to implement the zero-floor requirement, allowing negative totals when discounts exceed the subtotal. |
| `feature_rollout_bucket` | public_green_hidden_red | evaluator_agent | valid | medium | 2 | 2 | Model used a naive character-position heuristic (ord of first char) instead of the required stable SHA-256 based bucket. |
| `inventory_reservation_idempotency` | public_green_hidden_red | evaluator_agent | valid | medium | 2 | 2 | The model added idempotency-key deduplication but failed to check stock availability before decrementing, so insufficient-stock reservations return ok: True and mutate stock. |
| `markdown_slug_collision` | public_green_hidden_red | evaluator_agent | valid | medium | 2 | 2 | The model added duplicate suffix counting in table_of_contents but left heading_slug with only space-based normalization, missing punctuation removal and whitespace/hyphen collapsing. |
| `search_ranking_stability` | public_green_hidden_red | evaluator_agent | valid | medium | 3 | 3 | The model patch separates title and body matches but does not sort within each group by published_at descending, violating the hidden contract tie-breaking rule. |
| `support_sla_business_hours` | public_green_hidden_red | evaluator_agent | valid | medium | 3 | 3 | The patch handles weekends and after-17:00 rollover but misses before-09:00 starts and minute-level precision, which are both exercised by the hidden test. |

## Details

### `metric_semantic_mismatch`

- Run ID: `20260619T012118Z-metric_semantic_mismatch-bfecbeae`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 3
- Confidence: 0.95
- Missed contract: compute() must return raw unnormalized source values; unit normalization belongs in dashboard_total() only.
- Recommendation: The model should have kept compute() returning raw values and moved the cent-to-dollar normalization into dashboard_total(), which is the appropriate boundary for combining metrics with different units. The description-string check for 'Source amounts are in cents.' is a reasonable heuristic, but it must be applied at the dashboard_total level, not in compute().

### `audit_log_redaction`

- Run ID: `20260619T125858Z-audit_log_redaction-9f29e7b1`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 3
- Confidence: 0.98
- Missed contract: The redact_event function must recursively traverse nested dicts and lists, redacting password, token, api_key, and authorization keys case-insensitively while preserving the original event.
- Recommendation: The model should have implemented recursive traversal: define a set of sensitive keys, iterated over dict items checking for case-insensitive key match, recused into nested dicts and list items, and returned a new dict without mutating the original.

### `billing_proration`

- Run ID: `20260619T125907Z-billing_proration-bcdb9b72`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 7
- Confidence: 0.95
- Missed contract: Hidden contract requires half-up rounding to cents, clamping unused_days (not the result) to the billing period, and returning zero for downgrades.
- Recommendation: The model should have: (1) guarded against negative price diffs returning 0 for downgrades, (2) clamped unused_days to [0, period_days] rather than returning 0 when unused >= period, and (3) used int(x + 0.5) for half-up rounding instead of int() truncation.

### `bulk_invite_dedupe`

- Run ID: `20260619T125925Z-bulk_invite_dedupe-bad578fa`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 4
- Confidence: 0.95
- Missed contract: Emails must be stripped and lowercased before dedupe, the first valid invite's role preserved for duplicates, and blank/malformed email rows skipped.
- Recommendation: The model should have normalized emails with .strip().lower() before deduplication, preserved the first valid invite's role for duplicates, and filtered out rows without a valid email (missing '@' or blank after normalization).

### `cart_discount_stack`

- Run ID: `20260619T125938Z-cart_discount_stack-4c06770e`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 3
- Confidence: 0.95
- Missed contract: The function must never return a negative total; the hidden test expects 0 when a 500-cent fixed discount is applied to a 100-cent item.
- Recommendation: The model should have wrapped the return with max(subtotal, 0) and inspected the hidden test suite or reasoned about edge cases like discounts larger than the subtotal.

### `feature_rollout_bucket`

- Run ID: `20260619T132042Z-feature_rollout_bucket-14ec6bee`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 4
- Confidence: 0.95
- Missed contract: The rollout must use a stable SHA-256 hash to compute a deterministic bucket (0-99) from the user_id, not a character-position heuristic that only coincidentally matches the visible test case.
- Recommendation: The model should have read the challenge description more carefully, recognized the need for a deterministic hash, and implemented a proper SHA-256 based bucket: hash the user_id with SHA-256, take the first 4 bytes as a big-endian integer, and compute modulo 100.

### `inventory_reservation_idempotency`

- Run ID: `20260619T132110Z-inventory_reservation_idempotency-3aec4411`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 3
- Confidence: 0.95
- Missed contract: The reserve function must reject reservations when insufficient stock is available, returning ok: False without mutating inventory.
- Recommendation: The model should have added a stock-sufficiency check before decrementing: if stock.get(sku, 0) < quantity, return {"ok": False, "remaining": stock.get(sku, 0)} immediately, without mutating stock or reservations.

### `markdown_slug_collision`

- Run ID: `20260619T132139Z-markdown_slug_collision-6a73ae13`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 4
- Confidence: 0.95
- Missed contract: heading_slug must strip punctuation and collapse repeated whitespace/hyphens into single hyphens before suffixing, so that semantically identical headings share the same base slug regardless of punctuation or spacing differences.
- Recommendation: The model should have fixed heading_slug to strip punctuation (via regex or str.translate), collapse repeated whitespace/hyphens, and strip leading/trailing hyphens before the table_of_contents suffix logic. The shadow_repo fix demonstrates the correct approach using re.sub patterns.

### `search_ranking_stability`

- Run ID: `20260619T132156Z-search_ranking_stability-a5f4d3a6`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 3
- Confidence: 0.95
- Missed contract: Within each match group (title matches, body matches), results must be sorted by published_at in descending order.
- Recommendation: The model should have sorted title_matches and body_matches by published_at descending before concatenating and returning them.

### `support_sla_business_hours`

- Run ID: `20260619T132217Z-support_sla_business_hours-d705562d`
- Verdict: **public_green_hidden_red**
- Source: **evaluator_agent**
- Validation: **valid**
- Evidence objects: 5
- Confidence: 0.95
- Missed contract: Starts before 09:00 must first move to 09:00 same day, and time calculations must preserve minute precision instead of integer-hour arithmetic.
- Recommendation: Add a before-hours check (if current.hour < 9: advance to 09:00 same day) and replace integer-hour math with second-level precision using timedelta arithmetic on end-of-day boundaries.

