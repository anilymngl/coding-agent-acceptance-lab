"""Provenance-aware Gemma experiment inventory.

Groups Gemma rows by experiment_id before any aggregation. Deduplicates by
run_id across database files. Separates controlled matrix evidence from smoke
tests, ad-hoc runs, and overlapping duplicates. Outputs a Markdown report to
stdout.

This report is a frozen snapshot generated from local SQLite sources that are
not committed to the repository. It is not independently reproducible from a
clean checkout.

Usage:
  uv run python scripts/analyze_gemma.py
  uv run python scripts/analyze_gemma.py > reports/gemma-experiments-inventory.md
"""

import hashlib
import json
import sqlite3
import glob
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone

# ── controlled matrix definitions (from configs/matrix/*.json) ──────────
CONTROLLED_MATRICES = {
    "local-gemma4-two-model-2026-06-20": {
        "config": "configs/matrix/local-gemma4-two-model.json",
        "desc": "e4b vs 31b, maintenance_value sparse, pass@1",
        "expected_models": ["gemma4-e4b", "gemma4-31b"],
        "expected_packs": {"maintenance_value": 10},  # pack -> scenario count
        "expected_modes": {"maintenance_value": ["sparse"]},
    },
    "local-gemma4-smallest-two-2026-06-20": {
        "config": "configs/matrix/local-gemma4-smallest-two.json",
        "desc": "e4b vs 12b, maintenance_value sparse + contract_visible, pass@1",
        "expected_models": ["gemma4-e4b", "gemma4-12b"],
        "expected_packs": {"maintenance_value": 10},
        "expected_modes": {"maintenance_value": ["sparse", "contract_visible"]},
    },
    "north-mini-vs-gemma4-12b-2026-06-21": {
        "config": "configs/matrix/north-mini-vs-gemma4-12b.json",
        "desc": "North Mini vs Gemma 4 12b, ci_forensics + maintenance_value + product_workflows, sparse + contract_visible, pass@1",
        "expected_models": ["gemma4-12b"],  # only Gemma side (north-mini excluded)
        "expected_packs": {"ci_forensics": 12, "maintenance_value": 10, "product_workflows": 11},
        "expected_modes": {
            "ci_forensics": ["sparse", "contract_visible"],
            "maintenance_value": ["sparse", "contract_visible"],
            "product_workflows": ["sparse", "contract_visible"],
        },
    },
}

# experiment_ids that are known duplicates of controlled matrices (same config,
# different run) or subset retries
DUPLICATE_EXPERIMENTS = {
    "local-gemma4-full-2026-06-20": {
        "config": "configs/matrix/local-gemma4-full.json",
        "desc": "Overlap with smallest-two (same models, maintenance_value sparse). Different timeout settings.",
        "overlaps_with": ["local-gemma4-smallest-two-2026-06-20"],
    },
}

SMOKE_EXPERIMENTS = {
    "local-gemma4-12b-smoke-2026-06-20",
    "local-gemma4-e4b-smoke-2026-06-20",
}

# ad-hoc experiment patterns (prefix match)
AD_HOC_PREFIXES = [
    "20260620T",
    "20260621T",
]


# ── model alias -> full model ID mapping (from matrix configs) ─────────
def _model_aliases():
    """Return {alias: model_id} from known matrix configs."""
    aliases = {}
    for info in CONTROLLED_MATRICES.values():
        cfg_path = info["config"]
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            for m in cfg.get("models", []):
                aliases[m["alias"]] = m["id"]
        except Exception:
            pass
    return aliases


MODEL_ALIASES = _model_aliases()


def classify_experiment(experiment_id: str) -> str:
    """Classify experiment into: controlled | duplicate | smoke | ad_hoc | unknown."""
    for mid in sorted(CONTROLLED_MATRICES, key=len, reverse=True):
        if experiment_id.startswith(mid):
            return "controlled"
    for mid in sorted(DUPLICATE_EXPERIMENTS, key=len, reverse=True):
        if experiment_id.startswith(mid):
            return "duplicate"
    for sid in SMOKE_EXPERIMENTS:
        if experiment_id.startswith(sid):
            return "smoke"
    for prefix in AD_HOC_PREFIXES:
        if experiment_id.startswith(prefix):
            return "ad_hoc"
    return "unknown"


