# Challenge Design

This project treats evals as curated workflow challenges, not random broken
repositories.

Each challenge should answer five concrete questions:

1. What real coding-agent behavior does this reveal?
2. What tempting wrong path should the agent avoid?
3. What evidence proves the fix works?
4. What makes the patch feel trustworthy or untrustworthy?
5. Can another person run the same task and get comparable results?

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

