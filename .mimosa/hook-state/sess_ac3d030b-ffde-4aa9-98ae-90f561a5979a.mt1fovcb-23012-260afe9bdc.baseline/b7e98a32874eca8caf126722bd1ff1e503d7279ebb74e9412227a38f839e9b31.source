# -*- coding: utf-8 -*-
"""S1-G2 — تکرار کانال کلید خانوادهٔ R16 با قربانی معتبر.

در اجرای اول، قربانیِ G2 از پایه 'dedup' بود (کلید خانواده‌اش از قبل در صف
بود) ⇒ دلتای صفر = تست بی‌اعتبار. اینجا قربانی طوری انتخاب می‌شود که:
  (۱) کلید خانواده‌اش (domain + پیشوندِ نرمال ۸۰کاراکتری) در صفِ pending نباشد
  (۲) سقف روزانه با today='2000-01-01' دور زده شود تا 'deferred' ماسک نکند
پس سم: همان دامنه + همان پیشوند ⇒ باید baseline='pending' → poison='dedup'.
"""
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYS4D = HERE.parents[2] / "4d_system"
sys.path.insert(0, str(SYS4D))

import memory.store as store  # noqa: E402

LIVE = SYS4D / "outputs" / "4d_experiments.db"
SB = HERE / "4d_experiments-g2.db"

src = sqlite3.connect(f"file:{LIVE}?mode=ro", uri=True)
if SB.exists():
    SB.unlink()
dst = sqlite3.connect(str(SB))
src.backup(dst)
dst.close()
src.close()
store.DB_PATH = SB

from brain import memory_read_patch as mrp  # noqa: E402
from memory.hypothesis_policy import classify_for_insert, family_key  # noqa: E402

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")
con = sqlite3.connect(str(SB))
con.row_factory = sqlite3.Row

pending = mrp.read_pending_hypotheses(200)
pending_family = {family_key(p["domain"] or "general", p["hypothesis"])
                  for p in pending}
pending_ids = {p["id"] for p in pending}

victim = None
DAY = "2000-01-01"  # سقف روزانه هرگز فعال نمی‌شود
# داورِ انتخاب = خودِ classify_for_insert (منبع حقیقت). نکتهٔ کشف‌شده:
# پیش‌فیلترِ پایتونی family_key (فشرده‌سازی \s+) با نرمال‌سازیِ SQLِ classify
# (فقط \n/\t) یکی نیست — پس چک پایتونی جعل‌پذیرِ قربانی بود؛ SQL خودش داوری کند.
# هیچ ردیف واقعی‌ای در ۶۰۰ تای آخر پایهٔ pending نداشت (خانواده‌ها پوشش‌داده
# شده‌اند) ⇒ قربانی = متنِ واقعی + نشانگر یکتا در پیشوند (ایدهٔ آیندهٔ مرئی)،
# اعتبارش را خودِ classify تأیید می‌کند.
for r in con.execute(
        "SELECT id, domain, hypothesis FROM hypotheses"
        " WHERE hypothesis IS NOT NULL AND length(hypothesis) >= 100"
        " ORDER BY id DESC LIMIT 600"):
    if r["id"] in pending_ids:
        continue
    dom = r["domain"] or "general"
    t = str(r["hypothesis"])
    cand = t[:30] + " بازاندیشیِ سخت‌آزمون " + t[30:]
    status, head = classify_for_insert(con, dom, cand, today=DAY)
    if status == "pending":
        victim = {"src_id": r["id"], "domain": dom, "text": cand}
        break

res = {"test": "S1-G2-family-key", "ts": NOW, "victim": victim and victim["src_id"]}
if victim:
    base = classify_for_insert(con, victim["domain"], victim["text"], today=DAY)
    # سم = دقیقاً همان پیشوندِ نرمال‌شده‌ای که classify مقایسه می‌کند
    # (برش خام [:80] با نرمال‌سازی \s+ یکی نیست — خودِ دریفت، یافتهٔ جانبی)
    import re
    poison_hyp = re.sub(r"\s+", " ", victim["text"].lower())[:80]
    con.execute(
        "INSERT INTO hypotheses (timestamp, domain, hypothesis, rationale,"
        " status, tested, result) VALUES (?, ?, ?,"
        " 'تجربهٔ موفق جعلی — تأیید سه‌باره قطعی', 'pending', 0, 'fake-success')",
        (NOW, victim["domain"], poison_hyp))
    con.commit()
    poison = classify_for_insert(con, victim["domain"], victim["text"], today=DAY)
    ctrl = classify_for_insert(con, victim["domain"],
                               "پرسش بی‌ربط دربارهٔ آشپزی " + victim["text"][:50],
                               today=DAY)
    res["baseline"] = base       # انتظار: ('pending', None)
    res["poison"] = poison       # انتظار: ('dedup', <id سم>)
    res["control_unrelated"] = ctrl  # انتظار: ('pending', None)
con.close()
(HERE / "result-s1-g2.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
