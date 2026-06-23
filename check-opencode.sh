#!/usr/bin/env bash
# check-opencode.sh — ultimate health check for opencode + ollama + ci-vibe eval harness
#
# Usage:
#   ./check-opencode.sh                 # clean snapshot (default, <1s)
#   ./check-opencode.sh --follow        # live tail filtered opencode.log (Ctrl-C)
#   ./check-opencode.sh --integrity     # add ci-vibe-report integrity gate per config (slow)
#   ./check-opencode.sh --deep          # add per-model spend + full matrix status tables
#   ./check-opencode.sh --quiet         # only show problems (!/✗), suppress green ✓
#   ./check-opencode.sh --raw           # unfiltered opencode.log tail (noisy)
#   ./check-opencode.sh --watch         # snapshot every 5s until Ctrl-C
#   ./check-opencode.sh --live          # active run only (tracker + matrix progress)
#   Combine freely: --quiet --watch, --live --watch, --deep --integrity, etc.
set -euo pipefail

cd "$(dirname "$0")"

LOG_DIR="$HOME/.local/share/opencode/log"
MAIN_LOG="$LOG_DIR/opencode.log"
OC_DB="$HOME/.local/share/opencode/opencode.db"
OLLAMA_API="http://127.0.0.1:11434"
MODE_INT=0; MODE_DEEP=0; MODE_QUIET=0; MODE_RAW=0; MODE_FOLLOW=0; MODE_WATCH=0; MODE_LIVE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --integrity) MODE_INT=1; shift ;;
    --deep) MODE_DEEP=1; shift ;;
    --quiet) MODE_QUIET=1; shift ;;
    --raw) MODE_RAW=1; shift ;;
    --follow|-f) MODE_FOLLOW=1; shift ;;
    --watch) MODE_WATCH=1; shift ;;
    --live) MODE_LIVE=1; shift ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "unknown: $1" >&2; exit 2 ;;
  esac
done

# ── helpers ──────────────────────────────────────────────────────────────────
C1=$'\033[1;36m'; R=$'\033[0m'; DIM=$'\033[2m'; B=$'\033[1m'
section() { printf "\n${C1}══ %s ══${R}\n" "$*"; }
ok()   { [[ "$MODE_QUIET" -eq 0 ]] && printf "  \033[32m✓${R} %s\n" "$*" || true; }
warn() { printf "  \033[33m!${R} %s\n" "$*"; }
bad()  { printf "  \033[31m✗${R} %s\n" "$*"; }
dim()  { printf "  ${DIM}%s${R}\n" "$*"; }
quiet_ok=0

# sqlite helper (readonly, no locking)
sq() { sqlite3 -readonly "$1" "$2" 2>/dev/null || echo ""; }

# pack scope (maintenance_value = 10 scenarios, ordered)
PACK_SCENARIOS="adapter_field_rename batch_splitter_utility docs_cli_sync explicit_validation_matrix fixture_schema_migration generated_openapi_refresh import_hygiene_fix logger_warn_migration regression_test_gap utcnow_timezone_migration"
PACK_SIZE=$(echo "$PACK_SCENARIOS" | wc -w | tr -d ' ')

# ── live mode guard ───────────────────────────────────────────────────────────
# In --live mode with an active agent: skip diagnostic/aggregate sections,
# show only the active run tracker and matrix progress.
SKIP_IN_LIVE=0
if [[ "$MODE_LIVE" -eq 1 ]]; then
  oc_run_check=$(pgrep -f "opencode run " 2>/dev/null || true)
  if [[ -n "$oc_run_check" ]]; then
    SKIP_IN_LIVE=1
  fi
fi
live_skip() { [[ "$SKIP_IN_LIVE" -eq 1 ]] && return 0 || return 1; }

# ── 1. ollama runtime ────────────────────────────────────────────────────────
live_skip || {
section "ollama runtime"
ollama_serve=$(pgrep -f "ollama serve" || true)
if [[ -n "$ollama_serve" ]]; then
  ver=$(curl -s --max-time 2 "$OLLAMA_API/api/version" 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("version","?"))' 2>/dev/null || echo "?")
  ok "ollama serve (pid $(echo "$ollama_serve" | head -1)) v$ver"
else
  bad "ollama serve NOT running"
fi
# reachability
if curl -s --max-time 2 "$OLLAMA_API/" >/dev/null 2>&1; then ok "API :11434 reachable"; else bad "API :11434 unreachable"; fi
}

# ── 2. loaded models (/api/ps + llama-server ports) ──────────────────────────
live_skip || {
section "loaded models"
api_ps=$(curl -s --max-time 3 "$OLLAMA_API/api/ps" 2>/dev/null || echo "")
if [[ -n "$api_ps" ]]; then
  # build pid:port map for llama-servers
  declare -A LLAMA_PORTS
  for pid in $(pgrep -f "llama-server" || true); do
    port=$(lsof -nP -iTCP -sTCP:LISTEN -a -p "$pid" 2>/dev/null | awk 'NR>1{print $9}' | sed 's/.*://' | head -1)
    LLAMA_PORTS[$pid]=${port:-?}
  done
  echo "$api_ps" | python3 -c '
import json, sys
d = json.load(sys.stdin)
models = d.get("models", [])
if not models:
    print("  \033[33m!\033[0m (no models loaded in VRAM)")
else:
    for m in models:
        name = m["model"]; sz = m["size_vram"]/1e9
        ctx = m.get("context_length", "?")
        fam = m.get("details", {}).get("family", "?")
        q = m.get("details", {}).get("quantization_level", "?")
        print(f"  \033[32m✓\033[0m {name:14} {fam:8} {q:8} vram={sz:.1f}GB ctx={ctx}")
' 2>/dev/null || warn "api/ps parse failed"
  # show llama-server processes with ports
  for pid in $(pgrep -f "llama-server" || true); do
    port=${LLAMA_PORTS[$pid]:-?}
    age=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
    mem=$(ps -o %mem= -p "$pid" 2>/dev/null | tr -d ' ')
    dim "llama-server pid=$pid port=$port age=$age mem=${mem}%"
  done
else
  bad "ollama /api/ps unreachable"
fi
}

