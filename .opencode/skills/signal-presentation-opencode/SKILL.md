# Signal Artifact Engine

## Philosophy

Signal is about clarity, honesty, and signal-to-noise ratio. Not about format.

**First principles:**
- Every artifact must be honest about what it knows and doesn't know
- Every claim must be tagged with its evidence status
- Every term must be defined before use
- Every artifact must be readable by its intended audience

## Real Guidelines

### 1. Truth Labels (Non-Negotiable)

Tag every claim with its evidence status:
- **Built** — implemented artifact exists
- **Observed** — seen in a run, repo, trace, review, or demo
- **Not built** — discussed or desired, but not implemented
- **Target** — planned next state
- **Recommendation** — judgment based on evidence and tradeoff

If you can't honestly tag a claim, cut it.

### 2. Define Before Use

Every page must define load-bearing terms before using them. No jargon without explanation.

**Bad:** "The trust gap is 28%."
**Good:** "The trust gap (public pass rate minus hidden pass rate) is 28%."

### 3. Evidence Tiers

State what tier of evidence you're working with:
- **Tier 1** — behavior microscope (single team, no external audit)
- **Tier 2** — comparative claims (evaluator agreement on false-greens)
- **Tier 3** — public benchmark (external audit)

Don't make Tier 3 claims from Tier 1 evidence.

### 4. Concrete Case > Generalization

One concrete example that reveals the pattern is worth three summary tables.

**Example:** The `decimal_money_rounding` byte-identical bug was more convincing than any summary statistic.

### 5. The Turn

Every presentation needs a turn: "We thought X → learned Y → now do Z."

If you have no turn, you have no presentation.

### 6. Color as Semantics

Use color consistently:
- **Green** — pass, good, success
- **Rose** — fail, false-green, broken
- **Blue** — info, neutral
- **Amber** — warning, partial
- **Gray** — missing, not-run, unknown

### 7. Multi-Page Suite

Sometimes you need 6 interconnected pages with a shared nav bar, not a single deck.

**When:** You have multiple artifact types (paper, catalog, evidence table, evaluator findings).
**How:** Shared nav bar, consistent styling, cross-link audit.

## Curated Examples

### Example 1: Research Paper

**File:** `examples/north-mini-test/paper.html`
**Purpose:** Academic-style findings
**Structure:**
- Abstract (one paragraph summary)
- Method (how we ran the experiment)
- Results (tables, per-scenario detail)
- Discussion (what it means)
- Limitations (what we can't claim)

**Key patterns:** Serif font, scrollable, truth labels on claims, evidence tier in footer.

### Example 2: System Inventory

**File:** `examples/north-mini-test/harness-built-target.html`
**Purpose:** Document what exists and what's missing
**Structure:**
- Pipeline flow diagram (left-to-right blocks with arrows)
- Component cards (what each file does, I/O, evidence)
- Not built gaps (what's missing)
- Target (what's planned next)
- Recommendations (what to do)

**Key patterns:** Data flow diagram, truth labels on every component, "Built/Observed/Not built" tags.

### Example 3: Evidence Index

**File:** `examples/north-mini-test/evidence-index.html`
**Purpose:** Raw data with visual encoding
**Structure:**
- How-to-read legend (what each column means)
- Filterable table (by pack, lane, outcome)
- Color-coded rows (green = pass, rose = false-green)

**Key patterns:** Filter controls, color semantics, data accuracy verified.

### Example 4: Evaluator Findings

**File:** `examples/north-mini-test/evaluator-findings.html`
**Purpose:** Reviewed false-greens with root causes
**Structure:**
- Glossary (what is a false-green, how reviews work)
- Summary stats (10 evaluator-agent reviews, 10 evidence-validated false-green diagnoses, shadow-fix outcomes not yet structured)
- Review cards (per-case verdict, root cause, confidence, patch quality)
- What's missing (91 unreviewed)

**Key patterns:** Glossary before content, concrete cases, evidence tier stated.

## Diagram Rules

A diagram must either replace a paragraph or reveal a relationship that a table hides. Otherwise cut it.

- One sentence headline per figure, one visual relationship, one short caption.
- One truth label per figure: **Observed**, **Interpretation**, **Study Design**, **Conceptual Model**, or **Analytic Frame**.
- Semantic colors only: green = pass, rose = false-green, amber = partial/warning, blue = neutral, gray = unknown.
- Sans-serif labels inside figures; serif captions outside.
- Max width ~720px. Self-contained inline SVG or HTML/CSS. No external chart libraries.
- Add accessible `<title>` and `<desc>` to each SVG. Print-safe CSS. No text smaller than 10px (labels 8px minimum).
- No gradients, icon soup, model logos, pie charts, donut charts, generic AI architecture diagrams, or duplicated harness diagrams.

## How to Use

1. **What's the context?** What data do you have? What's the audience?
2. **What's the purpose?** Inform, persuade, explore, archive, operate?
3. **What artifact fits?** Paper, deck, table, diagram, page, post?
4. **Apply the guidelines.** Truth labels, define terms, evidence tiers, concrete cases.
5. **Verify.** Cross-link audit, data accuracy, audience fit.
6. **Bundle.** Put in `publishables/` with README.

## Verification Checklist

### All artifacts
- [ ] Truth labels on every claim
- [ ] No unexplained jargon
- [ ] Data accuracy verified
- [ ] Evidence tier stated
- [ ] Audience fit checked

### Multi-page suite
- [ ] Cross-link audit (every page links to every other)
- [ ] Nav bar consistent
- [ ] README with table of contents

### Data-heavy artifacts
- [ ] How-to-read legend
- [ ] Color semantics consistent
- [ ] Filter controls work

### Narrative artifacts
- [ ] Turn narrative present
- [ ] Concrete case included
- [ ] Recommendation clear
- [ ] Limitations stated

## Key Insight

The artifact is not the point. The point is **clarity, honesty, and signal**.

Let the agent figure out the best format based on context. The guidelines are the compass, not the map.
