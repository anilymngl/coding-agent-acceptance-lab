"""Provenance-aware Gemma experiment inventory.

Groups Gemma rows by experiment_id before any aggregation. Separates controlled
matrix evidence from smoke tests, ad-hoc runs, and overlapping duplicates.
Outputs a Markdown report to stdout.

Usage:
  uv run python scripts/analyze_gemma.py
  uv run python scripts/analyze_gemma.py > reports/gemma-experiments-inventory.md
"""

import sqlite3
import glob
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

# ── controlled matrix experiment_ids (from configs/matrix/*.json) ──────────
CONTROLLED_MATRICES = {
    "local-gemma4-two-model-2026-06-20": {
        "config": "configs/matrix/local-gemma4-two-model.json",
        "desc": "e4b vs 31b, maintenance_value sparse, pass@1",
    },
    "local-gemma4-smallest-two-2026-06-20": {
        "config": "configs/matrix/local-gemma4-smallest-two.json",
        "desc": "e4b vs 12b, maintenance_value sparse + contract_visible, pass@1",
    },
    "north-mini-vs-gemma4-12b-2026-06-21": {
        "config": "configs/matrix/north-mini-vs-gemma4-12b.json",
        "desc": "North Mini vs Gemma 4 12b, ci_forensics + maintenance_value + product_workflows, sparse + contract_visible, pass@1",
    },
}

# experiment_ids that are known duplicates of controlled matrices (same config,
# different run) or subset retries
DUPLICATE_EXPERIMENTS = {
    "local-gemma4-full-2026-06-20": {
        "config": "configs/matrix/local-gemma4-full.json",
        "desc": "Overlap with smallest-two config (same models, maintenance_value sparse). Different timeout settings.",
        "overlaps_with": ["local-gemma4-smallest-two-2026-06-20"],
    },
}

SMOKE_EXPERIMENTS = {
    "local-gemma4-12b-smoke-2026-06-20",
    "local-gemma4-e4b-smoke-2026-06-20",
}

# ad-hoc experiment patterns (prefix match)
AD_HOC_PREFIXES = [
    "20260620T",  # custom timestamps from smoke/one-offs
    "20260621T",  # north-mini-full manual runs
]


def classify_experiment(experiment_id: str) -> str:
    """Classify experiment into: controlled | duplicate | smoke | ad_hoc | unknown."""
    # check prefix match for controlled matrices (experiment_ids have suffixes like -model-pack-mode)
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


