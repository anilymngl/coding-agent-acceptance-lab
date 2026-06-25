# Release Continuation State

Date: 2026-06-25

## Git Identity

- Current branch: `audit/final-public-release`
- Current `HEAD`: `b809763a97945319dc3646e04a0726706e985ab2`
- Current `origin/main`: `b809763a97945319dc3646e04a0726706e985ab2`
- Remote: `origin https://github.com/anilymngl/north-mini-test.git`
- Worktree root: local repository checkout path redacted from the public release branch.

## Branch State

- `audit/final-public-release` exists locally at `b809763a97945319dc3646e04a0726706e985ab2`.
- `audit/final-public-release` does not exist on `origin` at discovery time.
- `dev/pre-open-source-main-2026-06-25` does not exist on `origin` at discovery time.
- `dev/final-public-release-audit-2026-06-25` does not exist on `origin` at discovery time.
- `release/open-source-v1` does not exist on `origin` at discovery time.
- `42f21b8` is contained by local `audit/final-public-release`, local `main`, local `publishables-v2-matrix-update`, `origin/main`, and `origin/publishables-v2-matrix-update`.
- `6b777f4` is contained by local `audit/final-public-release`, local `main`, and `origin/main`.

## Preservation Branches

- `dev/pre-open-source-main-2026-06-25`: `b809763a97945319dc3646e04a0726706e985ab2`
- `dev/final-public-release-audit-2026-06-25`: `87319ed04df9c5f2b7658c9643666fcdbd2ad077`
- Both preservation branches were pushed to `origin`.
- No annotated snapshot tags were created.

## Audit Change Status

- Audit changes are not committed.
- Audit changes are not pushed.
- `reports/final-public-release-audit.md` exists in the working tree but is untracked at discovery time, so it does not exist in Git yet.
- Staged files: none.

## Modified Files

- `docs/model-comparison-eval-pipeline-plan-2026-06-20.md`
- `publishables/README.md`
- `publishables/evidence-index.html`
- `publishables/harness-built-target.html`
- `publishables/paper.html`
- `publishables/paper_academic.html`
- `reports/laguna-xs2-vs-north-mini-first-comparison.md`
- `reports/laguna-xs2-vs-north-mini-leaderboard.md`
- `reports/leaderboard-local-gemma4-smallest-two.md`
- `reports/leaderboard-local-gemma4-two-model.md`
- `reports/north-mini-code-evidence-pack-2026-06-20.md`
- `reports/north-mini-maintenance-value-v2-2026-06-20.md`
- `scripts/verify_publishables.py`

## Untracked Files

- `reports/final-public-release-audit.md`

This continuation report was created after the discovery commands and before branch preservation.

## Ignored Project Files Present

- `.DS_Store`
- `.archive/`
- `.opencode/.DS_Store`
- `.opencode/.gitignore`
- `.opencode/node_modules/`
- `.opencode/package-lock.json`
- `.opencode/package.json`
- `.opencode/skills/.DS_Store`
- `.opencode/skills/create-presentation/.DS_Store`
- `.opencode/skills/signal-presentation-opencode/.DS_Store`
- `.venv/`
- `app/__pycache__/`
- `ci_vibe_lab/__pycache__/`
- `data/`
- `north_mini_test.egg-info/`
- `publishables/.DS_Store`
- `runs/`
- `tests/__pycache__/`

## Discovery Commands Run

```bash
git fetch --all --prune
git status --short --branch
git branch --show-current
git remote -v
git rev-parse HEAD
git rev-parse origin/main
git log --graph --decorate --oneline --all -n 40
git branch -a --contains b809763
git branch -a --contains 42f21b8
git branch -a --contains 6b777f4
git diff --stat
git diff --cached --stat
git ls-files --others --exclude-standard
git status --ignored --short
git rev-parse --show-toplevel
git worktree list
git ls-remote --heads origin audit/final-public-release dev/pre-open-source-main-2026-06-25 dev/final-public-release-audit-2026-06-25 release/open-source-v1
```
