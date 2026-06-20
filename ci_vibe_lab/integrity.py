from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from ci_vibe_lab.analysis import is_headline_accepted_audit_status
from ci_vibe_lab.matrix import classify_row


ARTIFACT_FIELDS = (
    "prompt_path",
    "patch_path",
    "public_output_path",
    "hidden_output_path",
    "opencode_stdout_path",
    "opencode_stderr_path",
)

HASH_FIELDS = (
    "prompt_path",
    "patch_path",
    "hidden_output_path",
)


def sha256_file(path_value: object) -> str:
    if not path_value:
        return ""
    path = Path(str(path_value))
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class IntegrityIssue:
    severity: str
    category: str
    run_id: str
    field: str
    detail: str


@dataclass
class IntegrityReport:
    rows_checked: int = 0
    artifacts_checked: int = 0
    artifacts_present: int = 0
    artifacts_missing: int = 0
    hashes_computed: int = 0
    false_greens_total: int = 0
    false_greens_unclassified: int = 0
    quarantined_in_headline: int = 0
    missing_audit_rows: int = 0
    issues: list[IntegrityIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def add(self, severity: str, category: str, run_id: str, field_name: str, detail: str) -> None:
        self.issues.append(
            IntegrityIssue(
                severity=severity,
                category=category,
                run_id=run_id,
                field=field_name,
                detail=detail,
            )
        )


def verify_artifact_integrity(
    rows: list[dict[str, object]],
    audits: dict[str, dict[str, object]],
    *,
    expected_row_count: int | None = None,
) -> IntegrityReport:
    report = IntegrityReport(rows_checked=len(rows))
    audited_scenarios = set(audits)

    for row in rows:
        run_id = str(row.get("run_id", ""))
        scenario = str(row.get("scenario", ""))
        outcome = classify_row(row)
        audit = audits.get(scenario)

        if outcome == "false_green":
            report.false_greens_total += 1
            fairness = str((audit or {}).get("fairness_classification", "") or "")
            if not fairness or fairness == "semantic_contract_miss":
                if audit is None:
                    report.false_greens_unclassified += 1
                    report.add(
                        "warning",
                        "unclassified_false_green",
                        run_id,
                        "fairness_classification",
                        f"Scenario `{scenario}` has no audit row; false-green cannot be classified.",
                    )
                elif not str(audit.get("fairness_classification", "")):
                    report.false_greens_unclassified += 1
                    report.add(
                        "warning",
                        "unclassified_false_green",
                        run_id,
                        "fairness_classification",
                        f"Scenario `{scenario}` false-green has blank fairness classification.",
                    )

        if audit is None and scenario not in audited_scenarios:
            report.missing_audit_rows += 1
            report.add(
                "warning",
                "missing_audit",
                run_id,
                "scenario_audits",
                f"Scenario `{scenario}` has no scenario_audits row.",
            )

        audit_status = str((audit or {}).get("audit_status", "accepted"))
        if not is_headline_accepted_audit_status(audit_status):
            if outcome in {"hidden_pass", "false_green", "public_red"}:
                report.quarantined_in_headline += 1
                report.add(
                    "error",
                    "quarantined_in_headline",
                    run_id,
                    "audit_status",
                    f"Scenario `{scenario}` audit status `{audit_status}` should exclude it from headline metrics.",
                )

        for field_name in ARTIFACT_FIELDS:
            path_value = row.get(field_name)
            if not path_value:
                continue
            report.artifacts_checked += 1
            path = Path(str(path_value))
            if path.exists():
                report.artifacts_present += 1
            else:
                report.artifacts_missing += 1
                report.add(
                    "error",
                    "missing_artifact",
                    run_id,
                    field_name,
                    f"Artifact path does not exist: {path_value}",
                )

        for field_name in HASH_FIELDS:
            path_value = row.get(field_name)
            if not path_value:
                continue
            digest = sha256_file(path_value)
            if digest:
                report.hashes_computed += 1
            elif Path(str(path_value)).exists():
                report.add(
                    "error",
                    "hash_failed",
                    run_id,
                    field_name,
                    f"Could not compute SHA256 for existing path: {path_value}",
                )

    if expected_row_count is not None and expected_row_count != len(rows):
        report.add(
            "error",
            "row_count_mismatch",
            "",
            "row_count",
            f"Expected {expected_row_count} rows but loaded {len(rows)}.",
        )

    return report


def integrity_report_markdown(report: IntegrityReport) -> str:
    lines = [
        "# Artifact Integrity Report",
        "",
        "## Summary",
        "",
        f"- Rows checked: {report.rows_checked}",
        f"- Artifacts checked: {report.artifacts_checked}",
        f"- Artifacts present: {report.artifacts_present}",
        f"- Artifacts missing: {report.artifacts_missing}",
        f"- SHA256 hashes computed: {report.hashes_computed}",
        f"- False-greens total: {report.false_greens_total}",
        f"- False-greens unclassified: {report.false_greens_unclassified}",
        f"- Quarantined rows in headline: {report.quarantined_in_headline}",
        f"- Missing audit rows: {report.missing_audit_rows}",
        f"- Overall: {'PASS' if report.passed else 'FAIL'}",
        "",
    ]
    errors = [issue for issue in report.issues if issue.severity == "error"]
    warnings = [issue for issue in report.issues if issue.severity == "warning"]
    if errors:
        lines.extend(["## Errors", "", "| Run ID | Category | Field | Detail |", "|---|---|---|---|"])
        for issue in errors:
            lines.append(
                f"| `{issue.run_id}` | `{issue.category}` | `{issue.field}` | {issue.detail.replace('|', '/')} |"
            )
        lines.append("")
    if warnings:
        lines.extend(["## Warnings", "", "| Run ID | Category | Field | Detail |", "|---|---|---|---|"])
        for issue in warnings:
            lines.append(
                f"| `{issue.run_id}` | `{issue.category}` | `{issue.field}` | {issue.detail.replace('|', '/')} |"
            )
        lines.append("")
    if not report.issues:
        lines.extend(["## Issues", "", "No integrity issues detected.", ""])
    return "\n".join(lines) + "\n"
