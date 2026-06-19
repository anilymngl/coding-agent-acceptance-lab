# North Mini Code OpenCode Vibe Eval

Date: 2026-06-19  
Harness: OpenCode CLI via `ci_vibe_lab.runner`  
Model: `opencode/north-mini-code-free`  
Agent: `build`  
Run database: `data/north-mini-code-eval.sqlite`  
Run artifacts: `runs/north-mini-code-eval/`

## Executive Read

North Mini Code did the visible coding-agent workflow well: it inspected files,
ran tests, edited narrowly, and reran tests. It got **10/10 public tests green**.

The hidden acceptance layer changed the picture: **6/10 hidden tests passed**.
The failures were not random syntax errors. They were mostly **contract-depth
failures**: the model fixed the immediate symptom while missing the fuller domain
contract behind the task.

This is exactly why this eval shape is useful. Public tests measure whether the
agent can get CI green. Hidden tests reveal whether the patch is trustworthy.

## Method

I expanded the `ci_forensics` challenge pack to 10 deterministic generated repos.
Each challenge starts red, then the runner:

1. creates a fresh git repo for the challenge
2. runs the visible unittest suite to confirm baseline failure
3. invokes OpenCode with the same prompt shape
4. captures stdout/stderr, patch, duration, and final public test output
5. injects hidden acceptance tests
6. reruns the full suite
7. stores results in SQLite and artifacts on disk

Command used:

```bash
uv run python -m ci_vibe_lab.runner run \
  --challenge all \
  --model opencode/north-mini-code-free \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --db data/north-mini-code-eval.sqlite \
  --runs-dir runs/north-mini-code-eval
```

Verification command for the harness:

```bash
uv run python -m unittest discover -s tests -v
```

## Scorecard

| Metric | Result |
|---|---:|
| Challenges run | 10 |
| Baseline red checks | 10/10 |
| OpenCode exit code 0 | 10/10 |
| Public tests passed | 10/10 |
| Hidden acceptance passed | 6/10 |
| Total runtime | 183.8s |
| Average runtime | 18.4s |
| Median runtime | 17.7s |
| Average patch size | 468 chars |

## Challenge Results

| Challenge | Category | Public | Hidden | What Happened |
|---|---|---:|---:|---|
| `async_export_race` | race-condition | pass | pass | Made the background writer deterministic by joining the thread. |
| `csv_header_contract` | data-contract | pass | fail | Used declared columns but missed empty-export header and extra-field filtering. |
| `decimal_money_rounding` | money | pass | fail | Switched to `Decimal` but still truncated cents instead of half-up rounding. |
| `dependency_api_change` | dependency-boundary | pass | fail | Checked `ok`, but kept returning legacy hardcoded `charge_id`. |
| `env_bool_parser` | configuration | pass | fail | Handled common false strings but missed empty string / whitespace normalization. |
| `idempotency_key_regression` | idempotency | pass | pass | Correctly made the key deterministic over order, user, and attempt. |
| `pagination_cursor_drift` | pagination | pass | pass | Correctly followed `next_cursor` until `None`. |
| `stale_generated_schema` | generated-artifact | pass | pass | Regenerated/updated schema to include the missing field. |
| `tenant_cache_leak` | isolation | pass | pass | Correctly changed cache key to `(tenant_id, user_id)`. |
| `timezone_ci_only` | environment-drift | pass | pass | Correctly used `zoneinfo.ZoneInfo(account_timezone)`. |

## Failure Analysis

### 1. `csv_header_contract`

Patch:

```diff
-    columns = sorted(rows[0].keys())
+    columns = EXPORT_COLUMNS
```

This was directionally right. The model identified the declared export contract.
But it did not reason through the full contract:

- empty exports should still emit the documented header
- rows may contain internal fields that must not be exported

Hidden failure:

- `export_csv([])` returned `""`
- `csv.DictWriter` raised on `internal_note`

Interpretation: good local diagnosis, incomplete data-contract reasoning.

### 2. `decimal_money_rounding`

Patch:

```diff
+from decimal import Decimal
...
-    total = 0.0
+    total = Decimal("0")
...
-        total += float(line["unit_price"]) * int(line["quantity"])
+        total += Decimal(line["unit_price"]) * int(line["quantity"])
     return int(total * 100)
```

This shows useful domain knowledge: it knew floats were wrong for money. But it
stopped one step early. `int(total * 100)` still truncates. Hidden acceptance
expected half-up cent rounding.

Interpretation: recognizes the right tool, but misses the policy boundary.

### 3. `dependency_api_change`

Patch:

```diff
-    if result is not True:
+    if not result.get("ok"):
         raise PaymentError(...)
```

This fixed the visible failure. It also handled failed gateway responses. But it
did not propagate the new `id` field:

```text
expected charge_id: ch_inv_101_2500
actual charge_id: legacy-charge
```

Interpretation: solved the guard condition, missed downstream data semantics.

### 4. `env_bool_parser`

Patch:

```diff
+    value = source.get(name, "")
+    if isinstance(value, str):
+        return value.lower() not in ("false", "0", "no", "off")
+    return bool(value)
```

This handled the visible `false` case and several common false values. It failed
on the hidden empty-string and whitespace cases.

Interpretation: practical but shallow normalization. This is a classic place
where agents pass public tests while leaving production footguns.

## Success Analysis

### Strong Simple Fixes

`idempotency_key_regression`, `pagination_cursor_drift`, and `timezone_ci_only`
were clean wins. The patches were small and matched the intended contract:

- idempotency key includes all identity components
- pagination follows the renamed cursor
- timezone conversion uses the account timezone explicitly

These are the model's best-looking runs because the bug and fix were local, and
the correct contract was visible in nearby source/tests.

### Better-Than-Expected Workflow Fixes

`tenant_cache_leak` passed hidden acceptance and took the longest run
at 29.5s. It still found the right fix: composite cache keys. This suggests the
model can handle small security/isolation bugs when the fixture exposes the
boundary clearly.

`stale_generated_schema` passed hidden acceptance. The trace showed it inspected
the generator and source fields, then produced the right checked-in artifact.
That is a good sign for generated-file workflows.

### Acceptable But Not Elegant

`async_export_race` passed hidden acceptance by starting the thread and then
joining it immediately. That satisfies the function contract, but it leaves a
pointless thread and sleep in production code. A stronger engineer would remove
the background thread entirely and write synchronously.

Interpretation: correct behavior, mediocre taste.

## Tool Discipline

Across all 10 runs, the model:

- ran the visible unittest suite before editing
- made one focused source edit or generated artifact update
- reran the visible unittest suite after editing
- exited cleanly

Approximate tool-use profile:

| Challenge | Test Runs in Trace | Reads | Edits | Bash Calls |
|---|---:|---:|---:|---:|
| `async_export_race` | 2 | 4 | 1 | 8 |
| `csv_header_contract` | 2 | 2 | 1 | 2 |
| `decimal_money_rounding` | 2 | 3 | 1 | 9 |
| `dependency_api_change` | 2 | 4 | 1 | 3 |
| `env_bool_parser` | 2 | 4 | 1 | 2 |
| `idempotency_key_regression` | 2 | 2 | 1 | 2 |
| `pagination_cursor_drift` | 2 | 4 | 1 | 4 |
| `stale_generated_schema` | 2 | 7 | 0 | 6 |
| `tenant_cache_leak` | 2 | 8 | 2 | 10 |
| `timezone_ci_only` | 2 | 4 | 1 | 5 |

The workflow pattern is healthy. The main weakness is not lack of tool use; it
is insufficient contract expansion beyond the public failure.

## What This Reveals About North Mini Code Here

Facts from this run:

- It can reliably repair visible small Python CI failures.
- It uses OpenCode tools coherently enough for a local coding-agent workflow.
- It tends to produce compact patches.
- It often stops once public tests pass.
- Hidden acceptance catches meaningful misses.

Recommendation:

Use this model for cheap first-pass CI repair, small local bug fixes, and
generated-artifact chores. Do not treat a green public test run as enough.
Require hidden tests, broader acceptance checks, or human review for:

- money/math policy
- data export contracts
- dependency response semantics
- configuration parsing
- safety/isolation boundaries

My practical trust level from this 10-case run:

- **Good:** fast local diagnosis, small patches, visible test repair.
- **Mixed:** contract depth and edge-case completeness.
- **Weak:** knowing when a visible test is only one example of a broader domain rule.

## Eval Framework Takeaway

This eval pack is doing the right thing. It is not a benchmark leaderboard. It is
a behavior microscope.

The strongest signal is the gap between:

```text
public pass: 10/10
hidden pass: 6/10
```

That gap is the product. It tells us how often the model can make CI green while
still missing the actual engineering contract.

Next improvements:

1. Run each challenge 3 times to measure variance.
2. Add patch-quality scoring in the dashboard/report.
3. Add a second model baseline for comparison.
4. Add a "taste" hidden review category for patches like `async_export_race`.
5. Split challenges into packs: `ci_forensics`, `product_feature`, `refactor_relay`, and `frontend_taste`.

