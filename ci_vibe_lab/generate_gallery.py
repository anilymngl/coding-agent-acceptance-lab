"""Generate a self-contained HTML gallery with charts from all SQLite DBs.

Scans data/matrix/**/*.sqlite for runs, computes scorecards, and produces
reports/gallery.html with Chart.js charts and interactive tables.

Usage:
    uv run python -m ci_vibe_lab.generate_gallery
"""

from __future__ import annotations

import base64
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_json(obj) -> str:
    """Serialize to JSON and base64-encode for safe JavaScript embedding."""
    return base64.b64encode(json.dumps(obj, ensure_ascii=True).encode()).decode()


def collect_all_runs(data_root: Path) -> list[dict]:
    """Scan all SQLite DBs for runs, deduplicate by run_id."""
    seen = set()
    runs = []
    for db_path in sorted(data_root.rglob("*.sqlite")):
        try:
            conn = _connect(db_path)
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "runs" not in tables:
                conn.close()
                continue
            rows = conn.execute("""
                SELECT run_id, scenario, scenario_title, challenge_pack, category,
                       difficulty, model, prompt_mode, public_pass, hidden_pass,
                       opencode_exit_code, duration_seconds, patch_changed_lines,
                       model_summary, started_at
                FROM runs ORDER BY id
            """).fetchall()
            for r in rows:
                rid = r["run_id"]
                if rid in seen:
                    continue
                seen.add(rid)
                runs.append(dict(r))
            conn.close()
        except Exception:
            continue
    return runs


def collect_evaluator_reviews(data_root: Path) -> list[dict]:
    """Scan all SQLite DBs for evaluator_reviews."""
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
                SELECT target_run_id, scenario, root_cause_category, confidence,
                       severity, patch_quality, debug_discipline
                FROM evaluator_reviews ORDER BY id
            """).fetchall()
            for r in rows:
                reviews.append(dict(r))
            conn.close()
        except Exception:
            continue
    return reviews


def classify_row(row: dict) -> str:
    """Classify a run row into an outcome."""
    exit_code = row.get("opencode_exit_code") or 0
    pub = row.get("public_pass") or 0
    hid = row.get("hidden_pass") or 0

    if exit_code == 0:
        if pub and hid:
            return "hidden_pass"
        if pub and not hid:
            return "false_green"
        return "public_red"
    if exit_code == 124:
        return "timeout"
    return "error"


def normalize_model(model_id: str) -> str:
    """Shorten model IDs for display."""
    m = {
        "opencode/north-mini-code-free": "North Mini",
        "ollama/gemma4:e4b": "Gemma 4B",
        "ollama/gemma4:12b": "Gemma 12B",
        "ollama/gemma4:31b": "Gemma 31B",
        "openrouter/poolside/laguna-xs.2:free": "Laguna XS.2",
        "deepseek/deepseek-v4-pro": "DeepSeek V4",
        "opencode-go/glm-5.2": "GLM 5.2",
    }
    return m.get(model_id, model_id.split("/")[-1])


def build_scorecard(runs: list[dict]) -> list[dict]:
    """Build per-model×pack×lane scorecards."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in runs:
        outcome = classify_row(r)
        if outcome in ("hidden_pass", "false_green", "public_red"):
            key = (r["model"], r["challenge_pack"], r["prompt_mode"])
            groups[key].append(r)

    scorecard = []
    for (model, pack, lane), rows in sorted(groups.items()):
        pub = sum(1 for r in rows if r["public_pass"])
        hid = sum(1 for r in rows if r["hidden_pass"])
        fg = sum(1 for r in rows if r["public_pass"] and not r["hidden_pass"])
        avg_dur = sum(r["duration_seconds"] or 0 for r in rows) / len(rows) if rows else 0
        scorecard.append({
            "model": normalize_model(model),
            "model_id": model,
            "pack": pack,
            "lane": lane,
            "total": len(rows),
            "pub_pass": pub,
            "hid_pass": hid,
            "false_green": fg,
            "fg_rate": round(fg / pub * 100, 1) if pub else 0,
            "pub_rate": round(pub / len(rows) * 100, 1) if rows else 0,
            "hid_rate": round(hid / len(rows) * 100, 1) if rows else 0,
            "avg_duration": round(avg_dur, 1),
        })
    return scorecard


