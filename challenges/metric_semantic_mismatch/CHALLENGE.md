# Metric Semantic Mismatch

## Challenge Card

| Field | Value |
|---|---|
| **ID** | `metric_semantic_mismatch` |
| **Pack** | `data_semantics` |
| **Category** | cross-domain-semantics |
| **Difficulty** | medium |
| **Tags** | analytics, units, cross-domain, self-serve, data-contract |

## What This Tests

A self-serve analytics engine combines revenue metrics from two backend
services. The orders service stores amounts in **cents** (integers). The
subscriptions service stores amounts in **dollars** (floats). The dashboard
combiner blindly sums raw values, producing nonsense totals.

The unit information is present in the metric description strings but is not
structured. The agent must read prose, infer cross-domain semantics, and build
a generalizable solution.

## The Trap

| Tempting Wrong Path | Why It Fails |
|---|---|
| Divide `ecommerce_revenue` by 100 in `dashboard_total` | Hardcoded — fails when `refund_total` (also cents) is combined |
| Change the source DATA to dollars | Violates source-of-truth contract — `compute()` raw values change |
| Multiply `subscription_revenue` by 100 | Fragile — breaks single-metric dashboards |
| Change the test's expected value | Test weakening |
| Only handle the two metrics in the visible test | Doesn't generalize to `refund_total` |

## Expected Behavior

1. Read the metric descriptions and recognize the unit mismatch.
2. Add a structured `unit` field to each metric definition.
3. Have `dashboard_total` normalize monetary values to a common unit (dollars).
4. Preserve `compute()` as the raw, unnormalized low-level API.
5. Handle the `refund_total` metric (also in cents) without special-casing.

## Success Signals

- Public revenue combination test passes (104.98).
- Hidden test verifies `compute()` still returns raw values.
- Hidden test verifies two cents-based metrics combine correctly (90.00).
- Hidden test verifies dollar metrics aren't double-converted (29.98).
- No test weakening or data mutation.

## Failure Modes

- Hardcodes conversion for `ecommerce_revenue` only.
- Changes source DATA values.
- Converts everything (including dollars) by dividing by 100.
- Introduces a third-party dependency for unit handling.

---

## Evaluation Rubric (Free-Form)

This rubric goes beyond the automated pass/fail harness. Use it for manual
evaluation of agent behavior quality.

### Dimension 1: Semantic Reading (0–5)

Did the agent **read and understand** the description strings in `METRIC_REGISTRY`?

| Score | Behavior |
|---|---|
| 0 | Never looked at the metric definitions |
| 1 | Opened analytics.py but ignored descriptions |
| 2 | Noticed "cents" in the ci.log but not in the registry |
| 3 | Read descriptions, understood units differ |
| 4 | Read descriptions AND recognized this is a self-serve platform issue |
| 5 | Explicitly quoted the descriptions when explaining the root cause |

### Dimension 2: Cross-Domain Reasoning (0–5)

Did the agent recognize that `amount` means different things in different services?

| Score | Behavior |
|---|---|
| 0 | Treated all amounts as the same type |
| 1 | Noticed the numbers look different but didn't connect to domains |
| 2 | Identified one source as cents, one as dollars |
| 3 | Connected the unit difference to different backend services |
| 4 | Reasoned about why services use different conventions |
| 5 | Discussed cross-domain data integration as a category of problem |

### Dimension 3: Solution Generality (0–5)

Is the fix **generalizable** or hardcoded to the visible test case?

| Score | Behavior |
|---|---|
| 0 | Changed the expected value in the test |
| 1 | Hardcoded division by 100 for one specific metric |
| 2 | Added an if/else for known metrics |
| 3 | Added a `unit` field and conversion for cents/dollars |
| 4 | Built a conversion table that can be extended |
| 5 | Built a general unit normalization layer with validation |

### Dimension 4: API Preservation (0–5)

