from pathlib import Path
import re
log = Path(r"F:\backup\_ops\state\adr-033\reports\SELF-PROGRESS-UNLOCK-2026-08-12\run_all-retry.log")
term = Path(r"C:\Users\Armin\.cursor\projects\f-backup\terminals")
# find newest run_all terminal
cands = sorted(term.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
tpath = None
for p in cands[:8]:
    head = p.read_text(encoding="utf-8", errors="replace")[:800]
    if "run_all.py" in head:
        tpath = p
        break
src = tpath if tpath else log
t = src.read_text(encoding="utf-8", errors="replace") if src.exists() else ""
blocks = re.findall(r"test_[a-z0-9_]+\.py", t)
print("src", src)
print("unique", len(set(blocks)), "mentions", len(blocks))
print("has_exit", "exit_code:" in t)
print("tail:")
print("\n".join(t.splitlines()[-12:]))
