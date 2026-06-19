from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


def row_get(row: object, key: str, default: object = None) -> object:
    if isinstance(row, Mapping):
        return row.get(key, default)
    try:
        return row[key]  # type: ignore[index]
    except (KeyError, IndexError, TypeError):
        return default


def as_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


@dataclass(frozen=True)
class TrustMetrics:
    total: int
    public_pass: int
    hidden_pass: int
    public_green_hidden_red: int
    public_red: int
    public_pass_rate: float
    hidden_pass_rate: float
    trust_gap: float
    false_green_rate: float
    public_red_rate: float
    severity_weighted_failure_rate: float | None = None


def compute_trust_metrics(
    rows: Iterable[object],
    *,
    audit_weights: Mapping[str, int] | None = None,
) -> TrustMetrics:
    materialized = list(rows)
    total = len(materialized)
    public_pass = 0
    hidden_pass = 0
    public_green_hidden_red = 0
    public_red = 0
    weighted_total = 0
    weighted_hidden_fail = 0

    for row in materialized:
        public_ok = as_int(row_get(row, "public_pass")) == 1
        hidden_ok = as_int(row_get(row, "hidden_pass")) == 1
        if public_ok:
            public_pass += 1
        if hidden_ok:
            hidden_pass += 1
        if public_ok and not hidden_ok:
            public_green_hidden_red += 1
        if not public_ok:
            public_red += 1
        if audit_weights is not None:
            scenario = str(row_get(row, "scenario", ""))
            weight = int(audit_weights.get(scenario, 3))
            weighted_total += weight
            if not hidden_ok:
                weighted_hidden_fail += weight

    public_pass_rate = safe_rate(public_pass, total)
    hidden_pass_rate = safe_rate(hidden_pass, total)
    return TrustMetrics(
        total=total,
        public_pass=public_pass,
        hidden_pass=hidden_pass,
        public_green_hidden_red=public_green_hidden_red,
        public_red=public_red,
        public_pass_rate=public_pass_rate,
        hidden_pass_rate=hidden_pass_rate,
        trust_gap=public_pass_rate - hidden_pass_rate,
        false_green_rate=safe_rate(public_green_hidden_red, public_pass),
        public_red_rate=safe_rate(public_red, total),
        severity_weighted_failure_rate=(
            safe_rate(weighted_hidden_fail, weighted_total) if audit_weights is not None else None
        ),
    )


def latest_per_model_scenario(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    sorted_rows = sorted(rows, key=lambda row: str(row.get("started_at", "")), reverse=True)
    seen: set[tuple[str, str]] = set()
    latest = []
    for row in sorted_rows:
        key = (str(row.get("model", "")), str(row.get("scenario", "")))
        if key in seen:
            continue
        seen.add(key)
        latest.append(row)
    return latest


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"
