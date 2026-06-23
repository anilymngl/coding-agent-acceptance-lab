"""Generate a self-contained static HTML evaluator report from all SQLite DBs.

Scans data/matrix/**/*.sqlite for evaluator_reviews, joins with runs,
and produces reports/evaluator-report.html as pure static HTML.

Usage:
    uv run python -m ci_vibe_lab.generate_evaluator_report
"""

from __future__ import annotations

import base64
import glob
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def collect_reviews(data_root: Path) -> list[dict]:
    """Scan all SQLite DBs for evaluator_reviews, join with runs."""
    reviews = []
    for db_path in sorted(data_root.rglob("*.sqlite")):
        try:
            conn = _connect(db_path)
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "evaluator_reviews" not in tables:
                conn.close()
                continue

            rows = conn.execute("""
                SELECT
                    er.target_run_id, er.target_model, er.scenario,
                    er.evaluator_model, er.verdict, er.root_cause_category,
                    er.root_cause, er.missed_contract, er.patch_quality,
                    er.debug_discipline, er.severity, er.confidence,
                    er.evidence_json, er.recommendation, er.review_limits,
                    er.created_at
                FROM evaluator_reviews er
                ORDER BY er.scenario, er.created_at
            """).fetchall()

            for r in rows:
                run_data = {}
                if "runs" in tables:
                    run_row = conn.execute(
                        "SELECT patch, model_summary, public_pass, hidden_pass, "
                        "duration_seconds, patch_changed_lines, trap, vibe "
                        "FROM runs WHERE run_id = ?",
                        (r["target_run_id"],),
                    ).fetchone()
                    if run_row:
                        run_data = {
                            "patch": (run_row["patch"] or "")[:2000],
                            "model_summary": run_row["model_summary"] or "",
                            "public_pass": run_row["public_pass"],
                            "hidden_pass": run_row["hidden_pass"],
                            "duration_seconds": run_row["duration_seconds"],
                            "patch_changed_lines": run_row["patch_changed_lines"],
                            "trap": run_row["trap"] or "",
                            "vibe": run_row["vibe"] or "",
                        }

                evidence = []
                try:
                    evidence = json.loads(r["evidence_json"] or "[]")
                except json.JSONDecodeError:
                    pass

                reviews.append({
                    "target_run_id": r["target_run_id"],
                    "target_model": r["target_model"],
                    "scenario": r["scenario"],
                    "evaluator_model": r["evaluator_model"],
                    "verdict": r["verdict"],
                    "root_cause_category": r["root_cause_category"],
                    "root_cause": r["root_cause"],
                    "missed_contract": r["missed_contract"],
                    "patch_quality": r["patch_quality"],
                    "debug_discipline": r["debug_discipline"],
                    "severity": r["severity"],
                    "confidence": r["confidence"],
                    "evidence": evidence,
                    "recommendation": r["recommendation"],
                    "review_limits": r["review_limits"],
                    "created_at": r["created_at"],
                    "source_db": str(db_path),
                    **run_data,
                })
            conn.close()
        except Exception:
            continue
    return reviews


def _h(text: str) -> str:
    """HTML-escape text."""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _patch_html(patch: str) -> str:
    """Format patch as colored HTML."""
    if not patch:
        return '<span class="dim">no patch</span>'
    lines = []
    for line in patch.split("\n"):
        line = _h(line)
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(f'<span class="add">{line}</span>')
        elif line.startswith("-") and not line.startswith("---"):
            lines.append(f'<span class="del">{line}</span>')
        elif line.startswith("@@"):
            lines.append(f'<span class="ctx">{line}</span>')
        else:
            lines.append(line)
    return "<br>".join(lines)


def _evidence_html(evidence: list) -> str:
    if not evidence:
        return '<span class="dim">no evidence</span>'
    parts = []
    for e in evidence:
        parts.append(
            '<div class="evidence-item">'
            f'<div class="ev-src">{_h(e.get("source", ""))}</div>'
            f'<div class="ev-quote">{_h(e.get("quote", ""))}</div>'
            f'<div class="ev-interp">{_h(e.get("interpretation", ""))}</div>'
            "</div>"
        )
    return "\n".join(parts)


STYLES = """\
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;color:#1a1a1a;background:#fff;line-height:1.5}
.container{max-width:1000px;margin:0 auto;padding:40px 24px 80px}
h1{font-size:1.8rem;font-weight:800;letter-spacing:-0.02em;margin-bottom:8px}
h2{font-size:1.2rem;font-weight:700;margin-top:32px;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #eee}
.dim{color:#888;font-size:0.8rem}
.mono{font-family:'SF Mono','JetBrains Mono','Fira Code',monospace;font-size:0.85em}
.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:0.7rem;font-weight:600}
.tag.medium{background:#fff3cd;color:#856404}
.stats-row{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.stat{flex:1;min-width:100px;text-align:center;padding:14px;background:#f8f9fa;border-radius:8px;border:1px solid #e9ecef}
.stat .val{font-size:1.8rem;font-weight:800;line-height:1}
.stat .lab{font-size:0.7rem;color:#888;text-transform:uppercase;margin-top:4px}
.cause-bar{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:0.82rem}
.cause-bar .bar{height:20px;background:#1a1a1a;border-radius:4px;min-width:2px;transition:width 0.3s}
.cause-bar .ct{font-size:0.75rem;color:#888;min-width:24px;text-align:right}
.review{border:1px solid #e9ecef;border-radius:8px;margin:14px 0;overflow:hidden}
.review-header{padding:10px 16px;background:#f8f9fa;font-size:0.85rem;display:flex;justify-content:space-between;align-items:center}
.review-header strong{font-size:0.9rem}
.review-body{padding:16px}
.field{margin-bottom:10px}
.field-label{font-size:0.72rem;font-weight:600;text-transform:uppercase;color:#888;letter-spacing:0.04em;margin-bottom:2px}
.field-value{font-size:0.88rem;color:#333}
pre{font-family:'SF Mono','JetBrains Mono','Fira Code',monospace;font-size:0.75rem;line-height:1.5;background:#fafafa;border:1px solid #eee;border-radius:4px;padding:12px;overflow-x:auto;max-height:260px;white-space:pre-wrap}
.add{color:#27ae60}.del{color:#c0392b}.ctx{color:#999}
.evidence-item{background:#f8f9fa;border-left:3px solid #ddd;padding:8px 12px;margin:6px 0;font-size:0.8rem}
.ev-src{font-weight:600;font-size:0.68rem;text-transform:uppercase;color:#888}
.ev-interp{margin-top:4px;color:#666;font-size:0.78rem}
.meta{font-size:0.75rem;color:#888;margin-top:10px;padding-top:8px;border-top:1px solid #eee}
"""