def extract_prefix(experiment_id: str) -> str:
    """Extract matrix prefix from experiment_id like 'local-gemma4-two-model-2026-06-20-gemma4-31b-...'."""
    for mid in sorted(CONTROLLED_MATRICES, key=len, reverse=True):
        if experiment_id.startswith(mid):
            return mid
    for mid in sorted(DUPLICATE_EXPERIMENTS, key=len, reverse=True):
        if experiment_id.startswith(mid):
            return mid
    return experiment_id


def outcome_label(pub: int, hid: int) -> str:
    """Return human-readable outcome for a (public_pass, hidden_pass) pair."""
    if pub and hid:
        return "hidden pass"
    elif pub and not hid:
        return "false-green"
    else:
        return "public-red"


def outcome_emoji(pub: int, hid: int) -> str:
    """Return emoji outcome string for per-scenario tables."""
    if pub and hid:
        return "&#x2705;&#x2705; hidden pass"
    elif pub and not hid:
        return "&#x2705;&#x274C; **false-green**"
    else:
        return "&#x274C;&#x274C; public-red"


def row_payload(row: dict) -> tuple:
    """Comparable tuple of key fields for duplicate detection."""
    return tuple(
        row.get(col) for col in [
            "scenario", "model", "challenge_pack", "prompt_mode",
            "started_at", "public_pass", "hidden_pass", "opencode_exit_code",
            "duration_seconds",
        ]
    )


