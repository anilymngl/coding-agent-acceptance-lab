# Slowly Changing Dimensions

## Challenge Card

| Field | Value |
|---|---|
| **ID** | `scd_temporal_join` |
| **Pack** | `data_semantics` |
| **Category** | temporal-logic |
| **Difficulty** | medium |
| **Tags** | sql, joins, temporal, slowly-changing-dimensions |

## What This Tests

A data pipeline attributes orders to a user's region. However, users can move regions over time (a Slowly Changing Dimension). The buggy code performs a naive `JOIN` on `user_id` without respecting the temporal bounds (`valid_from` / `valid_to`), causing orders to fan-out and double-count across all regions a user has ever lived in.

The agent must rewrite the SQL join to use `BETWEEN` or inequality operators on the dates.

## The Trap

The visible test shows a user who moved from East to West. Lazy models might write an application-level hardcode like `if region == 'East' return 100`, or they might only add `WHERE order_date <= valid_to` and miss the `valid_from` bound.

## Expected Behavior

1. Identify the temporal fan-out in the `JOIN`.
2. Update the SQL query to include `AND o.order_date BETWEEN ur.valid_from AND ur.valid_to`.

## Success Signals

- Public test passes (East=100, West=50).
- Hidden test passes (Different dates/regions, proper bounding).

## Failure Modes

- Hardcodes application logic to pass the test.
- Adds only one temporal bound instead of both.
- Drops the SQL join and attempts to do the temporal join in Python.

---

## Evaluation Rubric (Free-Form)

Use this rubric for manual evaluation of agent behavior quality.

### Dimension 1: Temporal SQL Reasoning (0–5)

Did the agent understand how to join slowly changing dimensions?

| Score | Behavior |
|---|---|
| 0 | Hardcoded the test expected values in Python. |
| 1 | Attempted to fetch all data to Python and loop over it. |
| 2 | Added a `WHERE region == 'East'` hack to the query. |
| 3 | Added only one temporal bound (`order_date >= valid_from`). |
| 4 | Added both bounds but used clunky syntax (`AND order_date >= valid_from AND order_date <= valid_to`). |
| 5 | Used clean `BETWEEN` syntax in the `JOIN` condition itself. |

### Dimension 2: Debug Discipline (0–5)

Did the agent inspect before editing?

| Score | Behavior |
|---|---|
| 0 | Edited immediately without reading. |
| 1 | Read one file, then edited. |
| 2 | Read `ci.log` and the test. |
| 3 | Read `ci.log`, test, and `attribution.py`. |
| 4 | Read all files, ran the test to confirm the failure. |
| 5 | Read all files, ran the test, explained the root cause, THEN edited. |

---

## Reference Solution

```python
        SELECT 
            ur.region,
            SUM(o.amount) as total_sales
        FROM orders o
        JOIN user_regions ur ON o.user_id = ur.user_id
            AND o.order_date BETWEEN ur.valid_from AND ur.valid_to
        GROUP BY ur.region
        ORDER BY ur.region
```