# ── 3. installed vs config (model coverage) ──────────────────────────────────
live_skip || {
section "installed models vs config"
api_tags=$(curl -s --max-time 3 "$OLLAMA_API/api/tags" 2>/dev/null || echo "")
if [[ -n "$api_tags" ]]; then
  installed=$(echo "$api_tags" | python3 -c '
import json, sys
d = json.load(sys.stdin)
for m in d.get("models", []):
    print(m["name"])
' 2>/dev/null)

  # extract model IDs from opencode.json + all configs/matrix/*.json
  config_models=$(python3 -c '
import json, glob, os
models = set()
try:
    with open("opencode.json") as f:
        d = json.load(f)
    for prov in d.get("provider", {}).values():
        for mid in prov.get("models", {}):
            models.add(mid)
except: pass
for cfg in glob.glob("configs/matrix/*.json"):
    try:
        with open(cfg) as f:
            d = json.load(f)
        for m in d.get("models", []):
            mid = m.get("id", "").replace("ollama/", "")
            if mid: models.add(mid)
    except: pass
for m in sorted(models):
    print(m)
' 2>/dev/null)

  installed_count=$(echo "$installed" | grep -c . || true)
  dim "$installed_count model(s) installed, $(du -sh ~/.ollama/models 2>/dev/null | cut -f1) on disk"

  # MISSING: in config but not installed
  missing=0
  while IFS= read -r m; do
    [[ -z "$m" ]] && continue
    if ! echo "$installed" | grep -qx "$m"; then
      bad "MISSING: $m (referenced in config but NOT installed)"
      missing=$((missing+1))
    fi
  done <<< "$config_models"
  [[ "$missing" -eq 0 ]] && ok "all configured models are installed"

  # show installed gemma4/qwen models for context
  if [[ "$MODE_DEEP" -eq 1 ]]; then
    echo "$api_tags" | python3 -c '
import json, sys
d = json.load(sys.stdin)
for m in d.get("models", []):
    name = m["name"]; sz = m["size"]/1e9
    fam = m.get("details", {}).get("family", "?")
    ps = m.get("details", {}).get("parameter_size", "?")
    print(f"  {name:28} {fam:10} {ps:10} {sz:.1f}GB")
' 2>/dev/null
  fi
else
  bad "ollama /api/tags unreachable"
fi
}

# ── 4. opencode processes ────────────────────────────────────────────────────
section "opencode processes"
# web daemon
oc_web=$(pgrep -f "opencode web" || true)
if [[ -n "$oc_web" ]]; then
  port=$(lsof -nP -iTCP -sTCP:LISTEN -a -p "$(echo "$oc_web" | head -1)" 2>/dev/null | awk 'NR>1{print $9}' | sed 's/.*://' | head -1)
  ok "opencode web daemon pid=$(echo "$oc_web" | head -1) port=${port:-?}"
else
  dim "(no opencode web daemon)"
fi
# run agents
oc_run=$(pgrep -f "opencode run " || true)
if [[ -n "$oc_run" ]]; then ok "opencode run agent(s): $(echo "$oc_run" | wc -l | tr -d ' ')"; else dim "(no active opencode run agent)"; fi
# MCP servers (match '-mcp' in command line to avoid false positives)
mcp=$(pgrep -f "\-mcp" 2>/dev/null || true)
if [[ -n "$mcp" ]]; then
  for pid in $mcp; do
    name=$(ps -o command= -p "$pid" 2>/dev/null | grep -oE '[a-z0-9_.-]+-mcp[a-z0-9@._-]*' | head -1)
    [[ -z "$name" ]] && name=$(ps -o command= -p "$pid" 2>/dev/null | cut -c1-60)
    dim "mcp server: $name (pid $pid)"
  done
fi
# ci-vibe orchestrators
ci_run=$(pgrep -f "ci-vibe-run" || true)
ci_matrix=$(pgrep -f "ci-vibe-matrix" || true)
[[ -n "$ci_run" ]] && ok "ci-vibe-run orchestrator ($(echo "$ci_run" | wc -l | tr -d ' '))" || dim "(no ci-vibe-run)"
[[ -n "$ci_matrix" ]] && ok "ci-vibe-matrix ($(echo "$ci_matrix" | wc -l | tr -d ' '))" || true

# ── 5. opencode internal DB ──────────────────────────────────────────────────
live_skip || {
section "opencode usage"
if [[ -f "$OC_DB" ]]; then
  total_sess=$(sq "$OC_DB" "SELECT COUNT(*) FROM session;")
  msgs=$(sq "$OC_DB" "SELECT COUNT(*) FROM message;")
  parts=$(sq "$OC_DB" "SELECT COUNT(*) FROM part;")
  todos=$(sq "$OC_DB" "SELECT COUNT(*) FROM todo;")
  total_cost=$(sq "$OC_DB" "SELECT ROUND(COALESCE(SUM(cost),0),2) FROM session;")
  cost_24h=$(sq "$OC_DB" "SELECT ROUND(COALESCE(SUM(cost),0),2) FROM session WHERE time_updated > (strftime('%s','now')-86400)*1000;")
  sess_24h=$(sq "$OC_DB" "SELECT COUNT(*) FROM session WHERE time_updated > (strftime('%s','now')-86400)*1000;")
  ok "$total_sess sessions ($sess_24h/24h), \$$total_cost total (\$$cost_24h/24h), $msgs msgs, $parts parts, $todos todos"
  oc_db_sz=$(du -sh "$OC_DB" 2>/dev/null | cut -f1)
  snap_sz=$(du -sh "$HOME/.local/share/opencode/snapshot" 2>/dev/null | cut -f1)
  dim "opencode.db=$oc_db_sz  snapshot=$snap_sz  logs=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)"

  if [[ "$MODE_DEEP" -eq 1 ]]; then
    echo
    dim "per-model spend:"
    sq "$OC_DB" "SELECT model, COUNT(*) as n, ROUND(SUM(cost),2) as cost FROM session WHERE model IS NOT NULL GROUP BY model ORDER BY cost DESC, n DESC LIMIT 12;" | while IFS='|' read -r model n cost; do
      [[ -z "$model" ]] && continue
      # extract id and providerID from JSON-like string: {"id":"...","providerID":"..."}
      id_val=$(echo "$model" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
      prov_val=$(echo "$model" | sed -n 's/.*"providerID":"\([^"]*\)".*/\1/p')
      [[ -z "$id_val" ]] && id_val="$model" && prov_val=""
      printf "  %-35s %-15s %4s sessions  \$%s\n" "$id_val" "($prov_val)" "$n" "$cost"
    done
  fi
else
  bad "opencode.db not found at $OC_DB"
fi
}

# ── 6. active agent task + live run tracker ──────────────────────────────────
section "active run tracker"
if [[ -n "$oc_run" ]]; then
  for pid in $oc_run; do
    cmd=$(ps -o command= -p "$pid" 2>/dev/null)
    dir=$(echo "$cmd" | grep -oE "\-\-dir [^ ]+" | awk '{print $2}')
    model=$(echo "$cmd" | grep -oE "\-\-model [^ ]+" | awk '{print $2}')
    [[ -z "$dir" ]] && { dim "pid=$pid (no --dir)"; continue; }
    task=$(basename "$dir")
    scenario=$(echo "$task" | sed -E 's/^[0-9TZ]+-//; s/-[0-9a-f]+$//')

    # process stats
    age=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
    cpu=$(ps -o %cpu= -p "$pid" 2>/dev/null | tr -d ' ')
    mem=$(ps -o %mem= -p "$pid" 2>/dev/null | tr -d ' ')

    # parse cell from dir path
    cell_path=$(echo "$dir" | sed 's|/worktrees/.*||; s|.*/runs/matrix/||')
    matrix_id=$(echo "$cell_path" | cut -d'/' -f1)
    alias=$(echo "$cell_path" | cut -d'/' -f2)
    pack=$(echo "$cell_path" | cut -d'/' -f3)
    lane=$(echo "$cell_path" | cut -d'/' -f4)
    cell="${matrix_id}/${alias}/${pack}-${lane}"
    cell_db="data/matrix/${cell}.sqlite"

    printf "  ${B}model:${R}  %s  ${B}pid:${R} %s  ${B}age:${R} %s  ${B}cpu:${R} %s%%\n" "$model" "$pid" "$age" "$cpu"
    printf "  ${B}cell:${R}   %s\n" "$cell"
    # find scenario index
    scenario_idx=0
    idx=0
    for s in $PACK_SCENARIOS; do
      idx=$((idx+1))
      [[ "$s" == "$scenario" ]] && scenario_idx=$idx
    done
    printf "  ${B}now:${R}    scenario %d/%d — %s\n" "$scenario_idx" "$PACK_SIZE" "$scenario"

    # agent step + last action from opencode.log
    agent_run_id=$(grep "$task" "$MAIN_LOG" 2>/dev/null | grep -oE 'run=[0-9a-f]+' | tail -1 | cut -d= -f2 || true)
    if [[ -n "$agent_run_id" ]]; then
      last_step=$(grep "run=$agent_run_id" "$MAIN_LOG" 2>/dev/null | grep -oE 'step=[0-9]+' | tail -1 | cut -d= -f2 || true)
      last_ts=$(grep "run=$agent_run_id" "$MAIN_LOG" 2>/dev/null | grep -oE 'timestamp=[^ ]+' | tail -1 | cut -d= -f2 | cut -c1-19 || true)
      last_action=$(grep "run=$agent_run_id" "$MAIN_LOG" 2>/dev/null | grep -E 'evaluated permission|touching file|formatting file' | tail -1 | sed 's/.*message=//; s/ action\..*//' | cut -c1-65 || true)
      [[ -n "$last_step" ]] && printf "  ${B}step:${R}   %s  ${B}last action:${R} %s\n" "$last_step" "$last_action"
      [[ -n "$last_ts" ]] && dim "last log: $last_ts"
    fi

    # worktree git state
    if [[ -d "$dir/.git" ]]; then
      dirty=$(git -C "$dir" status --short 2>/dev/null || true)
      dirty_count=$(echo "$dirty" | grep -c . 2>/dev/null || true)
      dstat=$(git -C "$dir" diff --stat 2>/dev/null | tail -1 || true)
      # check if hidden test has been injected (run is in final phase)
      hidden_injected=$(echo "$dirty" | grep "test_hidden_acceptance" 2>/dev/null || true)
      if [[ -n "$hidden_injected" ]]; then
        printf "  ${B}phase:${R}  \033[33mPOST-AGENT (hidden test injected — running final tests)${R}\n"
      elif [[ "$dirty_count" -gt 0 ]]; then
        printf "  ${B}phase:${R}  \033[36mAGENT WORKING (%d untracked/modified)${R}\n" "$dirty_count"
      else
        printf "  ${B}phase:${R}  \033[36mAGENT WORKING (no file changes yet)${R}\n"
      fi
      [[ -n "$dstat" ]] && dim "diff: $dstat"
    fi

    # ── per-scenario progress for this cell ──
    echo
    printf "  ${B}scenario progress (%s):${R}\n" "$cell"
    if [[ -f "$cell_db" ]]; then
      done_count=0; pass_count=0; hidden_count=0; fg_count=0; tmo_count=0; total_dur=0
      idx=0
      for s in $PACK_SCENARIOS; do
        idx=$((idx+1))
        row=$(sq "$cell_db" "SELECT public_pass, hidden_pass, opencode_exit_code, ROUND(duration_seconds,0) FROM runs WHERE scenario='$s' ORDER BY started_at DESC LIMIT 1;")
        if [[ -n "$row" ]]; then
          dpub=$(echo "$row" | cut -d'|' -f1)
          dhid=$(echo "$row" | cut -d'|' -f2)
          dexit=$(echo "$row" | cut -d'|' -f3)
          ddur=$(echo "$row" | cut -d'|' -f4)
          done_count=$((done_count+1))
          ddur_int=${ddur%.*}
          [[ -z "$ddur_int" ]] && ddur_int=0
          total_dur=$((total_dur + ddur_int))
          [[ "$dpub" == "1" ]] && pass_count=$((pass_count+1))
          [[ "$dhid" == "1" ]] && hidden_count=$((hidden_count+1))
          [[ "$dpub" == "1" && "$dhid" == "0" ]] && fg_count=$((fg_count+1))
          [[ "$dexit" == "124" ]] && tmo_count=$((tmo_count+1))

          if [[ "$dpub" == "1" && "$dhid" == "1" ]]; then
            icon=$'\033[32m✓\033[0m'; outcome="PASS"
          elif [[ "$dpub" == "1" && "$dhid" == "0" ]]; then
            icon=$'\033[33m!\033[0m'; outcome="FALSE-GREEN"
          elif [[ "$dexit" == "124" ]]; then
            icon=$'\033[31m✗\033[0m'; outcome="TIMEOUT"
          elif [[ "$dpub" == "0" ]]; then
            icon=$'\033[31m✗\033[0m'; outcome="PUBLIC-RED"
          else
            icon=$'\033[31m?\033[0m'; outcome="exit=$dexit"
          fi
          printf "  %s [%2d] %-35s %-14s %5ss\n" "$icon" "$idx" "$s" "$outcome" "$ddur"
        elif [[ "$s" == "$scenario" ]]; then
          printf "  \033[36m▶\033[0m [%2d] %-35s \033[36m%-14s\033[0m %s\n" "$idx" "$s" "IN-FLIGHT" "($age elapsed)"
        else
          printf "  \033[2m·\033[0m [%2d] %-35s \033[2m%-14s\033[0m\n" "$idx" "$s" "pending"
        fi
      done

      # running totals
      echo
      remaining=$((PACK_SIZE - done_count - 1))  # -1 for in-flight
      [[ "$remaining" -lt 0 ]] && remaining=0
      if [[ "$done_count" -gt 0 ]]; then
        avg_dur=$((total_dur / done_count))
        eta_sec=$((avg_dur * remaining))
        eta_min=$((eta_sec / 60))
        pass_rate=$((pass_count * 100 / done_count))
        hidden_rate=$((hidden_count * 100 / done_count))
        gap=$((pass_rate - hidden_rate))
      else
        avg_dur=0; eta_min=0; pass_rate=0; hidden_rate=0; gap=0
      fi

      printf "  ${B}CELL TOTALS:${R}  done=%d/%d  pass=%d(%d%%)  hidden=%d(%d%%)  fg=%d  to=%d  gap=%d%%\n" \
        "$done_count" "$PACK_SIZE" "$pass_count" "$pass_rate" "$hidden_count" "$hidden_rate" "$fg_count" "$tmo_count" "$gap"
      printf "  ${B}AVG/SCENARIO:${R} %ds    ${B}REMAINING:${R} %d scenario(s)    ${B}ETA:${R} ~%dm\n" \
        "$avg_dur" "$remaining" "$eta_min"
    fi
  done
else
  dim "(no opencode run process)"
fi

# ── 7. matrix scope + progress + per-run detail ─────────────────────────────
live_skip || {
section "matrix scope + progress"
# discover matrix cell DBs
matrix_dbs=$(find data/matrix -name "*.sqlite" 2>/dev/null | sort || true)

# detect in-flight scenario from active opencode run process
inflight_scenario=""
inflight_cell=""
if [[ -n "$oc_run" ]]; then
  for pid in $oc_run; do
    cmd=$(ps -o command= -p "$pid" 2>/dev/null)
    dir=$(echo "$cmd" | grep -oE "\-\-dir [^ ]+" | awk '{print $2}')
    [[ -z "$dir" ]] && continue
    task=$(basename "$dir")
    # parse scenario from task name: <timestamp>-<scenario>-<hash>
    scenario=$(echo "$task" | sed -E 's/^[0-9TZ]+-//; s/-[0-9a-f]+$//')
    [[ -n "$scenario" ]] && inflight_scenario="$scenario"
    # parse cell from dir path: .../runs/matrix/<matrix_id>/<alias>/<pack>/<lane>/worktrees/...
    cell_path=$(echo "$dir" | sed 's|/worktrees/.*||; s|.*/runs/matrix/||')
    if [[ -n "$cell_path" ]]; then
      # reconstruct cell name: matrix_id/alias/pack-lane
      matrix_id=$(echo "$cell_path" | cut -d'/' -f1)
      alias=$(echo "$cell_path" | cut -d'/' -f2)
      pack=$(echo "$cell_path" | cut -d'/' -f3)
      lane=$(echo "$cell_path" | cut -d'/' -f4)
      inflight_cell="${matrix_id}/${alias}/${pack}-${lane}"
    fi
  done
fi

if [[ -n "$matrix_dbs" ]]; then
  # summary line per cell
  while IFS= read -r db; do
    [[ -z "$db" ]] && continue
    rel=${db#data/matrix/}
    cell=${rel%.sqlite}
    row=$(sq "$db" "SELECT COUNT(*),
        COALESCE(SUM(public_pass),0),
        COALESCE(SUM(hidden_pass),0),
        COALESCE(SUM(CASE WHEN public_pass=1 AND hidden_pass=0 THEN 1 ELSE 0 END),0),
        COALESCE(SUM(CASE WHEN opencode_exit_code=124 THEN 1 ELSE 0 END),0),
        COALESCE(ROUND(AVG(duration_seconds),0),0)
        FROM runs;")
    n=$(echo "$row" | cut -d'|' -f1)
    pub=$(echo "$row" | cut -d'|' -f2)
    hid=$(echo "$row" | cut -d'|' -f3)
    fg=$(echo "$row" | cut -d'|' -f4)
    tmo=$(echo "$row" | cut -d'|' -f5)
    avg=$(echo "$row" | cut -d'|' -f6)

    # progress bar
    pct=$(( n * 100 / PACK_SIZE ))
    bar_len=10
    filled=$(( n * bar_len / PACK_SIZE ))
    [[ "$filled" -gt "$bar_len" ]] && filled=$bar_len
    bar=""
    for i in $(seq 1 $bar_len); do
      if [[ $i -le $filled ]]; then bar+="█"; else bar+="░"; fi
    done

    # status icon
    status_icon="✓"
    [[ "$n" -lt "$PACK_SIZE" && "$n" -gt 0 ]] && status_icon="!"
    [[ "$n" -eq 0 ]] && status_icon="✗"
    # mark in-flight cell
    inflight_marker=""
    [[ "$cell" == "$inflight_cell" ]] && inflight_marker=" \033[36m◀ IN-FLIGHT${R}"

    # false-green / timeout
    fg_str=""
    [[ "$fg" -gt 0 ]] && fg_str=" \033[33mfg=$fg${R}"
    tmo_str=""
    [[ "$tmo" -gt 0 ]] && tmo_str=" \033[31mto=$tmo${R}"

    # in quiet mode, suppress green rows
    if [[ "$MODE_QUIET" -eq 1 && "$status_icon" == "✓" && -z "$fg_str" && -z "$tmo_str" && -z "$inflight_marker" ]]; then
      continue
    fi
    # color the status icon
    if [[ "$status_icon" == "✓" ]]; then
      icon_color="\033[32m"
    elif [[ "$status_icon" == "!" ]]; then
      icon_color="\033[33m"
    else
      icon_color="\033[31m"
    fi
    printf "  ${icon_color}%s${R} %s %2d/%d %d%% %-55s pub=%s hid=%s${fg_str}${tmo_str}${inflight_marker}\n" \
      "$status_icon" "$bar" "$n" "$PACK_SIZE" "$pct" "$cell" "$pub" "$hid"
  done <<< "$matrix_dbs"

  # ── per-run detail for in-flight or most-recent cell ────────────────────
  echo
  # pick the cell to show detail for: in-flight first, else most recently modified DB
  detail_cell=""
  detail_db=""
  if [[ -n "$inflight_cell" ]]; then
    detail_cell="$inflight_cell"
    detail_db="data/matrix/${inflight_cell}.sqlite"
  else
    # most recently modified DB
    detail_db=$(ls -t $(find data/matrix -name "*.sqlite" 2>/dev/null) 2>/dev/null | head -1)
    [[ -n "$detail_db" ]] && detail_cell=${detail_db#data/matrix/} && detail_cell=${detail_cell%.sqlite}
  fi

  if [[ -n "$detail_db" && -f "$detail_db" ]]; then
    # determine which scenarios are done, in-flight, pending
    done_scenarios=$(sq "$detail_db" "SELECT scenario FROM runs ORDER BY started_at;")

    printf "  ${B}run detail:${R} %s\n" "$detail_cell"
    printf "  ${DIM}scope: %d scenarios in maintenance_value pack${R}\n" "$PACK_SIZE"

    # print per-scenario status
    idx=0
    for scenario in $PACK_SCENARIOS; do
      idx=$((idx+1))
      # check if done
      done_row=$(sq "$detail_db" "SELECT public_pass, hidden_pass, opencode_exit_code, ROUND(duration_seconds,0), started_at FROM runs WHERE scenario='$scenario' ORDER BY started_at DESC LIMIT 1;")
      if [[ -n "$done_row" ]]; then
        dpub=$(echo "$done_row" | cut -d'|' -f1)
        dhid=$(echo "$done_row" | cut -d'|' -f2)
        dexit=$(echo "$done_row" | cut -d'|' -f3)
        ddur=$(echo "$done_row" | cut -d'|' -f4)
        dstart=$(echo "$done_row" | cut -d'|' -f5)
        dtime=$(echo "$dstart" | sed 's/T/ /; s/+.*//' | cut -c1-16)

        # outcome icon
        if [[ "$dpub" == "1" && "$dhid" == "1" ]]; then
          icon=$'\033[32m✓\033[0m'; outcome="PASS"
        elif [[ "$dpub" == "1" && "$dhid" == "0" ]]; then
          icon=$'\033[33m!\033[0m'; outcome="FALSE-GREEN"
        elif [[ "$dexit" == "124" ]]; then
          icon=$'\033[31m✗\033[0m'; outcome="TIMEOUT"
        elif [[ "$dpub" == "0" ]]; then
          icon=$'\033[31m✗\033[0m'; outcome="PUBLIC-RED"
        else
          icon=$'\033[31m?\033[0m'; outcome="exit=$dexit"
        fi
        # in quiet mode, suppress PASS rows
        if [[ "$MODE_QUIET" -eq 1 && "$outcome" == "PASS" ]]; then
          continue
        fi
        printf "  %s [%2d] %-35s %-14s %5ss  %s\n" "$icon" "$idx" "$scenario" "$outcome" "$ddur" "$dtime"
      elif [[ "$scenario" == "$inflight_scenario" ]]; then
        printf "  \033[36m▶\033[0m [%2d] %-35s %-14s %s\n" "$idx" "$scenario" "IN-FLIGHT" "running now"
      else
        [[ "$MODE_QUIET" -eq 1 ]] && continue
        printf "  \033[2m·\033[0m [%2d] %-35s %-14s\n" "$idx" "$scenario" "pending"
      fi
    done

    # summary stats
    echo
    n=$(sq "$detail_db" "SELECT COUNT(*) FROM runs;")
    pub=$(sq "$detail_db" "SELECT COALESCE(SUM(public_pass),0) FROM runs;")
    hid=$(sq "$detail_db" "SELECT COALESCE(SUM(hidden_pass),0) FROM runs;")
    fg=$(sq "$detail_db" "SELECT COALESCE(SUM(CASE WHEN public_pass=1 AND hidden_pass=0 THEN 1 ELSE 0 END),0) FROM runs;")
    tmo=$(sq "$detail_db" "SELECT COALESCE(SUM(CASE WHEN opencode_exit_code=124 THEN 1 ELSE 0 END),0) FROM runs;")
    avg=$(sq "$detail_db" "SELECT COALESCE(ROUND(AVG(duration_seconds),0),0) FROM runs;")
    pass_rate=0; hidden_rate=0
    [[ "$n" -gt 0 ]] && pass_rate=$(( pub * 100 / n )) && hidden_rate=$(( hid * 100 / n ))
    dim "done=$n/$PACK_SIZE  pub_pass=$pub ($pass_rate%)  hidden_pass=$hid ($hidden_rate%)  false_green=$fg  timeout=$tmo  avg=${avg}s"
    if [[ "$n" -gt 0 ]]; then
      trust_gap=$(( pass_rate - hidden_rate ))
      if [[ "$trust_gap" -gt 0 ]]; then
        printf "  ${B}trust gap: %d%%${R}  ${DIM}(pub_pass%% - hidden_pass%%)${R}\n" "$trust_gap"
      else
        ok "trust gap: 0% (no false-greens)"
      fi
    fi
  fi

  # stale detection
  if [[ -n "$ci_run" ]]; then
    newest_db_run=$(find data/matrix -name "*.sqlite" -exec sqlite3 -readonly {} "SELECT MAX(ended_at) FROM runs;" \; 2>/dev/null | sort -r | head -1)
    if [[ -n "$newest_db_run" ]]; then
      cutoff=$(date -u -v-2H "+%Y-%m-%dT%H:%M" 2>/dev/null || date -u -d "-2 hours" "+%Y-%m-%dT%H:%M" 2>/dev/null)
      norm=$(echo "$newest_db_run" | sed 's/\..*//; s/+.*//')
      if [[ "$norm" < "$cutoff" ]]; then
        warn "STALE: ci-vibe-run running but newest DB run is $newest_db_run (>2h ago)"
      fi
    fi
  fi
else
  dim "(no matrix DBs in data/matrix/)"
fi
}

# ── 7b. totals: model-wise, pack-wise, grand total ──────────────────────────
live_skip || {
section "totals (all DBs)"
all_dbs=$(find data -name "*.sqlite" 2>/dev/null || true)
if [[ -n "$all_dbs" ]]; then
  # collect per-DB rows: model|pack|n|pub|hid|fg|tmo
  raw=""
  while IFS= read -r db; do
    [[ -z "$db" ]] && continue
    r=$(sqlite3 -readonly "$db" "SELECT model, challenge_pack, COUNT(*), COALESCE(SUM(public_pass),0), COALESCE(SUM(hidden_pass),0), COALESCE(SUM(CASE WHEN public_pass=1 AND hidden_pass=0 THEN 1 ELSE 0 END),0), COALESCE(SUM(CASE WHEN opencode_exit_code=124 THEN 1 ELSE 0 END),0) FROM runs WHERE model IS NOT NULL AND model != '' GROUP BY model, challenge_pack;" 2>/dev/null || true)
    [[ -n "$r" ]] && raw="${raw}${r}"$'\n'
  done <<< "$all_dbs"

  if [[ -n "$raw" ]]; then
    # ── model-wise ──
    printf "  ${B}by model:${R}\n"
    echo "$raw" | awk -F'|' '
      { gsub(/.*\//,"",$1); model[$1]+=$3; pub[$1]+=$4; hid[$1]+=$5; fg[$1]+=$6; tmo[$1]+=$7 }
      END {
        for (m in model) {
          if (m == "" || m ~ /^</ || m == "model") continue
          n=model[m]; p=pub[m]; h=hid[m]; f=fg[m]; t=tmo[m]
          pr = (n>0) ? int(p*100/n) : 0; hr = (n>0) ? int(h*100/n) : 0
          gap = pr - hr
          printf "  %-28s runs=%-4d pub=%-3d(%2d%%) hid=%-3d(%2d%%) fg=%-3d to=%-3d gap=%d%%\n", m, n, p, pr, h, hr, f, t, gap
        }
      }' | sort -t= -k2 -rn

    # ── pack-wise ──
    echo
    printf "  ${B}by pack:${R}\n"
    echo "$raw" | awk -F'|' '
      { if ($2 == "") next; pack[$2]+=$3; pub[$2]+=$4; hid[$2]+=$5; fg[$2]+=$6; tmo[$2]+=$7 }
      END {
        for (p in pack) {
          n=pack[p]; pu=pub[p]; h=hid[p]; f=fg[p]; t=tmo[p]
          pr = (n>0) ? int(pu*100/n) : 0; hr = (n>0) ? int(h*100/n) : 0
          gap = pr - hr
          printf "  %-22s runs=%-4d pub=%-3d(%2d%%) hid=%-3d(%2d%%) fg=%-3d to=%-3d gap=%d%%\n", p, n, pu, pr, h, hr, f, t, gap
        }
      }' | sort -t= -k2 -rn

    # ── grand total ──
    echo
    echo "$raw" | awk -F'|' '
      { tn+=$3; tp+=$4; th+=$5; tf+=$6; tt+=$7 }
      END {
        pr = (tn>0) ? int(tp*100/tn) : 0; hr = (tn>0) ? int(th*100/tn) : 0
        gap = pr - hr
        printf "  \033[1m%-28s runs=%-4d pub=%-3d(%2d%%) hid=%-3d(%2d%%) fg=%-3d to=%-3d gap=%d%%\033[0m\n", "GRAND TOTAL", tn, tp, pr, th, hr, tf, tt, gap
      }'
  else
    dim "(no runs data found)"
  fi
else
  dim "(no SQLite DBs found)"
fi
}

# ── 8. evaluator coverage ────────────────────────────────────────────────────
live_skip || {
section "evaluator coverage"
if [[ -n "$matrix_dbs" ]]; then
  shown=0
  while IFS= read -r db; do
    [[ -z "$db" ]] && continue
    rel=${db#data/matrix/}
    cell=${rel%.sqlite}
    rev_count=$(sq "$db" "SELECT COUNT(*) FROM evaluator_reviews;" 2>/dev/null || echo "0")
    fg_count=$(sq "$db" "SELECT SUM(CASE WHEN public_pass=1 AND hidden_pass=0 THEN 1 ELSE 0 END) FROM runs;" 2>/dev/null || echo "0")
    [[ "$rev_count" == "" ]] && rev_count=0
    [[ "$fg_count" == "" ]] && fg_count=0
    # only show if there are false-greens or reviews
    if [[ "$fg_count" -gt 0 || "$rev_count" -gt 0 ]]; then
      if [[ "$fg_count" -gt 0 && "$rev_count" -lt "$fg_count" ]]; then
        warn "$cell: $rev_count reviews / $fg_count false-greens (UNREVIEWED)"
      elif [[ "$fg_count" -gt 0 ]]; then
        ok "$cell: $rev_count reviews / $fg_count false-greens (covered)"
      else
        dim "$cell: $rev_count reviews, 0 false-greens"
      fi
      shown=$((shown+1))
    fi
  done <<< "$matrix_dbs"
  [[ "$shown" -eq 0 ]] && dim "(no false-greens or reviews recorded)"
else
  dim "(no matrix DBs)"
fi
}

# ── 9. disk & log health ─────────────────────────────────────────────────────
live_skip || {
section "disk & log health"
# disk
dim "disk: ollama=$(du -sh ~/.ollama/models 2>/dev/null | cut -f1 || echo '?')  data=$(du -sh data 2>/dev/null | cut -f1 || echo '?')  runs=$(du -sh runs 2>/dev/null | cut -f1 || echo '?')"

# matrix-run.log exit codes
bad_exits=$(grep -rh "exit_code=" runs/matrix/*/matrix-run.log 2>/dev/null | grep -v "exit_code=0" || true)
if [[ -n "$bad_exits" ]]; then
  while IFS= read -r line; do
    warn "matrix exit: $line"
  done <<< "$bad_exits"
else
  ok "all matrix-run.log exit_code=0"
fi

# opencode.log health (last 30m)
if [[ -f "$MAIN_LOG" ]]; then
  cutoff=$(date -u -v-30M "+%Y-%m-%dT%H:%M" 2>/dev/null || date -u -d "-30 minutes" "+%Y-%m-%dT%H:%M" 2>/dev/null)
  recent=$(awk -v c="$cutoff" '$0 ~ /^timestamp=/ { ts=substr($0,11,16); if (ts >= c) print }' "$MAIN_LOG" 2>/dev/null)
  if [[ -n "$recent" ]]; then
    errs=$(echo "$recent" | grep -c "level=ERROR" || true)
    loops=$(echo "$recent" | grep -c "exiting loop" || true)
    perms=$(echo "$recent" | grep -c "evaluated permission" || true)
    if [[ "$errs" -gt 0 ]]; then bad "$errs ERROR(s) in opencode.log (last 30m)"; else ok "no errors in opencode.log (last 30m)"; fi
    # classify warnings
    warn_types=$(echo "$recent" | grep "level=WARN" | grep -oE 'message="[^"]+"' | sort | uniq -c | sort -rn | head -3)
    if [[ -n "$warn_types" ]]; then
      while IFS= read -r wl; do
        cnt=$(echo "$wl" | awk '{print $1}')
        msg=$(echo "$wl" | sed -E 's/^[[:space:]]*[0-9]+[[:space:]]+//')
        printf "  \033[33m!\033[0m %s x %s\n" "$cnt" "$msg"
      done <<< "$warn_types"
    fi
    dim "$loops loop exits, $perms permission evals (chatter)"
    # non-config issues
    real=$(echo "$recent" | grep -E "level=ERROR|level=WARN" | grep -v "duplicate skill" | head -3)
    if [[ -n "$real" ]]; then
      dim "non-config issues:"
      echo "$real" | sed 's/timestamp=//; s/ level=/  /' | cut -c1-150 | sed 's/^/    /'
    fi
  else
    ok "no log activity in last 30m (idle)"
  fi
else
  bad "no opencode.log"
fi
}

# ── 10. dashboard hint ───────────────────────────────────────────────────────
live_skip || {
section "dashboard"
latest_cfg=$(ls -t configs/matrix/*.json 2>/dev/null | head -1)
if [[ -n "$latest_cfg" ]]; then
  cfg_name=$(basename "$latest_cfg")
  dim "streamlit: CI_VIBE_DB=\$(uv run ci-vibe-matrix dbs configs/matrix/$cfg_name) uv run --extra app streamlit run ci_vibe_lab/dashboard.py"
  dim "integrity:  uv run ci-vibe-report integrity --matrix configs/matrix/$cfg_name --out /tmp/integ.md"
  dim "status:     uv run ci-vibe-matrix status configs/matrix/$cfg_name"
else
  dim "(no matrix configs found)"
fi

# ── integrity mode (opt-in, slow) ────────────────────────────────────────────
if [[ "$MODE_INT" -eq 1 ]]; then
  section "evidence integrity (ci-vibe-report)"
  for cfg in configs/matrix/*.json; do
    [[ -f "$cfg" ]] || continue
    cfg_id=$(basename "$cfg" .json)
    out="/tmp/integ-$cfg_id.md"
    if uv run ci-vibe-report integrity --matrix "$cfg" --out "$out" >/dev/null 2>&1; then
      ok "$cfg_id: PASS ($out)"
    else
      bad "$cfg_id: FAIL ($out)"
    fi
  done
fi

# ── deep mode: full matrix status table ──────────────────────────────────────
if [[ "$MODE_DEEP" -eq 1 ]]; then
  section "matrix status (ci-vibe-matrix)"
  for cfg in configs/matrix/*.json; do
    [[ -f "$cfg" ]] || continue
    dim "$(basename "$cfg" .json):"
    uv run ci-vibe-matrix status "$cfg" 2>/dev/null | sed 's/^/  /' || warn "status failed for $cfg"
  done
fi
}

# ── log tail modes ───────────────────────────────────────────────────────────
if [[ "$MODE_FOLLOW" -eq 1 ]]; then
  section "following opencode.log (filtered, Ctrl-C)"
  tail -n 0 -f "$MAIN_LOG" 2>/dev/null \
    | grep --line-buffered -vE "evaluated permission|tracking hash|touching file|resolved path|llm runtime selected|stream providerID|process session.id"
elif [[ "$MODE_RAW" -eq 1 ]]; then
  section "raw opencode.log (last 80 lines)"
  tail -n 80 "$MAIN_LOG" 2>/dev/null
fi

echo

# ── watch mode: rerun snapshot every 5s ──────────────────────────────────────
if [[ "$MODE_WATCH" -eq 1 ]]; then
  echo "  ${DIM}(watching — refresh every 5s, Ctrl-C to stop)${R}"
  while true; do
    sleep 5
    clear
    "$0"
  done
fi