def main():
    db_paths = sorted(Path(p) for p in glob.glob("data/**/*.sqlite", recursive=True))
    db_count = len(db_paths)
    db_read = 0
    db_no_table = 0
    db_error = 0
    scan_errors = []  # (db_path, error_repr)

    # ── global run_id dedup registry ────────────────────────────────────
    runs_by_id: dict[str, dict] = {}
    run_sources: dict[str, set[str]] = defaultdict(set)
    duplicate_run_ids = 0
    conflict_run_ids = 0
    excluded_gemma3 = 0

    # ── collect every Gemma row with provenance ──────────────────────────
    # { experiment_id: [row_dict, ...] }
    experiments = defaultdict(list)

    for db_path in db_paths:
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "runs" not in tables:
                conn.close()
                db_no_table += 1
                continue

            columns = [
                c["name"]
                for c in conn.execute("PRAGMA table_info(runs)").fetchall()
            ]
            select_cols = [
                "run_id",
                "experiment_id",
                "scenario",
                "model",
                "challenge_pack",
                "prompt_mode",
                "started_at",
                "public_pass",
                "hidden_pass",
                "opencode_exit_code",
            ]
            if "duration_seconds" in columns:
                select_cols.append("duration_seconds")

            query = f"SELECT {', '.join(select_cols)} FROM runs"
            rows = conn.execute(query).fetchall()
            db_read += 1

            for r in rows:
                model = (r["model"] or "").strip()
                if not model or "gemma" not in model.lower():
                    continue
                if "gemma3" in model.lower() or "gemma 3" in model.lower():
                    excluded_gemma3 += 1
                    continue

                d = {col: r[col] for col in select_cols}
                d["_db"] = str(db_path)

                # ── run_id dedup ──────────────────────────────────────
                run_id = d["run_id"]
                run_sources[run_id].add(str(db_path))

                if run_id in runs_by_id:
                    existing = runs_by_id[run_id]
                    if row_payload(d) != row_payload(existing):
                        conflict_run_ids += 1
                    else:
                        duplicate_run_ids += 1
                    continue  # skip duplicate

                runs_by_id[run_id] = d
                exp_id = d["experiment_id"] or ""
                experiments[exp_id].append(d)

            conn.close()
        except Exception as exc:
            scan_errors.append((str(db_path), repr(exc)))
            db_error += 1

    raw_rows_discovered = len(runs_by_id) + duplicate_run_ids + conflict_run_ids
    unique_runs_retained = len(runs_by_id)

    # ── header ──────────────────────────────────────────────────────────
    print(
        f"# Gemma Experiment Inventory — Provenance-Aware\n"
        f"\n> **Frozen snapshot.** Generated from local SQLite sources under `data/`\n"
        f"> that are not committed to the repository. This report is not independently\n"
        f"> reproducible from a clean checkout.\n"
        f"\nGenerated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    )

    # scan health
    print("## Database Scan\n")
    print(f"| | Count |")
    print(f"|---|---|")
    print(f"| Discovered paths | {db_count} |")
    print(f"| Read successfully | {db_read} |")
    print(f"| No runs table | {db_no_table} |")
    print(f"| Query error | {db_error} |")
    print(f"| Raw rows discovered (pre-dedup) | {raw_rows_discovered} |")
    print(f"| Exact duplicate run_ids removed | {duplicate_run_ids} |")
    print(f"| Conflicting duplicate run_ids | {conflict_run_ids} |")
    print(f"| Unique run_ids retained | {unique_runs_retained} |")
    print(f"| Excluded gemma3 rows | {excluded_gemma3} |")
    print()

    if scan_errors:
        print("### Scan Errors\n")
        for db, err in scan_errors:
            print(f"- `{db}`: {err}")
        print()

    print(f"Unique experiment_ids: {len(experiments)}\n")

    # ── classify experiments ─────────────────────────────────────────────
    classified = defaultdict(list)
    for exp_id, rows in sorted(experiments.items()):
        cls = classify_experiment(exp_id)
        classified[cls].append((exp_id, rows))

    # ── build controlled signature set ──────────────────────────────────
    controlled_signatures = set()
    for exp_id, rows in classified.get("controlled", []):
        for r in rows:
            sig = (r["challenge_pack"], r["scenario"], r["model"].strip(), r["prompt_mode"])
            controlled_signatures.add(sig)

    # ── detect cross-experiment overlap ─────────────────────────────────
    seen_signatures = defaultdict(set)
    for exp_id, rows in experiments.items():
        for r in rows:
            sig = (r["challenge_pack"], r["scenario"], r["model"].strip(), r["prompt_mode"])
            seen_signatures[sig].add(exp_id)

    overlapping_signatures = {
        sig: exps for sig, exps in seen_signatures.items() if len(exps) > 1
    }

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1: CONTROLLED EVIDENCE
    # ══════════════════════════════════════════════════════════════════════
    print("---\n")
    print("## 1. Controlled Evidence\n")
    print(
        "Each subsection is a single matrix config with uniform run policy,\n"
        "scenario coverage, and prompt lanes. Rows are not pooled across experiments.\n"
    )

    controlled = classified.get("controlled", [])
    if not controlled:
        print("_(No controlled Gemma experiments found.)_\n")
    else:
        matrix_groups = defaultdict(list)
        for exp_id, rows in controlled:
            mid = extract_prefix(exp_id)
            matrix_groups[mid].append((exp_id, rows))

        for mid in sorted(matrix_groups):
            info = CONTROLLED_MATRICES.get(mid, {})
            exp_list = matrix_groups[mid]
            total_cell_rows = sum(len(rows) for _, rows in exp_list)
            print(f"### {mid}\n")
            print(f"- **Config:** `{info.get('config', '?')}`")
            print(f"- **Description:** {info.get('desc', '?')}")
            print(f"- **Cells (model+pack+mode combos):** {len(exp_list)}")
            print(f"- **Total rows:** {total_cell_rows}\n")

            for exp_id, rows in sorted(exp_list):
                groups = defaultdict(list)
                for r in rows:
                    key = (r["model"], r["challenge_pack"], r["prompt_mode"])
                    groups[key].append(r)

                for key in sorted(groups):
                    model, pack, mode = key
                    gr = groups[key]
                    total = len(gr)
                    pub = sum(1 for r in gr if r["public_pass"])
                    hid = sum(1 for r in gr if r["hidden_pass"])
                    fg = sum(1 for r in gr if r["public_pass"] and not r["hidden_pass"])
                    public_red = sum(1 for r in gr if not r["public_pass"] and not r["hidden_pass"])
                    fg_rate = f"{fg}/{pub}" if pub > 0 else "—"

                    # ── coverage check ─────────────────────────────────
                    expected_scenarios = info.get("expected_packs", {}).get(pack)
                    scenarios_found = sorted(set(r["scenario"] for r in gr))
                    coverage_status = "complete"
                    if expected_scenarios:
                        if len(scenarios_found) < expected_scenarios:
                            coverage_status = f"partial ({len(scenarios_found)}/{expected_scenarios})"
                        elif len(scenarios_found) > expected_scenarios:
                            coverage_status = f"overcomplete ({len(scenarios_found)}/{expected_scenarios})"

                    print(f"#### `{model}` — `{pack}` — `{mode}`\n")
                    print(f"| | Count |")
                    print(f"|---|---|")
                    print(f"| Experiment ID | `{exp_id}` |")
                    print(f"| Total runs | {total} |")
                    print(f"| Coverage | {coverage_status} |")
                    print(f"| Public pass | {pub} |")
                    print(f"| Hidden pass | {hid} |")
                    print(f"| False-green (public=pass, hidden=fail) | {fg} |")
                    print(f"| False-green / public-green rate | {fg_rate} |")
                    print(f"| Public-red (no public pass) | {public_red} |")
                    avg_dur = (
                        f"{sum(r['duration_seconds'] for r in gr if r.get('duration_seconds'))/len([r for r in gr if r.get('duration_seconds')]):.1f}s"
                        if any(r.get("duration_seconds") for r in gr)
                        else "N/A"
                    )
                    print(f"| Avg duration | {avg_dur} |")
                    print()

                    # per-scenario detail
                    print("| Scenario | Public | Hidden | Outcome |")
                    print("|---|---|---|---|")
                    for r in sorted(gr, key=lambda x: x["scenario"]):
                        pub_str = "Pass" if r["public_pass"] else "Fail"
                        hid_str = "Pass" if r["hidden_pass"] else "Fail"
                        print(f"| `{r['scenario']}` | {pub_str} | {hid_str} | {outcome_emoji(r['public_pass'], r['hidden_pass'])} |")
                    print()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2: HISTORICAL INVENTORY
    # ══════════════════════════════════════════════════════════════════════
    print("---\n")
    print("## 2. Historical Inventory\n")
    print(
        "Rows not part of the controlled matrices above. Grouped by experiment_id\n"
        "and explicitly labeled. **Do not pool these with controlled evidence.**\n"
    )

    other_classes = ["duplicate", "smoke", "ad_hoc", "unknown"]
    any_other = False

    for cls in other_classes:
        items = classified.get(cls, [])
        if not items:
            continue
        any_other = True

        label_map = {
            "duplicate": "Overlapping / Duplicate Experiments",
            "smoke": "Smoke Tests",
            "ad_hoc": "Ad-hoc Manual Runs",
            "unknown": "Unknown Provenance",
        }
        print(f"### {label_map[cls]}\n")

        for exp_id, rows in sorted(items):
            n_rows = len(rows)
            models = sorted(set(r["model"] for r in rows))
            packs = sorted(set(r["challenge_pack"] for r in rows))
            modes = sorted(set(r["prompt_mode"] for r in rows))
            pub = sum(1 for r in rows if r["public_pass"])
            hid = sum(1 for r in rows if r["hidden_pass"])
            fg = sum(1 for r in rows if r["public_pass"] and not r["hidden_pass"])

            # check overlap with *controlled* experiments specifically
            overlap_flag = ""
            if any(
                (r["challenge_pack"], r["scenario"], r["model"].strip(), r["prompt_mode"])
                in controlled_signatures
                for r in rows
            ):
                overlap_flag = " &#x26A0;&#xFE0F; overlaps with controlled experiments"

            info = DUPLICATE_EXPERIMENTS.get(exp_id, {})
            extra = ""
            if info:
                extra = f" — {info.get('desc', '')}"

            print(f"#### `{exp_id}`{extra}{overlap_flag}\n")
            print(f"- Rows: {n_rows} | Models: {', '.join(f'`{m}`' for m in models)}")
            print(f"- Packs: {', '.join(f'`{p}`' for p in packs)}")
            print(f"- Modes: {', '.join(f'`{m}`' for m in modes)}")
            print(f"- Public pass: {pub} | Hidden pass: {hid} | False-green: {fg}")
            db_list = sorted(set(r["_db"] for r in rows))
            print(f"- DBs: {', '.join(Path(db).name for db in db_list)}")
            print()

            print("| Scenario | Public | Hidden | Outcome |")
            print("|---|---|---|---|")
            for r in sorted(rows, key=lambda x: x["scenario"]):
                pub_s = "Pass" if r["public_pass"] else "Fail"
                hid_s = "Pass" if r["hidden_pass"] else "Fail"
                print(f"| `{r['scenario']}` | {pub_s} | {hid_s} | {outcome_label(r['public_pass'], r['hidden_pass'])} |")
            print()

    if not any_other:
        print("_(No other experiments found.)_\n")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3: SOURCE MANIFEST
    # ══════════════════════════════════════════════════════════════════════
    print("---\n")
    print("## 3. Source Manifest\n")
    print(
        "Database sources scanned to produce this inventory. These files are not\n"
        "committed to the repository.\n"
    )
    print("| Database | SHA-256 (first 16) | Rows scanned | Unique runs | Experiment IDs |")
    print("|---|---:|---:|---|")

    for db_path in db_paths:
        try:
            file_hash = hashlib.sha256(db_path.read_bytes()).hexdigest()[:16]
        except Exception:
            file_hash = "unreadable"

        # count unique run_ids in this DB
        db_run_count = sum(
            1 for r in runs_by_id.values()
            if r["_db"] == str(db_path)
        )
        db_exp_ids = sorted(set(
            runs_by_id[rid]["experiment_id"]
            for rid, sources in run_sources.items()
            if str(db_path) in sources
        ))

        print(f"| `{db_path}` | `{file_hash}` | ? | {db_run_count} | {len(db_exp_ids)} |")

    print()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4: CROSS-EXPERIMENT OVERLAP DIAGNOSTICS
    # ══════════════════════════════════════════════════════════════════════
    if overlapping_signatures:
        print("---\n")
        print("## 4. Cross-Experiment Overlap Diagnostics\n")
        print(
            "These (pack, scenario, model, prompt_mode) tuples appear in multiple\n"
            "experiment_ids. They explain why naive pooling would inflate counts.\n"
        )
        for sig, exps in sorted(overlapping_signatures.items()):
            pack, scenario, model, mode = sig
            print(
                f"- `{pack}` / `{scenario}` / `{model}` / `{mode}` — "
                f"appears in {len(exps)} experiments: {', '.join(sorted(exps))}"
            )
        print()

    # ── footer ──────────────────────────────────────────────────────────
    print("---\n")
    print("## Analysis Notes\n")
    print(
        "- **Unit of analysis**: experiment_id, not model name. Aggregation only within\n"
        "  a single controlled experiment.\n"
        "- **False-green rate**: false-greens divided by public-green attempts\n"
        "  (not all retained rows, not all public passes across experiments).\n"
        "- **Public-red**: rows with `public_pass=0, hidden_pass=0`. The cause\n"
        "  (timeout, provider error, bad patch, no edit, etc.) is not classified\n"
        "  from public-pass data alone. Do not read public-red as an\n"
        "  infrastructure label without separate runtime evidence.\n"
        "- **Overlapping rows**: flagged with &#x26A0;&#xFE0F; when the same\n"
        "  (pack, scenario, model, prompt_mode) tuple exists in a controlled\n"
        "  matrix.\n"
        "- Run IDs are deduplicated globally across all database files.\n"
        "  Conflicting duplicates (same run_id, different payload) are counted\n"
        "  in the scan header.\n"
        "- The controlled `local-gemma4-two-model` result (e4b 5/10 hidden,\n"
        "  31B 7/10 hidden, both 3 false-greens among public passes) remains the\n"
        "  cleanest Gemma evidence to date. It is pass@1, small, and sparse-only.\n"
        "- **Frozen snapshot.** The source databases under `data/` are gitignored.\n"
        "  Re-running this script requires the same local data.\n"
    )


if __name__ == "__main__":
    main()
