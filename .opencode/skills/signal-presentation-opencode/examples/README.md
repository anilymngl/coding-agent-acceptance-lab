# Signal Artifact Examples

Four curated examples showing the range of what Signal can produce.

## paper_v2.html — Research Paper

**Purpose:** Academic-style findings with full methodology
**When to use:** You have experimental data and want to make claims
**Key patterns:**
- Serif font, scrollable, formal structure
- Truth labels on every claim (Observed, Not built, Recommendation)
- Evidence tier in footer (Tier 1 — behavior microscope)
- Concrete case (decimal_money_rounding byte-identical bug)
- Turn narrative (pass@1 had a gap → pass@3 erased it)

**Structure:**
1. Abstract (one paragraph summary)
2. Method (how we ran the experiment)
3. Results (tables, per-scenario detail)
4. Discussion (what it means)
5. Limitations (what we can't claim)

---

## harness-built-target.html — System Inventory

**Purpose:** Document what exists, what's missing, what's planned
**When to use:** You have a system and want to show its state
**Key patterns:**
- Data flow diagram (left-to-right blocks with arrows)
- Component cards (what each file does, I/O, evidence)
- Truth labels on every component (Built, Observed, Not built)
- Gap analysis (what's missing)
- Target (what's planned next)

**Structure:**
1. Pipeline flow diagram
2. Component detail cards
3. Not built gaps
4. Target (next states)
5. Recommendations

---

## evidence-index.html — Evidence Index

**Purpose:** Raw data with visual encoding and filtering
**When to use:** You have a lot of data points and want to make them explorable
**Key patterns:**
- How-to-read legend (what each column means)
- Filterable table (by pack, lane, outcome)
- Color-coded rows (green = pass, rose = false-green)
- Data accuracy verified against source

**Structure:**
1. How-to-read legend
2. Filter controls
3. Data table
4. Footer with data source

---

## evaluator-findings.html — Evaluator Findings

**Purpose:** Reviewed false-greens with root causes
**When to use:** You have reviewed cases and want to show the findings
**Key patterns:**
- Glossary before content (what is a false-green, how reviews work)
- Summary stats (10 reviews, 10/10 confirmed, mean confidence 0.95)
- Review cards (per-case verdict, root cause, confidence, patch quality)
- What's missing (49 unreviewed)

**Structure:**
1. Glossary (define load-bearing terms)
2. Summary stats
3. Review cards (one per case)
4. What's missing

---

## How to Use These Examples

1. **Identify your purpose:** Inform, persuade, explore, archive, operate?
2. **Pick the closest example:** Which artifact type matches your need?
3. **Adapt the structure:** Keep the patterns that fit, drop the rest.
4. **Apply the guidelines:** Truth labels, define terms, evidence tiers, concrete cases.
5. **Verify:** Cross-link audit, data accuracy, audience fit.

## Key Insight

These examples show the range, not the rules. The guidelines in SKILL.md are the compass. The examples are the map.

If you need something different, build it. Just apply the first principles.
