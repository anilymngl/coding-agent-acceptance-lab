#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path
from html import escape

# Ensure we can import from the workspace root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ci_vibe_lab.scenarios import SCENARIOS

REPRESENTATIVE_SCENARIOS = {
    "stale_generated_schema",
    "dependency_api_change",
    "decimal_money_rounding",
    "generated_openapi_refresh",
    "adapter_field_rename",
    "batch_splitter_utility",
    "audit_log_redaction",
    "inventory_reservation_idempotency",
    "support_sla_business_hours",
}

def parse_test_code(code_str):
    """
    Simple parser to extract test methods and their assertions
    """
    methods = []
    lines = code_str.splitlines()
    current_method = None
    current_body = []
    
    for line in lines:
        match = re.match(r"^\s+def\s+(test_[a-zA-Z0-9_]+)\(", line)
        if match:
            if current_method:
                methods.append((current_method, "\n".join(current_body)))
            current_method = match.group(1)
            current_body = [line]
        elif current_method:
            indent_match = re.match(r"^(\s*)", line)
            indent = len(indent_match.group(1)) if indent_match else 0
            if line.strip() and indent < 8 and not line.strip().startswith("#"):
                methods.append((current_method, "\n".join(current_body)))
                current_method = None
                current_body = []
            else:
                current_body.append(line)
                
    if current_method:
        methods.append((current_method, "\n".join(current_body)))
        
    parsed_methods = []
    for name, body in methods:
        asserts = []
        for bline in body.splitlines():
            if "self.assert" in bline:
                asserts.append(bline.strip())
        parsed_methods.append({
            "name": name,
            "assertions": asserts,
            "body": body
        })
    return parsed_methods

