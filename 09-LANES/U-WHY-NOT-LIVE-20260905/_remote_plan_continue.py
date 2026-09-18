import json
import os

season_dir = "/home/ari/octopus-mesh/state/season"
print("SEASON_DIR", os.path.isdir(season_dir))
if os.path.isdir(season_dir):
    print("SEASON_FILES", ",".join(sorted(os.listdir(season_dir))[:40]))
note = os.path.join(season_dir, "SEASON-5-2026-09-04.md")
if os.path.isfile(note):
    txt = open(note, encoding="utf-8", errors="replace").read()
    print("NOTE_N", len(txt))
    print("NOTE_HAS_HOLD", "HOLD_EXTERNAL" in txt)
    print("NOTE_HAS_TELEGRAM", ("Telegram" in txt) or ("telegram" in txt))
gates = os.path.join(season_dir, "season5-gates-final.json")
d = json.load(open(gates, encoding="utf-8"))
print("M5", d.get("m5_owner_release"))
print("ADS", d.get("ads_budget"))
print("PAINTING", d.get("painting"))
print("HAS_HOLD_KEY", ("HOLD_EXTERNAL" in d) or ("hold_external" in d))

hits = []
for dirpath, _, filenames in os.walk(season_dir):
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if ("HOLD_EXTERNAL" in t) or ("hold_external" in t):
            hits.append(p)
print("HOLD_FILES_N", len(hits))
for p in hits[:20]:
    print("HOLD_FILE", p)

ledgers = [
    "/home/ari/ofn/data/state/legs/claims-ledger.jsonl",
    "/home/ari/ofn/09-LANES/ECONOMIC-LEARNING/runs/2026-09-02/economic-learning-ledger.jsonl",
]
for p in ledgers:
    if not os.path.isfile(p):
        print("LEDGER_MISSING", p)
        continue
    n = 0
    with open(p, encoding="utf-8", errors="replace") as f:
        for _ in f:
            n += 1
    print("LEDGER_LINES", p, n)

ofn = "/home/ari/ofn"
mods = []
if os.path.isdir(ofn):
    for dirpath, dirnames, filenames in os.walk(ofn):
        dirnames[:] = [x for x in dirnames if x not in (".git", "__pycache__", ".venv", "node_modules")]
        for fn in filenames:
            low = fn.lower()
            if low.endswith((".py", ".md", ".json")) and any(
                s in low for s in ("telegram", "hold_ext", "outbound", "wire")
            ):
                mods.append(os.path.join(dirpath, fn))
            if len(mods) > 30:
                break
        if len(mods) > 30:
            break
print("MOD_N", len(mods))
for p in mods[:30]:
    print("MOD", p)
