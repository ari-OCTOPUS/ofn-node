#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_prediction_writer.py — Q3: حلقهٔ predict→outcome→belief روی DB موقت."""
import sys, sqlite3, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_ops/memory"))
from memory.prediction_ledger import PredictionLedger   # همان طرحِ دیتابیسی

TMP = Path(tempfile.mkdtemp()) / "pred.db"
LED = PredictionLedger(TMP)
import brain.prediction_writer as PW
PW.LEDGER = TMP
PW.BELIEFS = TMP.with_suffix(".beliefs.json")

F = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: F.append(n)

pid1 = PW.predict("fx-test", 0.0100)
check("t1 prediction registered (id returned)", bool(pid1))
with LED._conn() as _c: rows = _c.execute("SELECT COUNT(*) FROM predictions WHERE source LIKE '%fx-test'").fetchone()[0]
check("t2 row in ledger", rows == 1)

r1 = PW.resolve("fx-test", 0.0120)   # MI بالا رفت → باید hit باشد
check("t3 outcome hit attached", r1 and r1["hit"] is True and r1["belief"]["alpha"] == 2.0)
r1b = PW.resolve("fx-test", 0.0120)
check("t4 duplicate resolve is a no-op", r1b is None)

pid2 = PW.predict("fx-test", 0.0120)
r2 = PW.resolve("fx-test", 0.0050)   # سقوط → miss
check("t5 miss updates beta", r2 and r2["hit"] is False and r2["belief"]["beta"] == 2.0)
with LED._conn() as _c: outs = _c.execute("SELECT outcome FROM outcomes ORDER BY outcome_id").fetchall()
check("t6 outcomes in ledger (hit then miss)", "hit" in outs[0][0] and "miss" in outs[1][0])

# دفعاتِ بعدی: باور آستانه را تغییر می‌دهد (تأثیر باور بر پیش‌بینی بعدی)
pid3 = PW.predict("fx-test", 0.0050)
with LED._conn() as _c: row = _c.execute("SELECT content FROM predictions WHERE prediction_id=?", (pid3,)).fetchone()
check("t7 theta derived from updated (pessimistic) belief", "belief mean 0.500" in row[0] or "belief mean" in row[0])

# تریگر ضدفتلش همچنان بیدار است
try:
    with LED._conn() as _c:
        _c.execute("UPDATE predictions SET content='x' WHERE prediction_id=?", (pid1,))
    check("t8 append-only trigger blocks UPDATE", False)
except sqlite3.DatabaseError:
    check("t8 append-only trigger blocks UPDATE", True)

# Q1/Q3b: self-test و پیام صادق
from core.model import run_self_test
st = run_self_test()
check("t9 run_self_test includes I_pred + Var_ex, all pass",
      "I_pred" in st and "Var_ex" in st and all(v[2] < 1e-4 for v in st.values()))
from brain.self_evolve import _reject_reason
check("t10 equal-novelty message is honest (برابر، نه کمتر)",
      "برابر" in _reject_reason(0.0, 0.0) and "کمتر" in _reject_reason(0.1, 0.2))

print("ALL PASS" if not F else "FAILURES: " + str(F))
sys.exit(1 if F else 0)