def build_catalog():
    # Load Study B cells for observed outcomes
    cells_path = REPO_ROOT / "publishables" / "data" / "study-b-cells.json"
    with open(cells_path, "r", encoding="utf-8") as f:
        cells = json.load(f)

    # Gather all unique categories for filtering
    categories = sorted(list({sc.category for sc in SCENARIOS.values()}))

    # Generate scenario cards HTML
    cards_html = []
    
    for sc_id, sc in sorted(SCENARIOS.items(), key=lambda item: (item[1].pack, item[0])):
        is_rep = "true" if sc_id in REPRESENTATIVE_SCENARIOS else "false"
        
        # 1. Parse visible test name and assertion
        test_file = ""
        visible_test_name = "n/a"
        visible_assertion = "n/a"
        for path, content in sc.files.items():
            if path.startswith("tests/") and path.endswith(".py"):
                test_file = path
                parsed = parse_test_code(content)
                if parsed:
                    visible_test_name = parsed[0]["name"]
                    if parsed[0]["assertions"]:
                        visible_assertion = parsed[0]["assertions"][0]
                break

        # 2. Parse hidden test name and assertion
        hidden_test_name = "n/a"
        hidden_assertion = "n/a"
        parsed_hidden = parse_test_code(sc.hidden_test)
        if parsed_hidden:
            hidden_test_name = parsed_hidden[0]["name"]
            if parsed_hidden[0]["assertions"]:
                hidden_assertion = parsed_hidden[0]["assertions"][0]

        # 3. Source files list
        source_files = []
        for path in sc.files.keys():
            if (path != "ci.log" and 
                path != "README.md" and 
                not path.startswith("tests/") and 
                path != "app/__init__.py"):
                source_files.append(path)
        source_files_html = ", ".join(f"<code>{escape(sf)}</code>" for sf in source_files)

        # 4. expected behavior, success signals, failure modes
        expected_behavior_bullets = "\n".join(f"<li>{escape(item)}</li>" for item in sc.expected_behavior)
        success_signals_bullets = "\n".join(f"<li>{escape(item)}</li>" for item in sc.success_signals)
        failure_modes_bullets = "\n".join(f"<li>{escape(item)}</li>" for item in sc.failure_modes)

        # 5. ci.log log excerpt
        log_excerpt_html = '<p class="no-log">No CI log excerpt defined.</p>'
        if "ci.log" in sc.files:
            log_content = sc.files["ci.log"].strip()
            log_excerpt_html = f'<pre class="log-box"><code>{escape(log_content)}</code></pre>'

        # 6. Study B outcomes table
        sc_cells = [c for c in cells if c["sc"] == sc_id]
        def find_cell(model, lane):
            for c in sc_cells:
                if c["model"] == model and c["lane"] == lane:
                    return c
            return None

        laguna_sparse = find_cell("laguna-xs2", "sparse")
        laguna_cv = find_cell("laguna-xs2", "cv")
        north_sparse = find_cell("north-mini", "sparse")
        north_cv = find_cell("north-mini", "cv")

        def render_row(label, cell):
            if not cell:
                return f"""
                <div class="outcome-row">
                    <span class="outcome-label">{label}</span>
                    <span class="outcome-symbols text-muted">n/a</span>
                    <span class="outcome-count text-muted">0/0</span>
                </div>"""
            h = cell["h"]
            r = cell["r"]
            symbols = []
            for _ in range(h):
                symbols.append("✓")
            for _ in range(r - h):
                symbols.append("●")
            symbols_html = " ".join(f'<span class="symbol-{"pass" if s == "✓" else "fail"}">{s}</span>' for s in symbols)
            return f"""
            <div class="outcome-row">
                <span class="outcome-label">{label}</span>
                <span class="outcome-symbols">{symbols_html}</span>
                <span class="outcome-count">{h}/{r}</span>
            </div>"""

        study_b_outcomes_html = f"""
        <div class="outcomes-block">
            <div class="outcomes-header-label">Study B Head-to-Head (Attempts Passed)</div>
            {render_row("Laguna sparse", laguna_sparse)}
            {render_row("Laguna CV", laguna_cv)}
            {render_row("North Mini sparse", north_sparse)}
            {render_row("North Mini CV", north_cv)}
        </div>"""

        # Paper link check
        paper_link_html = ""
        if sc_id in REPRESENTATIVE_SCENARIOS:
            paper_link_html = f'<a href="paper.html#representative-cases" class="paper-case-link">&rarr; Read paper case study</a>'

        card = f"""
    <!-- {sc_id} -->
    <article class="scenario-card" id="{sc_id}" data-pack="{sc.pack}" data-difficulty="{sc.difficulty}" data-category="{sc.category}" data-representative="{is_rep}">
      <details class="card-details-toggle">
        <summary class="card-header">
          <div class="card-header-main">
            <div class="card-title-row">
              <h2 class="card-title">{escape(sc.title)}</h2>
              <span class="card-meta">
                <span class="meta-tag pack-tag">{escape(sc.pack)}</span> &middot; 
                <span class="meta-tag cat-tag">{escape(sc.category)}</span> &middot; 
                <span class="diff-tag diff-{sc.difficulty}">{escape(sc.difficulty)}</span>
              </span>
            </div>
            <div class="card-id mono">{sc_id}</div>
            
            <p class="collapsed-description">{escape(sc.description)}</p>
            
            <div class="collapsed-summary-points">
              <div class="collapsed-point">
                <span class="lbl">What the agent saw</span>
                <span class="val">CI failure: {escape(visible_test_name)} ({escape(visible_assertion)})</span>
              </div>
              <div class="collapsed-point">
                <span class="lbl">The obvious fix</span>
                <span class="val">{escape(sc.trap)}</span>
              </div>
              <div class="collapsed-point">
                <span class="lbl">What the contract actually demands</span>
                <span class="val">{escape(sc.expected_behavior[0] if sc.expected_behavior else 'n/a')}</span>
              </div>
            </div>
          </div>
          <div class="inspect-action-badge">Inspect &darr;</div>
        </summary>
        
        <div class="card-content">
          <div class="content-grid">
            <!-- Left Column: Contract & Traps -->
            <div class="content-col">
              <div class="detail-section">
                <h3>What the contract actually owns</h3>
                <ul class="bullets">
                  {expected_behavior_bullets}
                </ul>
              </div>
              
              <div class="detail-section">
                <h3>What hidden acceptance checks</h3>
                <ul class="bullets">
                  {success_signals_bullets}
                </ul>
              </div>
              
              <div class="detail-section">
                <h3>What that fix misses</h3>
                <ul class="bullets">
                  {failure_modes_bullets}
                </ul>
              </div>
              
              <div class="detail-section tempting-fix-box">
                <h3>Why anyone should care</h3>
                <p>{escape(sc.trap)}</p>
              </div>
            </div>
            
            <!-- Right Column: Code & Outcomes -->
            <div class="content-col">
              <div class="detail-section">
                <h3>Visible Evidence & Logs</h3>
                {log_excerpt_html}
              </div>
              
              <div class="detail-section">
                <h3>Source Files & Tests</h3>
                <div class="code-metadata">
                  <div><strong>Failing Test File:</strong> <code class="mono">{escape(test_file)}</code></div>
                  <div><strong>Visible Test Method:</strong> <code class="mono">{escape(visible_test_name)}</code></div>
                  <div><strong>Visible Assertion:</strong> <code class="mono">{escape(visible_assertion)}</code></div>
                  <div style="margin-top:8px"><strong>Relevant Source Files:</strong> {source_files_html}</div>
                </div>
              </div>
              
              <div class="detail-section">
                <h3>Observed Study B Outcomes</h3>
                <div class="outcomes-table-container">
                  {study_b_outcomes_html}
                </div>
                <div class="evidence-links">
                  <a href="evidence-index.html#{sc_id}" class="evidence-matrix-link">&rarr; View raw evidence matrix row</a>
                  {paper_link_html}
                </div>
              </div>
            </div>
          </div>
          
          <!-- Hidden Test Source Disclosure -->
          <details class="hidden-source-disclosure">
            <summary>Show hidden test source code</summary>
            <pre class="code-block"><code class="python">{escape(sc.hidden_test)}</code></pre>
          </details>
        </div>
      </details>
    </article>"""
        cards_html.append(card)

    # Build category filters list HTML
    cat_options = [f'<option value="{c}">{c}</option>' for c in categories]

    # Load complete HTML shell
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scenario Catalog — Inspection Browser</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Inter', -apple-system, system-ui, sans-serif; background: #FAFAFA; color: #1e293b; padding: 40px 20px 80px; line-height: 1.5; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 24px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 2px; }}
  .sub {{ color: #475569; font-size: 12px; margin-bottom: 24px; }}
  .mono {{ font-family: 'SF Mono', Menlo, monospace; }}
  
  .nav-links {{ margin-bottom: 24px; font-size: 11px; }}
  .nav-links a {{ color: #2563eb; text-decoration: none; margin-right: 14px; font-weight: 600; }}
  .nav-links span {{ color: #94a3b8; margin-right: 8px; }}

  /* Controls and Filters */
  .controls-box {{ background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
  .search-row {{ display: flex; gap: 10px; margin-bottom: 12px; }}
  .search-input {{ flex: 1; padding: 8px 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 13px; font-family: inherit; }}
  .search-input:focus {{ outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,0.15); }}
  
  .filter-row {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; justify-content: space-between; font-size: 12px; }}
  .filters-left {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
  .filter-select {{ padding: 6px 10px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; font-size: 12px; cursor: pointer; }}
  .btn-action {{ padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 6px; background: white; font-size: 12px; font-weight: 600; cursor: pointer; transition: background-color 0.15s; }}
  .btn-action:hover {{ background-color: #f1f5f9; }}
  .toggle-label {{ display: flex; align-items: center; gap: 6px; cursor: pointer; font-weight: 600; color: #475569; }}
  
  /* Catalog list */
  .catalog-list {{ display: flex; flex-direction: column; gap: 14px; }}
  
  /* Card Styling */
  .scenario-card {{ background: white; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.01); transition: border-color 0.15s, box-shadow 0.15s; }}
  .scenario-card:hover {{ border-color: #cbd5e1; }}
  
  .card-details-toggle {{ width: 100%; }}
  .card-header {{ padding: 20px; cursor: pointer; list-style: none; position: relative; }}
  .card-header::-webkit-details-marker {{ display: none; }}
  
  .card-header-main {{ padding-right: 140px; }}
  .card-title-row {{ display: flex; align-items: baseline; gap: 12px; margin-bottom: 2px; flex-wrap: wrap; }}
  .card-title {{ font-size: 16px; font-weight: 800; color: #0f172a; letter-spacing: -0.01em; }}
  .card-id {{ font-size: 10px; color: #94a3b8; margin-bottom: 10px; }}
  .collapsed-description {{ font-size: 12px; color: #334155; line-height: 1.5; margin-bottom: 12px; }}
  
  /* Collapsed metadata tags */
  .meta-tag, .diff-tag {{ display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 8px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }}
  .pack-tag {{ background: #f1f5f9; color: #475569; }}
  .cat-tag {{ background: #eff6ff; color: #1e40af; }}
  .diff-tag.diff-easy {{ background: #dcfce7; color: #166534; }}
  .diff-tag.diff-medium {{ background: #fef3c7; color: #92400e; }}
  .diff-tag.diff-hard {{ background: #ffe4e6; color: #9f1239; }}
  
  /* Summary bullet list */
  .collapsed-summary-points {{ display: flex; flex-direction: column; gap: 4px; border-top: 1px solid #f1f5f9; padding-top: 10px; font-size: 11px; }}
  .collapsed-point {{ display: flex; gap: 8px; }}
  .collapsed-point .lbl {{ font-weight: 800; color: #64748b; font-size: 9px; letter-spacing: 0.05em; flex-shrink: 0; width: 170px; }}
  .collapsed-point .val {{ color: #334155; }}
  
  .inspect-action-badge {{ position: absolute; right: 20px; top: 20px; font-size: 10px; font-weight: 700; color: #2563eb; background: #eff6ff; border: 1px solid #bfdbfe; padding: 4px 10px; border-radius: 6px; }}
  
  /* Expanded details content */
  .card-content {{ padding: 0 20px 24px; border-top: 1px dotted #e2e8f0; margin-top: 4px; }}
  .content-grid {{ display: flex; gap: 24px; margin-top: 20px; }}
  .content-col {{ flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 20px; }}
  
  .detail-section h3 {{ font-size: 11px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: #64748b; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; }}
  .bullets {{ margin-left: 18px; font-size: 11.5px; color: #334155; }}
  .bullets li {{ margin-bottom: 6px; }}
  .tempting-fix-box {{ background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px 14px; font-size: 11.5px; color: #92400e; }}
  .tempting-fix-box p {{ font-weight: 500; }}
  
  /* Code and Log boxes */
  .log-box {{ background: #0f172a; color: #cbd5e1; border-radius: 8px; padding: 12px 14px; font-size: 10px; overflow-x: auto; font-family: 'SF Mono', Menlo, monospace; max-height: 160px; }}
  .no-log {{ font-size: 11px; color: #94a3b8; font-style: italic; }}
  .code-metadata {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; font-size: 11px; color: #475569; display: flex; flex-direction: column; gap: 6px; }}
  .code-metadata code {{ background: white; border: 1px solid #e2e8f0; padding: 1px 4px; border-radius: 4px; font-size: 10px; }}
  
  /* Study B Outcomes Table inside catalog */
  .outcomes-block {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; }}
  .outcomes-header-label {{ font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin-bottom: 8px; }}
  .outcome-row {{ display: flex; align-items: center; justify-content: space-between; font-size: 11px; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #f1f5f9; }}
  .outcome-row:last-child {{ margin-bottom: 0; padding-bottom: 0; border-bottom: none; }}
  .outcome-label {{ font-weight: 600; color: #334155; }}
  .outcome-symbols {{ font-family: monospace; font-size: 11px; letter-spacing: 2px; }}
  .symbol-pass {{ color: #16a34a; font-weight: bold; }}
  .symbol-fail {{ color: #cbd5e1; }}
  .outcome-count {{ font-weight: 700; color: #475569; font-size: 10px; }}
  
  .evidence-links {{ display: flex; flex-direction: column; gap: 6px; margin-top: 10px; font-size: 11px; }}
  .evidence-matrix-link, .paper-case-link {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
  .evidence-matrix-link:hover, .paper-case-link:hover {{ text-decoration: underline; }}
  
  /* Code block disclosure */
  .hidden-source-disclosure {{ margin-top: 18px; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
  .hidden-source-disclosure summary {{ font-size: 11px; font-weight: 700; color: #2563eb; cursor: pointer; margin-bottom: 8px; outline: none; }}
  .code-block {{ background: #1e293b; color: #f8fafc; border-radius: 8px; padding: 14px; font-size: 10.5px; overflow-x: auto; font-family: 'SF Mono', Menlo, monospace; max-height: 400px; }}
  
  /* Targeted state blue highlight */
  .scenario-card.is-targeted {{
    border-color: #2563eb;
    box-shadow: 0 0 12px rgba(37,99,235,0.25);
    animation: target-pulse 2s ease-out;
  }}
  @keyframes target-pulse {{
    0% {{ box-shadow: 0 0 16px rgba(37,99,235,0.5); }}
    100% {{ box-shadow: 0 0 4px rgba(37,99,235,0.05); }}
  }}

  @media (max-width: 860px) {{
    .content-grid {{ flex-direction: column; gap: 20px; }}
    .card-header-main {{ padding-right: 0; margin-top: 24px; }}
    .inspect-action-badge {{ top: 12px; right: 12px; }}
  }}
</style>
</head>
<body>
<div class="wrap">

  <h1>Scenario Catalog — Inspection Browser</h1>
  <p class="sub">Open any of the 33 tasks. Inspect what the agent saw, what fix looked tempting, what the authored contract required, what hidden acceptance checked, and how the evaluated systems behaved.</p>

  <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:11px;color:#92400e;line-height:1.5">
    <strong>Every scenario answers five questions:</strong> What looked broken? What was the obvious fix? What did that fix miss? What did the contract actually own? Why should anyone care? The page is built for the practitioner who wants to understand the mechanism behind the failure, not just count the result.
  </div>

  <div class="nav-links">
    <span>Research suite:</span>
    <a href="index.html">Home</a>
    <span>|</span>
    <a href="paper.html">Paper</a>
    <span>|</span>
    <a href="harness-built-target.html">System</a>
    <span>|</span>
    <span style="color:#333;font-weight:700">Scenarios</span>
    <span>|</span>
    <a href="evidence-index.html">Evidence</a>
    <span>|</span>
    <a href="evaluator-findings.html">Evaluator</a>
  </div>

  <!-- Controls Box -->
  <div class="controls-box">
    <div class="search-row">
      <input type="text" id="search-input" class="search-input" placeholder="Search by title, ID, contract text, or traps..." oninput="filterScenarios()">
    </div>
    <div class="filter-row">
      <div class="filters-left">
        <select id="filter-pack" class="filter-select" onchange="filterScenarios()">
          <option value="all">All Packs</option>
          <option value="ci_forensics">ci_forensics</option>
          <option value="maintenance_value">maintenance_value</option>
          <option value="product_workflows">product_workflows</option>
        </select>
        
        <select id="filter-difficulty" class="filter-select" onchange="filterScenarios()">
          <option value="all">All Difficulties</option>
          <option value="easy">easy</option>
          <option value="medium">medium</option>
          <option value="hard">hard</option>
        </select>
        
        <select id="filter-category" class="filter-select" onchange="filterScenarios()">
          <option value="all">All Categories</option>
          {chr(10).join(cat_options)}
        </select>
        
        <label class="toggle-label">
          <input type="checkbox" id="toggle-rep" onchange="filterScenarios()">
          Only representative paper cases
        </label>
      </div>
      
      <div class="filters-right">
        <button class="btn-action" onclick="toggleAllDetails(true)">Expand all</button>
        <button class="btn-action" onclick="toggleAllDetails(false)">Collapse all</button>
      </div>
    </div>
  </div>

  <!-- Catalog list -->
  <div class="catalog-list" id="catalog-list">
{chr(10).join(cards_html)}
  </div>

  <div class="foot">
    <span class="mono">github.com/anilymngl/north-mini-test</span> &middot; June 2026 &middot; Behavior microscope scenario cards
  </div>

</div>

<script>
function filterScenarios() {{
  const query = document.getElementById('search-input').value.toLowerCase().strip();
  const pack = document.getElementById('filter-pack').value;
  const diff = document.getElementById('filter-difficulty').value;
  const cat = document.getElementById('filter-category').value;
  const repOnly = document.getElementById('toggle-rep').checked;
  
  const cards = document.querySelectorAll('.scenario-card');
  cards.forEach(card => {{
    const cId = card.id;
    const cTitle = card.querySelector('.card-title').textContent.toLowerCase();
    const cDesc = card.querySelector('.collapsed-description').textContent.toLowerCase();
    const cText = card.textContent.toLowerCase();
    const cPack = card.getAttribute('data-pack');
    const cDiff = card.getAttribute('data-difficulty');
    const cCat = card.getAttribute('data-category');
    const cRep = card.getAttribute('data-representative') === 'true';
    
    const matchesSearch = !query || cId.includes(query) || cTitle.includes(query) || cDesc.includes(query) || cText.includes(query);
    const matchesPack = pack === 'all' || cPack === pack;
    const matchesDiff = diff === 'all' || cDiff === diff;
    const matchesCat = cat === 'all' || cCat === cat;
    const matchesRep = !repOnly || cRep;
    
    if (matchesSearch && matchesPack && matchesDiff && matchesCat && matchesRep) {{
      card.style.display = 'block';
    }} else {{
      card.style.display = 'none';
    }}
  }});
}}

function toggleAllDetails(open) {{
  const details = document.querySelectorAll('.card-details-toggle');
  details.forEach(d => {{
    d.open = open;
  }});
}}

// Handle direct hash navigation
function handleHash() {{
  const hash = location.hash;
  if (!hash) return;
  const id = decodeURIComponent(hash.slice(1));
  const card = document.getElementById(id);
  if (card) {{
    const details = card.querySelector('.card-details-toggle');
    if (details) details.open = true;
    
    // Clear targeted class on any previous targets
    document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('is-targeted'));
    
    requestAnimationFrame(() => {{
      card.scrollIntoView({{ block: 'start' }});
      card.classList.add('is-targeted');
    }});
  }}
}}

window.addEventListener('hashchange', handleHash);
window.addEventListener('DOMContentLoaded', handleHash);

// Helper for strings
if (!String.prototype.strip) {{
  String.prototype.strip = function() {{
    return this.replace(/^\\s+|\\s+$/g, '');
  }};
}}
</script>

</body>
</html>
"""

    output_path = REPO_ROOT / "publishables" / "scenario-catalog.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template.strip() + "\n")
    print(f"Scenario catalog generated successfully to {output_path}")

if __name__ == "__main__":
    build_catalog()
