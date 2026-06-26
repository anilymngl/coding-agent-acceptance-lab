# Challenge Design

This project treats evals as curated workflow challenges, not random broken
repositories.

Each challenge should answer five concrete questions:

1. What real coding-agent behavior does this reveal?
2. What tempting wrong path should the agent avoid?
3. What evidence proves the fix works?
4. What makes the patch feel trustworthy or untrustworthy?
5. Can another person run the same task and get comparable results?

## The Public/Hidden Split

Every challenge has two layers of tests:

**Public tests** live in the workspace the model works in. The model can
read them, run them, and get feedback during its session — exactly like
normal CI. These test the obvious, visible requirement.

**Hidden tests** are injected into the workspace *after the model exits*.
The model never sees them. They test whether the implementation is actually
correct: edge cases, generalization, API contract preservation, policy
completeness.

This split is the core of the methodology. A model that satisfies the
public tests without satisfying the hidden ones is a **false-green** —
it made CI pass without fixing the underlying contract. The **trust gap**
(public pass rate minus hidden pass rate) is the headline metric because
it directly measures how often "looks fixed" is actually "is fixed."

Standard benchmarks score pass/fail. This harness scores
*how often you can trust a pass*.

## Pivots

The public/hidden split is the seed. The harness makes six more deliberate
turns away from pass@1-style benchmarks.

1. **Score the trust gap, not the pass rate.** A pass rate tells you whether
   CI went green. It does not tell you whether the contract is fixed. The
   headline metric is public pass rate minus hidden pass rate, because that
   measures how often "looks fixed" is actually "is fixed." A model at 95%
   public and 54% hidden is not a good model with a few edge bugs. It is a
   model that ships confident wrong patches nearly half the time.

2. **Make the evaluator an agent, not a classifier.** The evaluator is not a
   prompt that asks a model to grade a diff. It gets a workbench: the seed
   repo, the model-patched repo with hidden tests, and a scratch `shadow_repo`
   it can edit. It reproduces the failure, forms a contract hypothesis, and
   optionally writes a better fix to confirm its judgment before scoring. A
   verdict backed by a shadow fix that passes every hidden test is a different
   kind of evidence than a verdict backed by vibes.

3. **Validate evidence as exact substrings.** Every quote in an evaluator
   review must appear verbatim in the evaluation packet. Pydantic checks the
   schema; the harness checks the quotes. Invent a quote and validation fails,
   falling back to a deterministic summary. The evaluator cannot hallucinate
   its way to confidence.

4. **Count false-greens and weight by severity.** The false-green rate —
   public green and hidden red, as a share of public green — is the number
   that changes how you deploy, not accuracy. Each scenario carries a risk
   area and impact weight, so a missed money contract counts more than a
   missed doc sync.

5. **Measure value per review hour, not just success.** The maintenance pack
   runs three attempts per task and reports accepted patches per review hour.
   A model that needs three tries to land a clean 8-line patch is not the same
   value as one that does it in one try, even if both eventually pass.

6. **Produce a deployment policy, not a leaderboard rank.** The output is a
   partition: use autonomously here, gate with hidden acceptance here, do not
   delegate here. The harness is built to produce that partition.

## Challenge Anatomy


Each challenge has:

- `pack`: a named collection, such as `ci_forensics`.
- `category`: the skill under stress, such as `environment-drift`.
- `difficulty`: human-scale difficulty, not benchmark prestige.
- `vibe`: the plain-English thing we want to learn about the model.
- `trap`: the plausible mistake the model may make.
- `expected_behavior`: what a strong agent should do.
- `success_signals`: objective or reviewable proof points.
- `failure_modes`: specific bad behaviors worth tracking.
- `rubric`: human review dimensions for the run.
- public tests: visible feedback available to the model.
- hidden tests: acceptance checks added after the agent finishes.

The generated repo is disposable. The challenge metadata is the product.

## Good Challenges

Good challenges are small enough to inspect but sharp enough to reveal judgment.

Prefer:

- one clear user-facing problem
- one realistic misleading path
- deterministic setup and tests
- hidden checks that test behavior, not exact patch text
- room for different good implementations
- a short prompt that sounds like a real engineering ticket

Avoid:

- trivia bugs
- puzzles that depend on hidden magic
- huge repos before the harness can explain failures clearly
- tasks where the only scoring signal is style preference
- tasks that require network access
- fragile timing or machine-specific behavior

## Current Pack: `ci_forensics`

`ci_forensics` tests whether a coding agent can behave like a practical engineer
when CI is red:

- read logs before editing
- reproduce the failure
- separate product bugs from environment drift
- avoid test weakening
- keep the patch minimal
- tell the truth about what passed

The first four challenges are deliberately compact:

- dependency boundary after an API change
- CI-only timezone behavior
- stale generated schema drift
- async file export race

They are not meant to be a leaderboard. They are meant to make model behavior
visible.

## Early Evidence That Shaped the Challenge Design

Before the breadth and depth studies, an exploratory slice contained 39 runs
of `opencode/north-mini-code-free` plus one `deepseek/deepseek-v4-pro`
control configuration.

This is historical design evidence, not the canonical result set. It helped
identify the behaviors that the later study measured more systematically.

- **False-greens followed recurrent, locally plausible strategies.** The
  agent fixed the visible input with the wrong rounding policy, redacted the
  exposed secret without handling nested values, or normalized a unit in the
  wrong API layer. The errors were not simply nonsense; the visible assertion
  pulled the patch toward an incomplete implementation.

- **The tool loop often looked disciplined while the contract remained
  broken.** The agent read, edited, tested, and exited without unrelated
  churn. The weakness was not necessarily tool use. The reasoning often
  stopped at "what makes this assertion pass?" rather than continuing to "what
  else must remain true?"

- **Semantic width appeared to matter.** Mechanical migrations and bounded
  maintenance tasks were easier than money rules, business calendars,
  security completeness, and state invariants. The early evidence suggested
  that difficulty was not explained by model size alone; it also depended on
  how much of the real contract was visible in the failing test.

These observations motivated the hidden-acceptance design and the later
separation between public-green patches and accepted patches.

The current canonical analysis is the public technical report in
[publishables/paper.html](../publishables/paper.html), backed by the release
data in [data/releases/v1/](../data/releases/v1/).
