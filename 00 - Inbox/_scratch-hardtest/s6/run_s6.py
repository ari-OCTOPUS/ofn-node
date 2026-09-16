# -*- coding: utf-8 -*-
"""S6 — لبهٔ پیش‌بینی واقعی (HARD-TEST) — پیگیری یافتهٔ هولداوت L1.

فرضیهٔ صفر: مدل پیش‌بینی (p_base) هیچ لبه‌ای بر نرخ پایه ندارد.
  (الف) پویشِ post-hoc زیرمجموعه‌ها — «اعلام: post-hoc است؛ برنده‌های تکی
        среди چند مقایسه می‌توانند شانسی باشند» (تعداد مقایسه‌ها گزارش می‌شود)
  (ب) مسیر بهبود: روان‌ساز exponential روی y_rate_hist / y_{t-1} با
      پروتکل درست: انتخاب پارامتر فقط روی train (۷۰٪ اول)، داوری روی
      test (۳۰٪ آخر) — همان تله‌ای که هولداوت گرفت، اینجا نمی‌گیرد.
عددهای سرREFERENCE: PHASE02 — base-rate بری‌ری 0.0829 (کل ۳۵۱) در برابر
مدل ثبت‌شده 0.0978؛ روی ۶۰ فریز: 0.1310 در برابر 0.1337.
"""
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:/Users/Armin/Desktop/OCTOPUS-NBB-CP-WORKING/nbb-control-plane"
           r"/_ops/observatory/scripts/backtest-hardtask-results.json")
rows = json.loads(SRC.read_text(encoding="utf-8"))["rows"]
rows.sort(key=lambda r: r["date"])
BASE = mean(r["y"] for r in rows)


def brier(preds):
    return sum((p - y) ** 2 for p, y in preds) / len(preds)


res = {"test": "S6-prediction-edge", "n": len(rows), "base_rate": round(BASE, 4)}

# ── بازتولید عددهای مرجع ────────────────────────────────────────────────
res["reference_all351"] = {
    "brier_model_p_base": round(brier([(r["p_base"], r["y"]) for r in rows]), 4),
    "brier_constant_baserate": round(brier([(BASE, r["y"]) for r in rows]), 4),
}

# بستهٔ ۶۰تایی فریز: item_id → date → p_base (join با چندگانگی تاریخ)
HOLD = json.loads((HERE.parents[2] / "_ops" / "evaluator-holdout"
                   / "holdout_items.json").read_text(encoding="utf-8"))["items"]
from collections import defaultdict  # noqa: E402

by_date = defaultdict(list)
for r in rows:
    by_date[r["date"]].append(r)
used = defaultdict(int)
sub60 = {}
missing = 0
for it in HOLD:
    cand = by_date.get(it["observable"]["date"], [])
    i = used[it["observable"]["date"]]
    if i < len(cand):
        sub60[it["item_id"]] = cand[i]
        used[it["observable"]["date"]] += 1
    else:
        missing += 1
res["reference_60frozen"] = {
    "matched": len(sub60), "missing_date_join": missing,
    "brier_model": round(brier([(r["p_base"], r["y"])
                                for r in sub60.values()]), 4) if sub60 else None,
    "brier_baserate": round(brier([(BASE, r["y"])
                                   for r in sub60.values()]), 4) if sub60 else None,
}

# ── (الف) پویش post-hoc زیرمجموعه‌ها ────────────────────────────────────
subsets = []


def add(name, pred):
    subsets.append((name, pred))


