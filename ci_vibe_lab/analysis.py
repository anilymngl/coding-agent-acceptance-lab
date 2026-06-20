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


@dataclass(frozen=True)
class ValueMetrics:
    attempts: int
    accepted_patches: int
    accepted_patches_per_review_hour: float
    accepted_patches_per_attempt_review_hour: float
    total_review_minutes: float
    all_attempt_review_minutes: float
    median_review_minutes: float
    median_changed_lines: float
    best_of_three_scenarios: int
    best_of_three_successes: int
    best_of_three_success_rate: float


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


def as_float(value: object) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def effective_review_minutes(row: object) -> float:
    manual = row_get(row, "manual_review_minutes")
    if manual not in {None, ""}:
        return as_float(manual)
    return as_float(row_get(row, "estimated_review_minutes"))


def accepted_patch(row: object) -> bool:
    return (
        as_int(row_get(row, "public_pass")) == 1
        and as_int(row_get(row, "hidden_pass")) == 1
        and str(row_get(row, "review_decision", "") or "").lower() != "reject"
    )


def select_best_patches(rows: Iterable[object]) -> list[object]:
    grouped: dict[tuple[str, str], list[object]] = {}
    for row in rows:
        key = (str(row_get(row, "model", "")), str(row_get(row, "scenario", "")))
        grouped.setdefault(key, []).append(row)

    selected: list[object] = []
    for group_rows in grouped.values():
        passing = [row for row in group_rows if accepted_patch(row)]
        if not passing:
            continue
        selected.append(
            sorted(
                passing,
                key=lambda row: (
                    as_int(row_get(row, "patch_changed_lines")),
                    str(row_get(row, "started_at", "")),
                ),
            )[0]
        )
    return selected


def compute_value_metrics(rows: Iterable[object]) -> ValueMetrics:
    materialized = list(rows)
    selected = select_best_patches(materialized)
    grouped_keys = {
        (str(row_get(row, "model", "")), str(row_get(row, "scenario", "")))
        for row in materialized
    }
    success_keys = {
        (str(row_get(row, "model", "")), str(row_get(row, "scenario", "")))
        for row in selected
    }
    review_minutes = [effective_review_minutes(row) for row in selected]
    total_review_minutes = sum(review_minutes)
    all_attempt_review_minutes = sum(effective_review_minutes(row) for row in materialized)
    accepted = len(selected)
    return ValueMetrics(
        attempts=len(materialized),
        accepted_patches=accepted,
        accepted_patches_per_review_hour=(
            accepted / (total_review_minutes / 60.0) if total_review_minutes else 0.0
        ),
        accepted_patches_per_attempt_review_hour=(
            accepted / (all_attempt_review_minutes / 60.0) if all_attempt_review_minutes else 0.0
        ),
        total_review_minutes=total_review_minutes,
        all_attempt_review_minutes=all_attempt_review_minutes,
        median_review_minutes=median(review_minutes),
        median_changed_lines=median([as_float(row_get(row, "patch_changed_lines")) for row in selected]),
        best_of_three_scenarios=len(grouped_keys),
        best_of_three_successes=len(success_keys),
        best_of_three_success_rate=safe_rate(len(success_keys), len(grouped_keys)),
    )


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"
