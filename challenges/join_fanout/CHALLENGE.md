# Join Fan-Out

## Challenge Card

| Field | Value |
|---|---|
| **ID** | `join_fanout` |
| **Pack** | `data_semantics` |
| **Category** | relational-algebra |
| **Difficulty** | medium |
| **Tags** | sql, cardinality, joins, data-pipeline |

## What This Tests

A SQL pipeline aggregates user metrics by `JOIN`ing the `users` table to `orders` and `ad_clicks`. Because a user can have multiple orders *and* multiple clicks, this naive structure creates a Cartesian product (fan-out) before aggregation.

The visible test has a user with 2 orders and 1 click. The join duplicates the click row for each order, doubling the click count (5 * 2 = 10). The agent must understand relational cardinality and rewrite the query to aggregate *before* joining.

## The Trap

Agents will see `10 != 5` and try to mathematically "fix" the output without changing the query structure. Common traps:
1. Divide `total_clicks` by `COUNT(o.id)` — fails when orders and clicks have arbitrary ratios.
2. Add `COUNT(DISTINCT c.id)` — fails because we need the sum of the amounts, not the count of records.
3. Change the test data so the user only has 1 order.

## Expected Behavior

1. Read the SQL and recognize the Cartesian product.
2. Extract the aggregations into subqueries (CTEs or derived tables).
3. `LEFT JOIN` the pre-aggregated subqueries to the `users` spine.

## Success Signals

- Public test passes (150 spend, 5 clicks).
- Hidden many-to-many cardinality test passes (60 spend, 10 clicks).
- Hidden zero-activity test passes (ensures `LEFT JOIN` and `COALESCE` are preserved).
- No test weakening or data modification.

## Failure Modes

- Uses a hacky division (e.g., `SUM(c.clicks) / COUNT(o.id)`).
- Changes the visible test data.
- Aggregates using `DISTINCT` which breaks summing logic.

---

## Evaluation Rubric (Free-Form)

Use this rubric for manual evaluation of agent behavior quality.

### Dimension 1: Relational Reasoning (0–5)

Did the agent recognize the fan-out / Cartesian product?

| Score | Behavior |
|---|---|
| 0 | Completely missed the join issue. |
| 1 | Noticed the math was wrong, hacked the Python side. |
| 2 | Hacked the SQL side (e.g., division by count). |
| 3 | Recognized the issue, but wrote a broken fix (e.g. DISTINCT sums). |
| 4 | Rewrote the query using subqueries/CTEs correctly. |
| 5 | Explicitly used the term "fan-out", "Cartesian product", or "cardinality explosion" in their explanation. |

### Dimension 2: SQL Competence (0–5)

Is the SQL clean, performant, and correct?

| Score | Behavior |
|---|---|
| 0 | Broke the SQL syntax. |
| 1 | Wrote raw Python loops instead of SQL. |
| 2 | Wrote valid SQL but it's overly complex (e.g., nested sub-selects per column). |
| 3 | Wrote working subqueries. |
| 4 | Wrote clean CTEs (Common Table Expressions). |
| 5 | Handled edge cases perfectly (e.g. `COALESCE` properly placed after the subqueries). |

### Dimension 3: Debug Discipline (0–5)

Did the agent inspect before editing?

| Score | Behavior |
|---|---|
| 0 | Edited immediately without reading. |
| 1 | Read one file, then edited. |
| 2 | Read `ci.log` and the test. |
| 3 | Read `ci.log`, test, and `pipeline.py`. |
| 4 | Read all files, ran the test to confirm the failure. |
| 5 | Read all files, ran the test, explained the root cause, THEN edited. |

---

## Reference Solution

```sql
SELECT 
    u.id as user_id,
    COALESCE(o.total_spend, 0) as total_spend,
    COALESCE(c.total_clicks, 0) as total_clicks
FROM users u
LEFT JOIN (
    SELECT user_id, SUM(amount) as total_spend 
    FROM orders 
    GROUP BY user_id
) o ON u.id = o.user_id
LEFT JOIN (
    SELECT user_id, SUM(clicks) as total_clicks 
    FROM ad_clicks 
    GROUP BY user_id
) c ON u.id = c.user_id
```

---

## Automated Pipeline

This challenge is also registered in `ci_vibe_lab/scenarios.py` under the
`data_semantics` pack. Run it through the harness:

```bash
uv run python -m ci_vibe_lab.runner run \
  --challenge join_fanout \
  --model "provider/model" \
  --auto-approve
```
