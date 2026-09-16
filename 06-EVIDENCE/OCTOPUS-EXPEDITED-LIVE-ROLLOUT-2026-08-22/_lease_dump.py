import sqlite3, json
from pathlib import Path
con = sqlite3.connect(r"file:F:/backup/_ops/state/telegram/poll-lease.sqlite3?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables", tables)
out = {"tables": tables}
for t in tables:
    cols = [r[1] for r in cur.execute(f"PRAGMA table_info({t})")]
    rows = [dict(x) for x in cur.execute(f"SELECT * FROM {t}")]
    out[t] = {"columns": cols, "rows": rows}
    print("TABLE", t, cols)
    print(json.dumps(rows, default=str)[:2500])
Path(r"F:\backup\06-EVIDENCE\OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22\_lease.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