def generate(data_root: Path, out_path: Path) -> None:
    reviews = collect_reviews(data_root)
    if not reviews:
        print("No evaluator reviews found.")
        return

    # Stats
    total = len(reviews)
    causes = Counter(r["root_cause_category"] for r in reviews)
    conf_sum = sum(r["confidence"] or 0 for r in reviews)
    avg_conf = conf_sum / total if total else 0
    pq_vals = [r["patch_quality"] for r in reviews if r["patch_quality"]]
    dd_vals = [r["debug_discipline"] for r in reviews if r["debug_discipline"]]
    avg_pq = sum(pq_vals) / len(pq_vals) if pq_vals else 0
    avg_dd = sum(dd_vals) / len(dd_vals) if dd_vals else 0
    max_cause = max(causes.values()) if causes else 1

    # Group by scenario
    by_scenario: dict[str, list[dict]] = {}
    for r in reviews:
        by_scenario.setdefault(r["scenario"], []).append(r)

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">',
        "<title>Evaluator Report</title>",
        f"<style>{STYLES}</style>",
        "</head><body><div class=container>",
        '<p class="dim mono">EVALUATOR REPORT</p>',
        "<h1>False-Green Verdicts</h1>",
        f'<p class="dim">{total} reviews · {len(causes)} root-cause categories · mean confidence {avg_conf:.2f}</p>',
        '<div class="stats-row">',
        f'<div class="stat"><div class="val">{total}</div><div class="lab">Reviews</div></div>',
        f'<div class="stat"><div class="val">{avg_conf:.2f}</div><div class="lab">Mean Confidence</div></div>',
        f'<div class="stat"><div class="val">{avg_pq:.1f}</div><div class="lab">Avg Patch Quality</div></div>',
        f'<div class="stat"><div class="val">{avg_dd:.1f}</div><div class="lab">Avg Debug Discipline</div></div>',
        "</div>",
        '<h2>Root-Cause Taxonomy</h2>',
    ]

    for cat, count in causes.most_common():
        pct = count / max_cause * 100 if max_cause else 0
        html_parts.append(
            f'<div class="cause-bar"><span style="min-width:180px">{_h(cat)}</span>'
            f'<span class="bar" style="width:{pct}%"></span>'
            f'<span class="ct">{count}</span></div>'
        )

    html_parts.append("<h2>Reviews by Scenario</h2>")

    for scenario, revs in sorted(by_scenario.items()):
        html_parts.append(f'<h3 style="margin-top:24px">{_h(scenario)} ({len(revs)} reviews)</h3>')
        for r in revs:
            header = (
                f'<span><strong>{_h(r["scenario"])}</strong> '
                f'<span class="tag medium">{_h(r["severity"])}</span></span>'
                f'<span class="dim">{_h(r["root_cause_category"])} · conf {(r["confidence"] or 0):.2f}</span>'
            )
            body = (
                f'<div class="field"><div class="field-label">Root Cause</div><div class="field-value">{_h(r["root_cause"])}</div></div>'
                f'<div class="field"><div class="field-label">Missed Contract</div><div class="field-value">{_h(r["missed_contract"])}</div></div>'
                f'<div class="field"><div class="field-label">Recommendation</div><div class="field-value">{_h(r["recommendation"])}</div></div>'
                + (f'<div class="field"><div class="field-label">Trap</div><div class="field-value">{_h(r["trap"])}</div></div>' if r.get("trap") else "")
                + (f'<div class="field"><div class="field-label">Model\'s Own Words</div><div class="field-value">{_h(r["model_summary"])}</div></div>' if r.get("model_summary") else "")
                + (f'<div class="field"><div class="field-label">Patch</div><pre>{_patch_html(r["patch"])}</pre></div>' if r.get("patch") else "")
                + f'<div class="field"><div class="field-label">Evidence ({len(r["evidence"])} items)</div>{_evidence_html(r["evidence"])}</div>'
                + f'<div class="meta">run: {_h(r["target_run_id"])} · model: {_h(r["target_model"])} · evaluator: {_h(r["evaluator_model"])} · db: {_h(r["source_db"])}</div>'
            )
            html_parts.append(f'<div class="review"><div class="review-header">{header}</div><div class="review-body">{body}</div></div>')

    html_parts.append("</div></body></html>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(html_parts), encoding="utf-8")
    print(f"Generated {out_path} ({total} reviews)")


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate evaluator report as static HTML.")
    parser.add_argument("--data-root", default="data/matrix")
    parser.add_argument("--out", default="reports/evaluator-report.html")
    args = parser.parse_args(argv)
    generate(Path(args.data_root), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