# دوره‌های زمانی (هشتم‌ها و نیمه‌ها)
n = len(rows)
for k in (2, 4, 8):
    for i in range(k):
        seg = rows[i * n // k:(i + 1) * n // k]
        add(f"period/{k}ths[{i}]", [(r["p_base"], r["y"]) for r in seg])
# باند y_rate_hist
bands = [(0.0, 0.001, "rate=0"), (0.001, 0.5, "rate∈(0,0.5)"),
         (0.5, 0.9, "rate∈[0.5,0.9)"), (0.9, 0.9999, "rate∈[0.9,1)"),
         (0.9999, 1.1, "rate=1")]
for lo, hi, name in bands:
    seg = [r for r in rows if lo <= r["y_rate_hist"] < hi]
    if len(seg) >= 15:
        add(f"y_rate_hist/{name}", [(r["p_base"], r["y"]) for r in seg])
# باند p_base خود مدل
for lo, hi, name in [(0.0, 0.51, "p=0.5"), (0.51, 0.9, "p∈(0.5,0.9)"),
                     (0.9, 1.01, "p≥0.9")]:
    seg = [r for r in rows if lo <= r["p_base"] < hi]
    if len(seg) >= 15:
        add(f"p_base_band/{name}", [(r["p_base"], r["y"]) for r in seg])

scan = []
for name, pred in subsets:
    if len(pred) < 15:
        continue
    bm = brier(pred)
    bb = brier([(BASE, y) for _, y in pred])
    scan.append({"subset": name, "n": len(pred),
                 "brier_model": round(bm, 4), "brier_baserate": round(bb, 4),
                 "delta_model_minus_base": round(bm - bb, 4)})
winners = [s for s in scan if s["delta_model_minus_base"] < 0]
res["posthoc_subset_scan"] = {
    "declared_posthoc": True,
    "n_comparisons": len(scan),
    "n_subsets_model_wins": len(winners),
    "best_for_model": min(scan, key=lambda s: s["delta_model_minus_base"]),
    "worst_for_model": max(scan, key=lambda s: s["delta_model_minus_base"]),
    "winners": winners,
    "multiplicity_note": f"با {len(scan)} مقایسه، چند برندهٔ تکی خودبه‌خود "
                         f"انتظار می‌رود؛ برنده فقط با اندازهٔ نمونهٔ کافی و "
                         f"دلتای منفیِ درشت معنادار است",
}

# ── (ب) مسیر بهبود — روان‌ساز exponential، انتخاب روی train فقط ─────────
SPLIT = int(n * 0.7)
train, test = rows[:SPLIT], rows[SPLIT:]
BASE_TRAIN = mean(r["y"] for r in train)


def run_smoother(alpha, source):
    """p_t = α·منبع(lag-1) + (1-α)·p_{t-1} · p_0 = نرخ پایهٔ train
    منبع: y_{t-1} (بلافاصله بعد از پیش‌بینیِ t آپدیت می‌شود ⇒ lag-1 درست)
    یا y_rate_hist (خودش تجمعیِ تا t-1 است)"""
    p = BASE_TRAIN
    out = []
    for r in rows:
        out.append((p, r["y"]))
        lag = r["y"] if source == "y_lag" else r["y_rate_hist"]
        p = alpha * lag + (1 - alpha) * p
    return out


best = {"name": None, "test_brier": None, "alpha": None, "train_brier": None}
table = []
for source in ("y_lag", "rate"):
    for alpha in [0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]:
        full = run_smoother(alpha, source)
        tr = brier(full[:SPLIT])
        te = brier(full[SPLIT:])
        table.append({"source": source, "alpha": alpha,
                      "train_brier": round(tr, 4), "test_brier": round(te, 4)})
        if best["name"] is None or tr < best["train_brier"]:
            best = {"name": source, "alpha": alpha, "train_brier": round(tr, 4),
                    "test_brier": round(te, 4)}
test_base_const = brier([(BASE_TRAIN, r["y"]) for r in test])
test_base_true = brier([(mean(r["y"] for r in test), r["y"]) for r in test])
test_model = brier([(r["p_base"], r["y"]) for r in test])
res["improvement_path"] = {
    "protocol": "انتخاب α فقط روی train (۷۰٪ اول)؛ داوری روی test (۳۰٪ آخر، زمانی)",
    "best_by_train": best,
    "test_brier_best_smoother": best["test_brier"],
    "test_brier_constant_train_baserate": round(test_base_const, 4),
    "test_brier_constant_test_baserate_oracle": round(test_base_true, 4),
    "test_brier_registered_model_p_base": round(test_model, 4),
    "smoother_beats_baserate_onsample": best["test_brier"] < test_base_const,
    "smoother_beats_oracle_baserate": best["test_brier"] < test_base_true,
    "table": table,
    "note": "oracle = نرخ پایهٔ محاسبه‌شده روی خودِ test (چیده‌شده) — شکستنِ "
            "این سقف یعنی سیگنالِ واقعی بالاتر از «همیشه ۹۱٪ بگو»",
}

(HERE / "result-s6.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in res.items()
                  if k not in ("improvement_path",)}, ensure_ascii=False, indent=1))
print("improvement best:", json.dumps(
    {k: res["improvement_path"][k] for k in
     ("best_by_train", "test_brier_best_smoother",
      "test_brier_constant_train_baserate",
      "test_brier_constant_test_baserate_oracle",
      "test_brier_registered_model_p_base",
      "smoother_beats_baserate_onsample", "smoother_beats_oracle_baserate")},
    ensure_ascii=False, indent=1))