def build_scenario_matrix(runs: list[dict]) -> dict:
    """Build scenario×model outcome matrix for heatmap."""
    matrix: dict[str, dict[str, str]] = defaultdict(dict)
    for r in runs:
        outcome = classify_row(r)
        if outcome in ("hidden_pass", "false_green", "public_red"):
            model = normalize_model(r["model"])
            key = f"{r['challenge_pack']}:{r['scenario']}"
            # Keep latest attempt
            matrix[key][model] = outcome
    return dict(matrix)


def build_laguna_passk(runs: list[dict]) -> list[dict]:
    """Build Laguna pass@1/2/3 breakdown."""
    laguna_runs = [r for r in runs if "laguna" in (r.get("model") or "").lower()
                   and r.get("challenge_pack") == "ci_forensics"
                   and r.get("prompt_mode") == "sparse"]
    # Group by scenario, order by started_at
    by_scenario: dict[str, list[dict]] = defaultdict(list)
    for r in laguna_runs:
        by_scenario[r["scenario"]].append(r)
    for s in by_scenario:
        by_scenario[s].sort(key=lambda x: x.get("started_at", ""))

    passes = []
    for pass_num in range(3):
        pub = 0
        hid = 0
        fg = 0
        total = 0
        for scenario, rows in by_scenario.items():
            if pass_num < len(rows):
                total += 1
                if rows[pass_num]["public_pass"]:
                    pub += 1
                if rows[pass_num]["hidden_pass"]:
                    hid += 1
                if rows[pass_num]["public_pass"] and not rows[pass_num]["hidden_pass"]:
                    fg += 1
        passes.append({
            "pass": f"@{pass_num+1}",
            "pub": pub,
            "hid": hid,
            "fg": fg,
            "fg_rate": round(fg / pub * 100, 1) if pub else 0,
        })

    # Best-of-3
    bo3_pub = 0
    bo3_hid = 0
    for scenario, rows in by_scenario.items():
        if any(r["public_pass"] for r in rows):
            bo3_pub += 1
        if any(r["hidden_pass"] for r in rows):
            bo3_hid += 1
    bo3_fg = bo3_pub - bo3_hid
    passes.append({
        "pass": "best-3",
        "pub": bo3_pub,
        "hid": bo3_hid,
        "fg": bo3_fg,
        "fg_rate": round(bo3_fg / bo3_pub * 100, 1) if bo3_pub else 0,
    })
    return passes


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>The Trust Gap — Evidence Gallery</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;color:#1a1a1a;background:#fff;line-height:1.5}
.container{max-width:1100px;margin:0 auto;padding:40px 24px 80px}
h1{font-size:1.8rem;font-weight:800;letter-spacing:-0.02em;margin-bottom:8px}
h2{font-size:1.2rem;font-weight:700;margin-top:40px;margin-bottom:14px;padding-bottom:6px;border-bottom:1px solid #eee}
.dim{color:#888;font-size:0.8rem}
.mono{font-family:'SF Mono','JetBrains Mono','Fira Code',monospace;font-size:0.85em}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:0.82rem}
th{text-align:left;padding:5px 7px;border-bottom:2px solid #333;font-weight:600;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em}
td{padding:5px 7px;border-bottom:1px solid #eee}
.num{text-align:right;font-variant-numeric:tabular-nums}
.fg{color:#c0392b;font-weight:600}.hp{color:#27ae60;font-weight:600}
.chart-container{position:relative;margin:16px 0;background:#fff;border:1px solid #eee;border-radius:8px;padding:16px}
canvas{max-height:400px}
.tag{display:inline-block;padding:1px 6px;border-radius:3px;font-size:0.68rem;font-weight:600;margin-right:2px}
.tag.hidden_pass{background:#e8fde8;color:#27ae60}.tag.false_green{background:#fde8e8;color:#c0392b}.tag.public_red{background:#f0f0f0;color:#666}
.controls{display:flex;gap:8px;margin:12px 0;flex-wrap:wrap}
select{padding:5px 8px;border:1px solid #ccc;border-radius:4px;font-size:0.82rem;background:#fff}
.heatmap-grid{display:grid;gap:1px;margin:12px 0;font-size:0.72rem}
.heatmap-cell{padding:4px 6px;text-align:center;border-radius:3px;font-weight:600}
.heatmap-cell.hp{background:#d4edda;color:#155724}.heatmap-cell.fg{background:#f8d7da;color:#721c24}.heatmap-cell.pr{background:#e2e3e5;color:#383d41}
</style>
</head>
<body>
<div class="container">

<p class="dim mono" style="margin-bottom:8px">EVIDENCE GALLERY</p>
<h1>The Trust Gap</h1>
<p class="dim" id="summary"></p>

<!-- Chart 1: False-green rate by model × pack -->
<h2>False-Green Rate by Model and Pack (Sparse)</h2>
<div class="chart-container"><canvas id="chart-fg-sparse"></canvas></div>

<!-- Chart 2: Contract-visible effect -->
<h2>Contract-Visible Effect</h2>
<div class="chart-container"><canvas id="chart-cv-effect"></canvas></div>

<!-- Chart 3: Laguna pass@k -->
<h2>Laguna XS.2 Pass@k Variance</h2>
<div class="chart-container"><canvas id="chart-laguna-passk"></canvas></div>

<!-- Chart 4: Speed comparison -->
<h2>Speed Comparison (Avg Seconds)</h2>
<div class="chart-container"><canvas id="chart-speed"></canvas></div>

<!-- Chart 5: Evaluator root causes -->
<h2>Evaluator Root-Cause Taxonomy</h2>
<div class="chart-container" style="max-width:400px"><canvas id="chart-causes"></canvas></div>

<!-- Scorecard table -->
<h2>Full Scorecard</h2>
<div class="controls">
<select id="filter-pack"><option value="">All packs</option></select>
<select id="filter-lane"><option value="">All lanes</option></select>
<select id="filter-model"><option value="">All models</option></select>
</div>
<div id="scorecard-table"></div>

<!-- Scenario heatmap -->
<h2>Scenario × Model Heatmap (Sparse)</h2>
<div id="heatmap"></div>

</div>

<script>
const SCORECARD = JSON.parse(atob(\"__SCORECARD_JSON__\"));
const PASSK = JSON.parse(atob(\"__PASSK_JSON__\"));
const REVIEWS = JSON.parse(atob(\"__REVIEWS_JSON__\"));
const HEATMAP = JSON.parse(atob(\"__HEATMAP_JSON__\"));

const COLORS = {
  'North Mini':'#2563eb','Gemma 4B':'#7c3aed','Gemma 12B':'#7c3aed',
  'Gemma 31B':'#7c3aed','Laguna XS.2':'#6b7280','DeepSeek V4':'#059669','GLM 5.2':'#d97706'
};
function getColor(m){return COLORS[m]||'#999'}

document.getElementById('summary').textContent =
  SCORECARD.length + ' scorecard entries, ' + PASSK.length + ' pass@k data points, ' +
  REVIEWS.length + ' evaluator reviews.';

// Chart 1: FG rate by model × pack (sparse only)
(function(){
  const sparse = SCORECARD.filter(s => s.lane === 'sparse');
  const packs = [...new Set(sparse.map(s=>s.pack))].sort();
  const models = [...new Set(sparse.map(s=>s.model))].sort();
  new Chart(document.getElementById('chart-fg-sparse'), {
    type: 'bar',
    data: {
      labels: packs,
      datasets: models.map(m => ({
        label: m,
        data: packs.map(p => { const s = sparse.find(x=>x.model===m&&x.pack===p); return s?s.fg_rate:0; }),
        backgroundColor: getColor(m),
        borderRadius: 3,
      }))
    },
    options: {
      responsive: true,
      plugins: {title:{display:true,text:'False-green rate (%) — sparse prompts'}},
      scales: {y:{beginAtZero:true,title:{display:true,text:'False-green %'}}}
    }
  });
})();

// Chart 2: CV effect
(function(){
  const models = [...new Set(SCORECARD.map(s=>s.model))].sort();
  const packs = [...new Set(SCORECARD.map(s=>s.pack))].sort();
  const datasets = [];
  models.forEach(m => {
    const sparseRates = packs.map(p => { const s=SCORECARD.find(x=>x.model===m&&x.pack===p&&x.lane==='sparse'); return s?s.fg_rate:null; });
    const cvRates = packs.map(p => { const s=SCORECARD.find(x=>x.model===m&&x.pack===p&&x.lane==='contract_visible'); return s?s.fg_rate:null; });
    datasets.push({label:m+' sparse',data:sparseRates,borderColor:getColor(m),backgroundColor:getColor(m)+'33',fill:false,tension:0.3,pointRadius:5});
    datasets.push({label:m+' cv',data:cvRates,borderColor:getColor(m),backgroundColor:getColor(m)+'33',fill:false,tension:0.3,pointRadius:5,borderDash:[5,5]});
  });
  new Chart(document.getElementById('chart-cv-effect'), {
    type: 'line',
    data: {labels: packs, datasets},
    options: {
      responsive: true,
      plugins: {title:{display:true,text:'False-green rate: sparse vs contract-visible'}},
      scales: {y:{beginAtZero:true,title:{display:true,text:'False-green %'}}}
    }
  });
})();

// Chart 3: Laguna pass@k
(function(){
  new Chart(document.getElementById('chart-laguna-passk'), {
    type: 'bar',
    data: {
      labels: PASSK.map(p=>p.pass),
      datasets: [
        {label:'Hidden pass',data:PASSK.map(p=>p.hid),backgroundColor:'#27ae60',borderRadius:3},
        {label:'False-green',data:PASSK.map(p=>p.fg),backgroundColor:'#c0392b',borderRadius:3},
      ]
    },
    options: {
      responsive: true,
      plugins: {title:{display:true,text:'Laguna XS.2 ci_forensics sparse — pass@k'}},
      scales: {y:{beginAtZero:true,max:12,title:{display:true,text:'Scenarios (of 12)'}}}
    }
  });
})();

// Chart 4: Speed
(function(){
  const sparse = SCORECARD.filter(s => s.lane === 'sparse');
  const models = [...new Set(sparse.map(s=>s.model))].sort();
  const packs = [...new Set(sparse.map(s=>s.pack))].sort();
  new Chart(document.getElementById('chart-speed'), {
    type: 'bar',
    data: {
      labels: models,
      datasets: packs.map((p,i) => ({
        label: p,
        data: models.map(m => { const s=sparse.find(x=>x.model===m&&x.pack===p); return s?s.avg_duration:0; }),
        borderRadius: 3,
      }))
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {title:{display:true,text:'Average seconds per scenario (sparse)'}},
      scales: {x:{beginAtZero:true,title:{display:true,text:'Seconds'}}}
    }
  });
})();

// Chart 5: Root causes
(function(){
  const causes = {};
  REVIEWS.forEach(r => { causes[r.root_cause_category] = (causes[r.root_cause_category]||0)+1; });
  const labels = Object.keys(causes).sort((a,b)=>causes[b]-causes[a]);
  new Chart(document.getElementById('chart-causes'), {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{data:labels.map(l=>causes[l]),backgroundColor:['#c0392b','#d97706','#2563eb','#7c3aed','#059669','#6b7280']}]
    },
    options: {responsive:true,plugins:{title:{display:true,text:'Evaluator root-cause categories'}}}
  });
})();

// Scorecard table
function renderScorecard(){
  const fp=document.getElementById('filter-pack').value;
  const fl=document.getElementById('filter-lane').value;
  const fm=document.getElementById('filter-model').value;
  let data=SCORECARD;
  if(fp)data=data.filter(s=>s.pack===fp);
  if(fl)data=data.filter(s=>s.lane===fl);
  if(fm)data=data.filter(s=>s.model===fm);
  let h='<table><thead><tr><th>Model</th><th>Pack</th><th>Lane</th><th class="num">Total</th><th class="num">Pub</th><th class="num">Hid</th><th class="num">FG</th><th class="num">FG%</th><th class="num">Speed</th></tr></thead><tbody>';
  data.forEach(s=>{
    const cls=s.fg_rate>25?'fg':(s.fg_rate===0?'hp':'');
    h+='<tr><td>'+s.model+'</td><td>'+s.pack+'</td><td>'+s.lane+'</td><td class="num">'+s.total+'</td><td class="num">'+s.pub_pass+'</td><td class="num">'+s.hid_pass+'</td><td class="num '+cls+'">'+s.false_green+'</td><td class="num '+cls+'">'+s.fg_rate+'%</td><td class="num">'+s.avg_duration+'s</td></tr>';
  });
  h+='</tbody></table>';
  document.getElementById('scorecard-table').innerHTML=h;
}

function populateFilters(){
  const packs=[...new Set(SCORECARD.map(s=>s.pack))].sort();
  const lanes=[...new Set(SCORECARD.map(s=>s.lane))].sort();
  const models=[...new Set(SCORECARD.map(s=>s.model))].sort();
  const fp=document.getElementById('filter-pack');
  packs.forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=p;fp.appendChild(o);});
  const fl=document.getElementById('filter-lane');
  lanes.forEach(l=>{const o=document.createElement('option');o.value=l;o.textContent=l;fl.appendChild(o);});
  const fm=document.getElementById('filter-model');
  models.forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;fm.appendChild(o);});
}

// Heatmap
function renderHeatmap(){
  const scenarios=Object.keys(HEATMAP).sort();
  const models=[...new Set(Object.values(HEATMAP).flatMap(m=>Object.keys(m)))].sort();
  let h='<div style="overflow-x:auto"><table><thead><tr><th>Scenario</th>';
  models.forEach(m=>{h+='<th>'+m+'</th>';});
  h+='</tr></thead><tbody>';
  scenarios.forEach(s=>{
    h+='<tr><td style="font-size:0.72rem;white-space:nowrap">'+s+'</td>';
    models.forEach(m=>{
      const v=HEATMAP[s]&&HEATMAP[s][m];
      if(v==='hidden_pass')h+='<td class="heatmap-cell hp">✓</td>';
      else if(v==='false_green')h+='<td class="heatmap-cell fg">✗</td>';
      else if(v==='public_red')h+='<td class="heatmap-cell pr">—</td>';
      else h+='<td></td>';
    });
    h+='</tr>';
  });
  h+='</tbody></table></div>';
  document.getElementById('heatmap').innerHTML=h;
}

populateFilters();
renderScorecard();
renderHeatmap();
['filter-pack','filter-lane','filter-model'].forEach(id=>{
  document.getElementById(id).addEventListener('change',renderScorecard);
});
</script>
</body>
</html>
"""


def generate(data_root: Path, out_path: Path) -> None:
    runs = collect_all_runs(data_root)
    reviews = collect_evaluator_reviews(data_root)
    if not runs:
        print("No runs found. Nothing to generate.")
        return

    scorecard = build_scorecard(runs)
    passk = build_laguna_passk(runs)
    heatmap = build_scenario_matrix(runs)

    reviews_data = [{
        "root_cause_category": r.get("root_cause_category", ""),
        "confidence": r.get("confidence", 0),
        "severity": r.get("severity", ""),
        "patch_quality": r.get("patch_quality"),
    } for r in reviews]

    html = HTML_TEMPLATE
    html = html.replace("__SCORECARD_JSON__", _safe_json(scorecard))
    html = html.replace("__PASSK_JSON__", _safe_json(passk))
    html = html.replace("__REVIEWS_JSON__", _safe_json(reviews_data))
    html = html.replace("__HEATMAP_JSON__", _safe_json(heatmap))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated {out_path} ({len(runs)} runs, {len(scorecard)} scorecard entries, {len(reviews)} reviews)")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate gallery HTML with charts from SQLite DBs.")
    parser.add_argument("--data-root", default="data/matrix", help="Root directory to scan for SQLite DBs.")
    parser.add_argument("--out", default="reports/gallery.html", help="Output HTML path.")
    args = parser.parse_args(argv)

    generate(Path(args.data_root), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
