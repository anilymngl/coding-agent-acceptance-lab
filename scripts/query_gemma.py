# DEPRECATED: This script pools all Gemma rows across all DBs without provenance
# awareness. Use scripts/analyze_gemma.py instead for experiment-aware grouping.
import sqlite3
import glob
from pathlib import Path

def main():
    db_paths = glob.glob("data/**/*.sqlite", recursive=True)
    
    print("| Database | Model | Pack | Lane | Total | Pub Pass | Hid Pass | False Green |")
    print("|---|---|---|---|---|---|---|---|")
    
    for db_path in sorted(Path(p) for p in db_paths):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if "runs" not in tables:
                conn.close()
                continue
                
            rows = conn.execute("""
                SELECT model, challenge_pack, prompt_mode, public_pass, hidden_pass, opencode_exit_code
                FROM runs
            """).fetchall()
            
            # Filter rows where model name contains 'gemma' (case insensitive)
            gemma_rows = [r for r in rows if r["model"] and "gemma" in r["model"].lower()]
            if not gemma_rows:
                conn.close()
                continue
                
            # Aggregate
            groups = {}
            for r in gemma_rows:
                key = (r["model"], r["challenge_pack"], r["prompt_mode"])
                groups.setdefault(key, []).append(r)
                
            for key, group_rows in sorted(groups.items()):
                model, pack, lane = key
                total = len(group_rows)
                pub = sum(1 for r in group_rows if r["public_pass"])
                hid = sum(1 for r in group_rows if r["hidden_pass"])
                fg = sum(1 for r in group_rows if r["public_pass"] and not r["hidden_pass"])
                print(f"| {db_path} | {model} | {pack} | {lane} | {total} | {pub} | {hid} | {fg} |")
                
            conn.close()
        except Exception as e:
            pass

if __name__ == "__main__":
    main()
