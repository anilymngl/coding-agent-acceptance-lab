# Repository Rename Checklist

Completed repository name: `coding-agent-acceptance-lab`

Use this checklist after `release/open-source-v1` is reviewed and merged.

## GitHub UI

1. Open GitHub repository settings.
2. Rename `anilymngl/north-mini-test` to `anilymngl/coding-agent-acceptance-lab`.
3. Confirm GitHub redirect behavior from the old name.

## Local Remote

```bash
git remote set-url origin https://github.com/anilymngl/coding-agent-acceptance-lab.git
git remote -v
git fetch --all --prune
```

## Replacement Inventory

Run:

```bash
rg -n 'north-mini-test|anilymngl/north-mini-test|github\\.io/north-mini-test' . \
  --glob '!.git/**' \
  --glob '!.venv/**' \
  --glob '!data/matrix/**' \
  --glob '!runs/**'
```

Classify each occurrence before editing:

- current repository identity
- historical project origin
- experiment name
- snapshot/provenance name
- URL
- local path
- report title

Do not blindly replace historical experiment identifiers.

## Current Inventory From Release Branch

Current repository identity:

- `reports/release-continuation-state.md` records the current remote and local worktree path.
- `reports/final-public-release-audit.md` records the current remote.
- `reports/audit-snapshots/final-public-release-audit-pre-data.md` preserves the pre-data audit remote.
- `publishables/harness-built-target.html` footer shows the current repository.
- `scripts/build_scenario_catalog.py` generates the current repository footer in `publishables/scenario-catalog.html`.
- `pyproject.toml` and `uv.lock` represented the current package identity and should use `coding-agent-acceptance-lab` after cleanup.

Historical project origin or archived provenance:

- `publishables/archive/*` contains old repository references and stale data-availability claims retained as archived snapshots, not current public pages.
- `presentation/*` contains older deck/post URLs, including `anomalyco/north-mini-test` and misspelled historical URLs. Treat as historical unless a deck is selected for public release.

Current URL replacement candidates after GitHub rename:

- README citation/repository references.
- `CITATION.cff` `repository-code`.
- public page footers generated from `scripts/build_scenario_catalog.py`.
- workflow badges or Pages URLs if added later.

Do not replace:

- experiment IDs, matrix directory names, source database labels, or audit snapshot text that intentionally records historical state.

## Follow-Up Checks

- README links
- citation URL
- workflow badges
- Pages URL
- release provenance notes
- PR and comparison links
- old-name redirect caveat
