# -*- coding: utf-8 -*-
"""S3-deepseek — پروب تفکیک روی deepseek-v4-flash (فرمان مالک «برو»، 2026-08-16).

همان طرح S3 (۱۰ فرضیهٔ واقعی از صف زنده + دوقلوی نویز با بذر 20260816)، همان
قرارداد JSON عضو شورا (councils_real._SYSTEM) — فقط صدای عضو این‌بار
deepseek-v4-flash از مسیر تولیدِ خودِ سیستم است (model_router tier=secondary:
گیت organ_gate + circuit breaker + لاگ paid-calls + سقف $20/هفته).

بودجه: سقف سختِ همین اسکریپت = ۲۲ تماس. هدف تصمیم: parse ≥8/10 و تفکیک ≥0.5
(در برابر اولاما: parse 5/10 · تفکیک 0.3).
"""
import json
import random
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYS4D = HERE.parents[2] / "4d_system"
OPS = HERE.parents[2] / "_ops"
sys.path.insert(0, str(SYS4D))
sys.path.insert(0, str(OPS))

# کلیدها از مکانیزم خودِ سیستم — مقدار هرگز چاپ/کپی نمی‌شود
import budget.env_loader as el  # noqa: E402

el.load_env()

from councils_real import _SYSTEM, _extract_json  # noqa: E402
import cortex.model_router as mr  # noqa: E402

HARD_CAP_CALLS = 22

# ── همان جفت‌های S3 (بذر و کوئری یکسان ⇒ قابل‌مقایسهٔ مستقیم) ──────────────
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


def member_opinion(q: str) -> dict:
    prompt = (f"نوع کار: hypothesis-review\nپرسش: {q[:400]}\n"
              f"نظرِ تو به‌عنوان عضو شورا (فقط JSON):")
    r = mr.ask("summarize", prompt, system=_SYSTEM, max_tokens=400,
               tier="secondary")
    text = str(r.get("text") or "") if isinstance(r, dict) else ""
    d = _extract_json(text)
    out = {"ok_call": bool(isinstance(r, dict) and r.get("ok")),
           "tier": r.get("tier") if isinstance(r, dict) else None,
           "model": r.get("model") if isinstance(r, dict) else None,
           "cost_usd": float(r.get("cost_usd") or 0) if isinstance(r, dict) else 0.0,
           "parse_ok": d is not None,
           "conf": float(d.get("confidence", 0.0)) if d else None,
           "opinion": str(d.get("opinion", ""))[:90] if d else
                      (f"__unparseable__ raw[:60]={text[:60]!r}")}
    return out


res = {"test": "S3-deepseek-probe", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "pairs": len(pairs), "calls": [], "budget": {"hard_cap": HARD_CAP_CALLS}}
n_calls = 0
total_cost = 0.0
hits = ties = misses = 0
parse_ok_pairs = 0
for i, p in enumerate(pairs):
    oc = member_opinion(p["correct"])
    on = member_opinion(p["noise"])
    n_calls += 2
    total_cost += oc["cost_usd"] + on["cost_usd"]
    pair_parse = oc["parse_ok"] and on["parse_ok"]
    parse_ok_pairs += pair_parse
    if oc["conf"] is not None and on["conf"] is not None:
        if oc["conf"] > on["conf"]:
            hits += 1
        elif oc["conf"] == on["conf"]:
            ties += 1
        else:
            misses += 1
    res["calls"].append({
        "hyp_id": p["hyp_id"], "pair_parse_ok": pair_parse,
        "conf_correct": oc["conf"], "conf_noise": on["conf"],
        "op_c": oc["opinion"], "op_n": on["opinion"],
        "model": oc["model"], "cost_pair_usd": round(oc["cost_usd"] + on["cost_usd"], 6)})
    print(f"pair {i+1}: correct={oc['conf']} noise={on['conf']} "
          f"parse={'ok' if pair_parse else 'FAIL'} model={oc['model']}")
    if n_calls >= HARD_CAP_CALLS:
        break

res["summary"] = {
    "discrimination": {"hits": hits, "ties": ties, "misses": misses,
                       "rate": round(hits / len(pairs), 3)},
    "parse_full_pairs": f"{parse_ok_pairs}/{len(pairs)}",
    "calls_made": n_calls, "total_cost_usd": round(total_cost, 5),
    "baseline_ollama": {"discrimination": 0.3, "parse": "5/10"},
    "decision_rule": "parse ≥8/10 و تفکیک ≥0.5 ⇒ بودجهٔ بزرگ = اثبات‌شده",
}

(HERE / "result-s3-deepseek.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res["summary"], ensure_ascii=False, indent=1))
