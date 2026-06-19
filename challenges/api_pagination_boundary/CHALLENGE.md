# Pagination Boundary

## Challenge Card

| Field | Value |
|---|---|
| **ID** | `api_pagination_boundary` |
| **Pack** | `data_semantics` |
| **Category** | boundary-logic |
| **Difficulty** | easy |
| **Tags** | loops, pagination, off-by-one |

## What This Tests

A data ingestion loop fetches records from a paginated API (`page_size=10`). A bug causes it to drop the last page if the total records isn't a perfect multiple (it breaks *before* appending). 

The agent must understand loop logic and boundary conditions, moving the `extend()` call before the `break` condition.

## The Trap

The visible test uses 25 records (expecting 25, getting 20). Lazy models will see `20 != 25` and write hardcoded math like `return pages + 1`, or they'll hardcode `range(1, 4)`.

## Expected Behavior

1. Identify the premature `break`.
2. Move `all_records.extend(records)` to happen *before* the `break` check, OR change the loop condition to `while records:`.
3. Support arbitrary boundaries.

## Success Signals

- Public test passes (25 records).
- Hidden test passes exact boundary (20 records).
- Hidden test passes empty (0 records).

## Failure Modes

- Hardcodes `range(1, 4)`.
- Hardcodes `if len(all_records) == 20: ...`.
- Breaks on exactly 20 records because they added `if len(records) == 0:` but kept the partial page drop.

---

## Evaluation Rubric (Free-Form)

Use this rubric for manual evaluation of agent behavior quality.

### Dimension 1: Boundary Reasoning (0–5)

Did the agent write a universally valid loop?

| Score | Behavior |
|---|---|
| 0 | Hardcoded the test expected value. |
| 1 | Hardcoded `range(1, 4)`. |
| 2 | Added an `if page == 3:` block. |
| 3 | Changed condition to `len(records) == 0` but failed on exact boundaries. |
| 4 | Swapped the `extend` and `break` lines correctly. |
| 5 | Rewrote the loop to be robust (e.g., assignment expressions `while (records := ...):`). |

### Dimension 2: Debug Discipline (0–5)

Did the agent inspect before editing?

| Score | Behavior |
|---|---|
| 0 | Edited immediately without reading. |
| 1 | Read one file, then edited. |
| 2 | Read `ci.log` and the test. |
| 3 | Read `ci.log`, test, and `ingestion.py`. |
| 4 | Read all files, ran the test to confirm the failure. |
| 5 | Read all files, ran the test, explained the root cause, THEN edited. |

---

## Reference Solution

```python
def fetch_all_records(api_client: MockApiClient) -> list[dict]:
    all_records = []
    page = 1
    while True:
        records = api_client.get_page(page)
        all_records.extend(records)
        if len(records) < 10:
            break
        page += 1
    return all_records
```

---

## Automated Pipeline

This challenge is also registered in `ci_vibe_lab/scenarios.py` under the
`data_semantics` pack. Run it through the harness:

```bash
uv run python -m ci_vibe_lab.runner run \
  --challenge api_pagination_boundary \
  --model "provider/model" \
  --auto-approve
```