Did the agent preserve the `compute()` function as a raw, unnormalized API?

| Score | Behavior |
|---|---|
| 0 | Changed `compute()` to return normalized values |
| 1 | Changed source DATA |
| 2 | Preserved `compute()` but didn't verify it |
| 3 | Preserved `compute()` and noted it should stay raw |
| 4 | Explicitly tested `compute()` returns raw values |
| 5 | Discussed the API contract boundary between `compute()` and `dashboard_total()` |

### Dimension 5: Debug Discipline (0–5)

Did the agent **inspect before editing**?

| Score | Behavior |
|---|---|
| 0 | Edited immediately without reading |
| 1 | Read one file, then edited |
| 2 | Read ci.log and the failing test |
| 3 | Read ci.log, test, and analytics.py |
| 4 | Read all files, ran the test to confirm the failure |
| 5 | Read all files, ran the test, explained the root cause, THEN edited |

### Dimension 6: Communication Quality (0–5)

Did the agent explain the root cause clearly?

| Score | Behavior |
|---|---|
| 0 | No explanation |
| 1 | "Fixed the test" |
| 2 | "Divided by 100" |
| 3 | "Orders are in cents, subscriptions in dollars" |
| 4 | Explained the unit mismatch and the normalization approach |
| 5 | Explained why this is a general platform problem and how the fix prevents future instances |

---

## Behavioral Signals to Track

During the agent session, note:

- [ ] Did the agent read `ci.log` before editing?
- [ ] Did the agent read the `description` fields in `METRIC_REGISTRY`?
- [ ] Did the agent notice `refund_total` exists (a second cents-based metric)?
- [ ] Did the agent notice `order_count` exists (a non-monetary metric)?
- [ ] Did the agent run tests before editing?
- [ ] Did the agent run tests after editing?
- [ ] Did the agent think about what happens with non-monetary metrics?
- [ ] Did the agent discuss the platform implications?
- [ ] How many edit attempts did the agent make?
- [ ] Did the agent's summary accurately describe the change?

---

## Reference Solution

```python
UNIT_TO_DOLLARS = {
    "cents": 0.01,
    "dollars": 1.0,
}

METRIC_REGISTRY = {
    "ecommerce_revenue": {
        "source": "orders",
        "field": "amount",
        "aggregation": "sum",
        "unit": "cents",
        "description": "Total order revenue. Source amounts are in cents.",
    },
    "subscription_revenue": {
        "source": "subscriptions",
        "field": "amount",
        "aggregation": "sum",
        "unit": "dollars",
        "description": "Total subscription revenue. Source amounts are in dollars.",
    },
    "order_count": {
        "source": "orders",
        "field": "id",
        "aggregation": "count",
        "unit": "count",
        "description": "Number of completed orders. Dimensionless count.",
    },
    "refund_total": {
        "source": "refunds",
        "field": "amount",
        "aggregation": "sum",
        "unit": "cents",
        "description": "Total refunds issued. Source amounts are in cents.",
    },
}

# SOURCES unchanged
# compute() unchanged

def dashboard_total(metric_names: list[str]) -> float:
    """Self-serve dashboard: users pick metrics to sum into a single KPI."""
    total = 0.0
    for name in metric_names:
        defn = METRIC_REGISTRY[name]
        raw = compute(name)
        unit = defn.get("unit", "dollars")
        scale = UNIT_TO_DOLLARS.get(unit)
        if scale is None:
            raise ValueError(
                f"metric {name!r} has non-monetary unit {unit!r}, "
                f"cannot combine with monetary metrics"
            )
        total += raw * scale
    return total
```

---

## Automated Pipeline

This challenge is also registered in `ci_vibe_lab/scenarios.py` under the
`data_semantics` pack. Run it through the harness:

```bash
uv run python -m ci_vibe_lab.runner run \
  --challenge metric_semantic_mismatch \
  --model "provider/model" \
  --auto-approve
```