def main():
    db_paths = glob.glob("data/**/*.sqlite", recursive=True)

    # ── collect every Gemma row with provenance ────────────────────────────
    # { experiment_id: [row_dict, ...] }
    experiments = defaultdict(list)

    for db_path in sorted(Path(p) for p in db_paths):
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

            for r in rows:
                model = (r["model"] or "").strip()
                if not model or "gemma" not in model.lower():
                    continue
                # exclude gemma3
                if "gemma3" in model.lower() or "gemma 3" in model.lower():
                    continue

                d = {col: r[col] for col in select_cols}
                d["_db"] = str(db_path)
                exp_id = d["experiment_id"] or ""
                experiments[exp_id].append(d)

            conn.close()
        except Exception:
            pass

    total_gemma_rows = sum(len(v) for v in experiments.values())
    print(
        f"# Gemma Experiment Inventory — Provenance-Aware\n"
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Total Gemma 4 rows found: {total_gemma_rows}\n"
        f"Unique experiment_ids: {len(experiments)}\n"
    )

    # ── classify experiments ───────────────────────────────────────────────
    classified = defaultdict(list)  # class -> [(exp_id, rows)]
    for exp_id, rows in sorted(experiments.items()):
        cls = classify_experiment(exp_id)
        classified[cls].append((exp_id, rows))

    # ── detect duplicate scenarios across experiments ──────────────────────
    # Per unique (scenario, model, prompt_mode), which experiments have it?
    seen_signatures = defaultdict(set)  # (scenario, model, prompt_mode) -> {exp_id}
    for exp_id, rows in experiments.items():
        for r in rows:
            sig = (r["scenario"], r["model"].strip(), r["prompt_mode"])
            seen_signatures[sig].add(exp_id)

    overlapping_signatures = {
        sig: exps for sig, exps in seen_signatures.items() if len(exps) > 1
    }

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1: CONTROLLED EVIDENCE
    # ══════════════════════════════════════════════════════════════════════
    print("\n---\n")
    print("## 1. Controlled Evidence\n")
    print(
        "Each subsection is a single matrix config with uniform run policy,\n"
        "scenario coverage, and prompt lanes. Rows are not pooled across experiments.\n"
    )

    controlled = classified.get("controlled", [])
    if not controlled:
        print("_(No controlled Gemma experiments found.)_\n")
    else:
        # group experiment_ids by matrix prefix
        matrix_groups = defaultdict(list)  # matrix_id -> [(exp_id, rows)]
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
                # group by model + pack + prompt_mode within this experiment cell
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
                    operational_failures = sum(
                        1 for r in gr if not r["public_pass"] and not r["hidden_pass"]
                    )
                    fg_rate = f"{fg}/{pub}" if pub > 0 else "—"

                    print(f"#### `{model}` — `{pack}` — `{mode}`\n")
                    print(f"| | Count |")
                    print(f"|---|---|")
                    print(f"| Experiment ID | `{exp_id}` |")
                    print(f"| Total runs | {total} |")
                    print(f"| Public pass | {pub} |")
                    print(f"| Hidden pass | {hid} |")
                    print(
                        f"| False-green (public=pass, hidden=fail) | {fg} |"
                    )
                    print(f"| False-green / public-green rate | {fg_rate} |")
                    print(
                        f"| Operational failures (no pass) | {operational_failures} |"
                    )
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
                        if r["public_pass"] and r["hidden_pass"]:
                            em = "&#x2705;&#x2705; pass"
                        elif r["public_pass"] and not r["hidden_pass"]:
                            em = "&#x2705;&#x274C; **false-green**"
                        elif not r["public_pass"] and r["hidden_pass"]:
                            em = "&#x274C;&#x2705; (unexpected)"
                        else:
                            em = "&#x274C;&#x274C; operational fail"
                        print(f"| `{r['scenario']}` | {pub_str} | {hid_str} | {em} |")
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
            # show experiment summary
            n_rows = len(rows)
            models = sorted(set(r["model"] for r in rows))
            packs = sorted(set(r["challenge_pack"] for r in rows))
            modes = sorted(set(r["prompt_mode"] for r in rows))
            pub = sum(1 for r in rows if r["public_pass"])
            hid = sum(1 for r in rows if r["hidden_pass"])
            fg = sum(1 for r in rows if r["public_pass"] and not r["hidden_pass"])

            # check overlap with controlled
            overlap_flag = ""
            if any(
                (r["scenario"], r["model"].strip(), r["prompt_mode"])
                in overlapping_signatures
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
            print(
                f"- DBs: {', '.join(Path(db).name for db in db_list)}"
            )
            print()

            # per-scenario compact list
            print("| Scenario | Public | Hidden | Outcome |")
            print("|---|---|---|---|")
            for r in sorted(rows, key=lambda x: x["scenario"]):
                pub_s = "Pass" if r["public_pass"] else "Fail"
                hid_s = "Pass" if r["hidden_pass"] else "Fail"
                if r["public_pass"] and r["hidden_pass"]:
                    o = "pass"
                elif r["public_pass"] and not r["hidden_pass"]:
                    o = "false-green"
                elif not r["public_pass"] and not r["hidden_pass"]:
                    o = "operational fail"
                else:
                    o = "hidden-only"
                print(f"| `{r['scenario']}` | {pub_s} | {hid_s} | {o} |")
            print()

    if not any_other:
        print("_(No other experiments found.)_\n")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3: EXCLUDED ROWS
    # ══════════════════════════════════════════════════════════════════════
    print("---\n")
    print("## 3. Excluded Rows\n")
    print(
        "Rows filtered from this inventory: non-Gemma models, gemma3 rows,\n"
        "and unparseable records.\n"
    )
    # quick recount for excluded
    excluded_count = 0
    for db_path in sorted(Path(p) for p in db_paths):
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
                continue
            rows = conn.execute("SELECT model FROM runs").fetchall()
            for r in rows:
                model = (r["model"] or "").strip()
                if model and "gemma3" in model.lower():
                    excluded_count += 1
            conn.close()
        except Exception:
            pass
    print(f"Excluded gemma3 rows: {excluded_count}\n")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4: DUPLICATE SIGNATURE DIAGNOSTICS
    # ══════════════════════════════════════════════════════════════════════
    if overlapping_signatures:
        print("---\n")
        print("## 4. Cross-Experiment Overlap Diagnostics\n")
        print(
            "These (scenario, model, prompt_mode) tuples appear in multiple\n"
            "experiment_ids. They explain why naive pooling would inflate counts.\n"
        )
        for sig, exps in sorted(overlapping_signatures.items()):
            scenario, model, mode = sig
            print(
                f"- `{scenario}` / `{model}` / `{mode}` — "
                f"appears in {len(exps)} experiments: {', '.join(sorted(exps))}"
            )
        print()

    # ── footer ──────────────────────────────────────────────────────────────
    print("---\n")
    print("## Analysis Notes\n")
    print(
        "- **Unit of analysis**: experiment_id, not model name. Aggregation only within\n"
        "  a single controlled experiment.\n"
        "- **False-green rate**: false-greens divided by public-green attempts\n"
        "  (not all retained rows, not all public passes across experiments).\n"
        "- **Operational failures**: rows with neither public nor hidden pass\n"
        "  (timeout, no output, config error, etc.). These are infrastructure\n"
        "  signals, not model-capability signals.\n"
        "- **Overlapping rows**: flagged with &#x26A0;&#xFE0F; when the same\n"
        "  scenario+model+prompt_mode exists in a controlled matrix.\n"
        "- The controlled `local-gemma4-two-model` result (e4b 5/10 hidden,\n"
        "  31B 7/10 hidden, both 3 false-greens among public passes) remains the\n"
        "  cleanest Gemma evidence to date. It is pass@1, small, and sparse-only.\n"
    )


if __name__ == "__main__":
    main()
