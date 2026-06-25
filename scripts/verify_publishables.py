#!/usr/bin/env python3
import json
import os
import re
import sys
from html.parser import HTMLParser

# Define paths relative to repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHABLES_DIR = os.path.join(REPO_ROOT, "publishables")

class PublishablesParser(HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.links = []
        self.ids = set()
        self.metrics = {}
        self.current_metric_name = None
        self.current_metric_data = ""
        self.text_content = []
        self.is_redirect = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Track element IDs and anchor names for fragment resolution
        if "id" in attrs_dict:
            self.ids.add(attrs_dict["id"])
        if tag == "a" and "name" in attrs_dict:
            self.ids.add(attrs_dict["name"])
            
        # Collect hyperlinks
        if tag == "a" and "href" in attrs_dict:
            self.links.append((self.filename, attrs_dict["href"]))
            
        # Collect data-metric attributes
        if "data-metric" in attrs_dict:
            self.current_metric_name = attrs_dict["data-metric"]
            self.current_metric_data = ""

        # Detect meta refresh redirects
        if tag == "meta" and attrs_dict.get("http-equiv") == "refresh":
            self.is_redirect = True

    def handle_data(self, data):
        self.text_content.append(data)
        if self.current_metric_name is not None:
            self.current_metric_data += data

    def handle_endtag(self, tag):
        if self.current_metric_name is not None:
            # We assume metric elements are simple leaf nodes containing numbers
            self.metrics[self.current_metric_name] = self.current_metric_data.strip()
            self.current_metric_name = None

def verify_dataset_integrity():
    print("--- Verifying Dataset Integrity ---")
    cells_path = os.path.join(PUBLISHABLES_DIR, "data", "study-b-cells.json")
    if not os.path.exists(cells_path):
        print(f"Error: {cells_path} does not exist.")
        sys.exit(1)
        
    with open(cells_path, "r") as f:
        cells = json.load(f)
        
    # Check exactly 132 cells
    if len(cells) != 132:
        print(f"Error: Expected 132 cells, found {len(cells)}")
        sys.exit(1)
        
    keys = set()
    total_retained = 0
    total_planned = 0
    total_false_greens = 0
    missing_attempts = 0
    missing_cells = []
    
    for i, cell in enumerate(cells):
        # Unique key check
        key = (cell["sc"], cell["pack"], cell["model"], cell["lane"])
        if key in keys:
            print(f"Error: Duplicate key {key} in study-b-cells.json")
            sys.exit(1)
        keys.add(key)
        
        # Numeric bounds checking
        r = cell["r"]
        p = cell["p"]
        h = cell["h"]
        fg = cell["fg"]
        
        if not (0 <= h <= r):
            print(f"Error at index {i}: h ({h}) must be between 0 and r ({r})")
            sys.exit(1)
            
        if not (0 <= fg <= r):
            print(f"Error at index {i}: fg ({fg}) must be between 0 and r ({r})")
            sys.exit(1)
            
        if h + fg > r:
            print(f"Error at index {i}: h + fg ({h + fg}) exceeds retained attempts r ({r})")
            sys.exit(1)
            
        total_retained += r
        
        # Planned attempts sum (planned is 3 for all cells)
        total_planned += 3
        total_false_greens += fg
        
        # Missing attempts check
        if r < 3:
            missing_attempts += (3 - r)
            missing_cells.append(cell)
            
        # Gateway logic verification
        if cell["model"] == "north-mini":
            if cell["pack"] == "product_workflows":
                if cell["gw"] != "or":
                    print(f"Error: North Mini product cell {key} must have gw='or'")
                    sys.exit(1)
            else:
                if cell["gw"] != "zen":
                    print(f"Error: North Mini non-product cell {key} must have gw='zen'")
                    sys.exit(1)
                    
    # Validate sums
    if total_retained != 391:
        print(f"Error: Retained attempts sum is {total_retained}, expected 391")
        sys.exit(1)
        
    if total_planned != 396:
        print(f"Error: Planned attempts sum is {total_planned}, expected 396")
        sys.exit(1)
        
    if total_false_greens != 101:
        print(f"Error: False greens sum is {total_false_greens}, expected 101")
        sys.exit(1)
        
    if missing_attempts != 5:
        print(f"Error: Expected exactly 5 missing attempts, found {missing_attempts}")
        sys.exit(1)
        
    for cell in missing_cells:
        if not (cell["model"] == "north-mini" and cell["pack"] == "maintenance_value" and cell["lane"] == "cv"):
            print(f"Error: Missing attempt in cell {cell} does not belong to North Mini maintenance CV.")
            sys.exit(1)
            
    print("Dataset integrity verified successfully!")
    return cells

def verify_metric_integrity(cells):
    print("--- Verifying Metric Integrity ---")
    summary_path = os.path.join(PUBLISHABLES_DIR, "data", "study-b-summary.json")
    if not os.path.exists(summary_path):
        print(f"Error: {summary_path} does not exist.")
        sys.exit(1)
        
    with open(summary_path, "r") as f:
        summary = json.load(f)
        
    # Check top-level summary counts
    sum_data = summary["summary"]
    if sum_data["total_cells"] != 132:
        print(f"Error: summary total_cells is {sum_data['total_cells']}, expected 132")
        sys.exit(1)
    if sum_data["planned_attempts"] != 396:
        print(f"Error: summary planned_attempts is {sum_data['planned_attempts']}, expected 396")
        sys.exit(1)
    if sum_data["retained_attempts"] != 391:
        print(f"Error: summary retained_attempts is {sum_data['retained_attempts']}, expected 391")
        sys.exit(1)
    if sum_data["false_greens"] != 101:
        print(f"Error: summary false_greens is {sum_data['false_greens']}, expected 101")
        sys.exit(1)
        
    # Recalculate metrics per model/lane
    # Map model names to their categories
    models = ["laguna-xs2", "north-mini"]
    lanes = ["sparse", "cv"]
    
    for m in models:
        for l in lanes:
            # filter cells
            subset = [c for c in cells if c["model"] == m and c["lane"] == l]
            runs = sum(c["r"] for c in subset)
            hidden_pass = sum(c["h"] for c in subset)
            false_green = sum(c["fg"] for c in subset)
            public_pass = hidden_pass + false_green
            
            # any_of_three is the count of scenarios where h > 0
            # all_of_three is the count of scenarios where h == r and r == 3
            any_of_three = sum(1 for c in subset if c["h"] > 0)
            all_of_three = sum(1 for c in subset if c["h"] == c["r"] and c["r"] == 3)
            
            expected_fg_rate = round(false_green / public_pass, 4) if public_pass > 0 else 0.0
            
            # Check summary matches
            m_sum = summary["models"][m][l]
            if m_sum["runs"] != runs:
                print(f"Error: Runs mismatch for {m}/{l}. Recalc={runs}, Summary={m_sum['runs']}")
                sys.exit(1)
            if m_sum["hidden"] != hidden_pass:
                print(f"Error: Hidden mismatch for {m}/{l}. Recalc={hidden_pass}, Summary={m_sum['hidden']}")
                sys.exit(1)
            if m_sum["false_green"] != false_green:
                print(f"Error: False green mismatch for {m}/{l}. Recalc={false_green}, Summary={m_sum['false_green']}")
                sys.exit(1)
            if abs(m_sum["false_green_rate"] - expected_fg_rate) > 0.0001:
                print(f"Error: FG rate mismatch for {m}/{l}. Recalc={expected_fg_rate}, Summary={m_sum['false_green_rate']}")
                sys.exit(1)
            if m_sum["any_of_three_success"] != any_of_three:
                print(f"Error: Any-of-three mismatch for {m}/{l}. Recalc={any_of_three}, Summary={m_sum['any_of_three_success']}")
                sys.exit(1)
            if m_sum["all_of_three_reliability"] != all_of_three:
                print(f"Error: All-of-three mismatch for {m}/{l}. Recalc={all_of_three}, Summary={m_sum['all_of_three_reliability']}")
                sys.exit(1)
                
    print("Metric integrity verified successfully!")

def verify_html_integrity():
    print("--- Verifying HTML and Hyperlinks ---")
    html_files = [
        "index.html",
        "paper.html",
        "paper_v2.html",
        "evidence-index.html",
        "evaluator-findings.html",
        "harness-built-target.html",
        "scenario-catalog.html"
    ]
    
    parsed_files = {}
    
    # Parse all HTML files
    for filename in html_files:
        filepath = os.path.join(PUBLISHABLES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Error: HTML file {filepath} is missing!")
            sys.exit(1)
            
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        parser = PublishablesParser(filename)
        parser.feed(content)
        parsed_files[filename] = parser
        
    # Check meta-refresh in paper_v2.html
    if not parsed_files["paper_v2.html"].is_redirect:
        print("Error: paper_v2.html does not redirect to paper.html via meta-refresh")
        sys.exit(1)
        
    # Validate data-metric tags in paper.html
    paper_metrics = parsed_files["paper.html"].metrics
    expected_metrics = {
        "study_b.retained_attempts": "391",
        "study_b.planned_attempts": "396",
        "study_b.cell_count": "132",
        "study_b.false_greens": "101",
        "study_b.unreviewed_false_greens": "91"
    }
    
    for key, expected_val in expected_metrics.items():
        if key not in paper_metrics:
            print(f"Error: data-metric '{key}' is missing in paper.html")
            sys.exit(1)
        if paper_metrics[key] != expected_val:
            print(f"Error: data-metric '{key}' value mismatch. Expected '{expected_val}', found '{paper_metrics[key]}'")
            sys.exit(1)
            
    print("HTML data-metrics checked and match expected totals.")

    # Validate hyperlinks and anchors
    all_links = []
    for parser in parsed_files.values():
        all_links.extend(parser.links)
        
    for source_file, href in all_links:
        # Ignore external links
        if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
            continue
            
        # Parse link target
        target_parts = href.split("#")
        target_path = target_parts[0]
        fragment = target_parts[1] if len(target_parts) > 1 else None
        
        # If target path is empty, it refers to the same file
        target_file = target_path if target_path else source_file
        
        # Check no link targets live inside archive/
        if "archive/" in target_file:
            print(f"Error: Link '{href}' in {source_file} points directly to the archive.")
            sys.exit(1)
            
        # Verify target file exists
        if target_file.startswith("data/"):
            # check data JSON file exists
            json_file = os.path.join(PUBLISHABLES_DIR, target_file)
            if not os.path.exists(json_file):
                print(f"Error: Link '{href}' in {source_file} points to missing file '{target_file}'")
                sys.exit(1)
        else:
            if target_file not in html_files:
                print(f"Error: Link '{href}' in {source_file} points to unregistered file '{target_file}'")
                sys.exit(1)
                
            # Verify fragment anchor if specified
            if fragment:
                target_parser = parsed_files[target_file]
                if fragment not in target_parser.ids:
                    print(f"Error: Link '{href}' in {source_file} points to missing anchor ID '{fragment}' in target {target_file}")
                    sys.exit(1)
                    
    print("All internal hyperlinks and fragment anchors resolved successfully!")
    return parsed_files

def verify_stale_claims(parsed_files):
    print("--- Verifying No Stale Claims ---")
    
    # We specify forbidden phrases as regular expressions to check exact stale claim patterns
    forbidden_patterns = [
        (re.compile(r"49\s+unreviewed", re.IGNORECASE), "49 unreviewed"),
        (re.compile(r"59\s+false-green", re.IGNORECASE), "59 false-greens"),
        (re.compile(r"239\s+run", re.IGNORECASE), "239 runs"),
        (re.compile(r"same\s+architecture", re.IGNORECASE), "same architecture (should be similar architecture class)"),
        (re.compile(r"wall\s+they\s+cannot\s+climb", re.IGNORECASE), "wall they cannot climb"),
        (re.compile(r"product\s+workflows\s+resist\s+everything", re.IGNORECASE), "product workflows resist everything"),
        (re.compile(r"v11\.html", re.IGNORECASE), "v11.html"),
        (re.compile(r"never\s+sees\s+original\s+source", re.IGNORECASE), "never sees original source"),
        (re.compile(r"cannot\s+make\s+things\s+up", re.IGNORECASE), "cannot make things up"),
        (re.compile(r"Laguna\s+matrix\s+integrity\s+not\s+yet\s+run", re.IGNORECASE), "Laguna matrix integrity not yet run")
    ]
    
    failed = False
    for filename, parser in parsed_files.items():
        combined_text = " ".join(parser.text_content)
        for pattern, desc in forbidden_patterns:
            if pattern.search(combined_text):
                print(f"Error: Stale claim found in {filename}: '{desc}'")
                failed = True
                
    if failed:
        sys.exit(1)
        
    print("Stale-claim check passed successfully!")

def main():
    print("Starting Publishables Verification Suite...")
    cells = verify_dataset_integrity()
    verify_metric_integrity(cells)
    parsed_files = verify_html_integrity()
    verify_stale_claims(parsed_files)
    print("\nSUCCESS: All verification checks passed!")

if __name__ == "__main__":
    main()
