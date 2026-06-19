# Ad-Hoc Challenges

Standalone challenge directories for manual, free-form coding agent evaluation.

Each subdirectory is a self-contained challenge that can be:

1. **Dropped into any isolated environment** for manual testing against any agent.
2. **Run through the automated pipeline** — challenges are also registered in
   `ci_vibe_lab/scenarios.py` and work with `ci_vibe_lab.runner`.

## Manual Testing Workflow

```bash
# 1. Copy the workspace to an isolated directory
cp -r challenges/<challenge>/workspace /tmp/<challenge>
cd /tmp/<challenge>

# 2. Verify the challenge starts red
python -m unittest discover -s tests -v

# 3. Give the agent the prompt from prompt.txt and let it work

# 4. After the agent finishes, inject the hidden test
cp challenges/<challenge>/hidden/test_*_hidden.py /tmp/<challenge>/tests/

# 5. Run tests again — this is the real eval
python -m unittest discover -s tests -v
```

## Automated Pipeline

All challenges here are also registered in `ci_vibe_lab/scenarios.py`. To run
through the harness:

```bash
uv run python -m ci_vibe_lab.runner run \
  --challenge metric_semantic_mismatch \
  --model "provider/model" \
  --auto-approve
```

## Directory Structure

Each challenge follows this layout:

```
<challenge_name>/
├── CHALLENGE.md              # Full challenge card, metadata, and eval rubric
├── prompt.txt                # Copy-paste prompt for the agent
├── workspace/                # The files the agent sees
│   ├── README.md
│   ├── ci.log
│   ├── app/
│   └── tests/
└── hidden/
    └── test_*_hidden.py      # Hidden acceptance test
```

## Relationship to the Automated Harness

The automated pipeline in `ci_vibe_lab/` captures pass/fail results and patches.
The standalone challenge directories here add:

- **CHALLENGE.md** with rich eval rubrics, behavioral signals, and trap analysis
- **Workspace isolation** so you can test agents outside the OpenCode CLI
- **Free-form evaluation** beyond binary pass/fail
