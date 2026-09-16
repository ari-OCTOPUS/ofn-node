# -*- coding: utf-8 -*-
"""S3 — قدرت تفکیک مشاورت شورا: عضوِ واقعی (ollama) در برابر استاب (HARD-TEST).

طراحی (مطابق مگاپرامپت، با برچسب‌گذاری ماشینی — «کور» ذاتاً):
  · ۱۰ فرضیهٔ واقعی از صفِ ۳۹۷تاییِ زنده (فقط-خواندن)
  · دوقلو: نسخهٔ درست = متن اصلی؛ نسخهٔ «غلط» = همان کلمات با ترتیب به‌هم‌ریخته
    (بذر ثابت — نویزِ ساختاری، بدون تغییر واژگان)
  · عضو واقعی: councils_real.make_llm_member (ollama محلی، $0، روتینگ summarize)
  · استاب: همان opinion_fnهای شورای معماری (کنترل)
سنجه:
  تفکیک عضو واقعی = سهمِ جفت‌هایی که confidence(درست) > confidence(نویز)
  تفکیک استاب = همان محاسبه روی خروجی استاب (انتظار: ۰ — خروجی ثابت)
سنجهٔ جانبی: نرخ parse موفق عضو واقعی (قرارداد JSON سخت) و تفاوتِ متن نظر.
"""
import json
import random
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYS4D = HERE.parents[2] / "4d_system"
sys.path.insert(0, str(SYS4D))

# پیش‌گاردِ بودجه: اگر اولاما پایین بود، روتر به ابرِ پولی فال‌بک می‌کند — توقف.
import urllib.request  # noqa: E402

try:
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=4):
        pass
except Exception as e:  # noqa: BLE001
    print(json.dumps({"test": "S3", "status": "ABORTED",
                      "reason": f"ollama down — اجرا یعنی فال‌بک پولی: {e}"}))
    sys.exit(2)

from councils_real import make_llm_member  # noqa: E402
from councils.councils_phase1 import ArchitectureCouncil  # noqa: E402

DB = SYS4D / "outputs" / "4d_experiments.db"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
rows = con.execute(
    "SELECT id, hypothesis FROM hypotheses WHERE status='pending' AND tested=0"
    " AND hypothesis IS NOT NULL AND length(hypothesis) >= 60"
    " ORDER BY timestamp DESC LIMIT 40").fetchall()
con.close()

rng = random.Random(20260816)
pairs = []
for r in rows:
    words = str(r["hypothesis"]).split()
    if len(words) < 8:
        continue
    shuffled = words[:]
    while shuffled == words:
        rng.shuffle(shuffled)
    pairs.append({"hyp_id": r["id"], "correct": r["hypothesis"],
                  "noise": " ".join(shuffled)})
    if len(pairs) == 10:
        break

stub_council = ArchitectureCouncil()
stub_fns = [m._fn for m in stub_council.members]

res = {"test": "S3-council-discrimination", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "pairs": len(pairs), "real": [], "stub": []}

real_hits = real_ties = real_miss = parse_ok = parse_fail = 0
for i, p in enumerate(pairs):
    member = make_llm_member(name=f"s3-real-{i}", max_calls=2)
    out_c = member.opine({"task": {"kind": "hypothesis-review", "q": p["correct"]}})
    out_n = member.opine({"task": {"kind": "hypothesis-review", "q": p["noise"]}})
    parseable = ("__" not in str(out_c["opinion"])) and ("__" not in str(out_n["opinion"]))
    parse_ok += parseable
    parse_fail += (not parseable)
    cc, cn = out_c["confidence"], out_n["confidence"]
    if cc > cn:
        real_hits += 1
    elif cc == cn:
        real_ties += 1
    else:
        real_miss += 1
    res["real"].append({
        "hyp_id": p["hyp_id"], "conf_correct": cc, "conf_noise": cn,
        "parse_ok": parseable,
        "op_c": str(out_c["opinion"])[:90], "op_n": str(out_n["opinion"])[:90]})
    print(f"pair {i+1}: correct={cc:.2f} noise={cn:.2f} "
          f"{'HIT' if cc > cn else ('TIE' if cc == cn else 'MISS')} "
          f"{'· parse-ok' if parseable else '· PARSE-FAIL'}")

stub_hits = stub_ties = 0
for i, p in enumerate(pairs):
    outs = [(fn({"task": {"kind": "hypothesis-review", "q": p["correct"]}}),
             fn({"task": {"kind": "hypothesis-review", "q": p["noise"]}}))
            for fn in stub_fns]
    for oc, on in outs:
        if oc["confidence"] > on["confidence"]:
            stub_hits += 1
        elif oc["confidence"] == on["confidence"]:
            stub_ties += 1
    res["stub"].append({"hyp_id": p["hyp_id"],
                        "stub_pair_identical": [str(oc["opinion"])[:40] == str(on["opinion"])[:40]
                                                for oc, on in outs]})

n_stub_calls = len(pairs) * len(stub_fns)
res["summary"] = {
    "real_member": {"hits": real_hits, "ties": real_ties, "misses": real_miss,
                    "n": len(pairs),
                    "discrimination_rate": round(real_hits / len(pairs), 3),
                    "parse_success": f"{parse_ok}/{parse_ok + parse_fail}"},
    "stub_control": {"hits": stub_hits, "ties": stub_ties,
                     "n_calls": n_stub_calls,
                     "discrimination_rate": round(stub_hits / n_stub_calls, 3)},
    "verdict_rule": "REAL اگر تفکیک عضو واقعی > استاب با فاصلهٔ معنادار؛ برابر ⇒ عضو تزئین",
}

(HERE / "result-s3.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res["summary"], ensure_ascii=False, indent=1))
