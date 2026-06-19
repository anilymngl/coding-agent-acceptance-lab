METRIC_REGISTRY = {
    "ecommerce_revenue": {
        "source": "orders",
        "field": "amount",
        "aggregation": "sum",
        "description": "Total order revenue. Source amounts are in cents.",
    },
    "subscription_revenue": {
        "source": "subscriptions",
        "field": "amount",
        "aggregation": "sum",
        "description": "Total subscription revenue. Source amounts are in dollars.",
    },
    "order_count": {
        "source": "orders",
        "field": "id",
        "aggregation": "count",
        "description": "Number of completed orders. Dimensionless count.",
    },
    "refund_total": {
        "source": "refunds",
        "field": "amount",
        "aggregation": "sum",
        "description": "Total refunds issued. Source amounts are in cents.",
    },
}

SOURCES = {
    "orders": [
        {"id": 1, "amount": 5000},
        {"id": 2, "amount": 2500},
    ],
    "subscriptions": [
        {"id": 1, "amount": 9.99},
        {"id": 2, "amount": 19.99},
    ],
    "refunds": [
        {"id": 1, "amount": 1500},
    ],
}


def compute(metric_name: str) -> float:
    """Compute a single registered metric from its source data."""
    defn = METRIC_REGISTRY[metric_name]
    rows = SOURCES[defn["source"]]
    values = [row[defn["field"]] for row in rows]
    if defn["aggregation"] == "sum":
        return sum(values)
    if defn["aggregation"] == "count":
        return float(len(values))
    raise ValueError(f"unknown aggregation: {defn['aggregation']}")


def dashboard_total(metric_names: list[str]) -> float:
    """Self-serve dashboard: users pick metrics to sum into a single KPI."""
    return sum(compute(name) for name in metric_names)
