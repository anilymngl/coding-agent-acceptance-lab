# Matrix Cell Recovery: Timeouts and Stalls

## When to use this

A matrix cell has rows with `opencode_exit_code = 124` (timeout). These are
runtime failures — the model never produced output, or the process was killed.
They are not semantic results. You want to retry them without re-running
successful rows.

## Step 1: Diagnose

Check which cells have timeouts and what kind:

```bash
uv run python -c "
import sqlite3, glob

for db_path in sorted(glob.glob('data/matrix/*/*/*.sqlite')):
    db = sqlite3.connect(db_path)
    timeouts = db.execute(
        'SELECT scenario, duration_seconds FROM runs WHERE opencode_exit_code = 124'
    ).fetchall()
    if timeouts:
        print(f'{db_path}')
        for t in timeouts:
            print(f'  {t[0]:40s} {t[1]:.0f}s')
    db.close()
"
```

- **300s** = `first_output_timeout` hit. Model never produced stdout. Likely
  rate limiting, cold start, or API stall.
- **900s** = full `timeout` hit. Model ran but didn't finish. Likely a hard
  scenario or the model got stuck in a loop.

## Step 2: Bump the timeout (if needed)

Edit the matrix config JSON. Find the model's `first_output_timeout` and
increase it. Example: 300 → 600.

```json
{
  "alias": "north-mini",
  "first_output_timeout": 600
}
```

If the timeouts are 900s (full timeout), bump `timeout` instead: 900 → 1800.

## Step 3: Delete timeout rows

```bash
uv run python -c "
import sqlite3
db = sqlite3.connect('data/matrix/<matrix-id>/<model>/<pack>-<lane>.sqlite')
deleted = db.execute('DELETE FROM runs WHERE opencode_exit_code = 124').rowcount
db.commit()
print(f'Deleted {deleted} timeout rows')
db.close()
"
```

## Step 4: Rerun with --resume

```bash
uv run ci-vibe-matrix run \
  configs/matrix/<config>.json \
  --resume \
  --only-model <model-alias> \
  --only-pack <pack> \
  --only-prompt-mode <lane>
```

`--resume` skips rows already in the DB (the successful ones). The deleted
timeout rows are gone, so the runner will attempt them fresh with the new
timeout.

## Step 5: Evaluate new false-greens

If the retry produced new false-green rows, run the evaluator:

```bash
uv run ci-vibe-matrix evaluate \
  configs/matrix/<config>.json \
  --only-model <model-alias> \
  --only-pack <pack> \
  --only-prompt-mode <lane>
```

## Step 6: Verify

```bash
uv run ci-vibe-matrix status configs/matrix/<config>.json
```

All cells should show `complete` with no timeout rows.

## Common causes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| All rows in a cell timeout at 300s | Rate limiting (free API tier) | Bump `first_output_timeout` to 600, wait for rate limit to clear |
| One row times out at 900s | Hard scenario, model stuck in loop | Bump `timeout` to 1800, or accept as genuine capability limit |
| Intermittent timeouts across cells | API instability, cold starts | Retry with same timeout, usually resolves |
| All rows timeout for one model only | Model-specific API issue | Check provider status, wait, retry |

## What this is NOT

This is not a retry for semantic failures (false-greens, public-reds). Those
are real results. Only retry rows where `opencode_exit_code = 124` — the
harness killed the run before the model could produce meaningful output.
