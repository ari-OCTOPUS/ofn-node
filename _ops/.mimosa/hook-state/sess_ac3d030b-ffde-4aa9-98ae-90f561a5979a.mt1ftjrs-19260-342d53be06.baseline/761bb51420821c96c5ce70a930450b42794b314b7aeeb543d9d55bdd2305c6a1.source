#!/usr/bin/env python3
"""ignition_softwta.py — بک‌لاگِ ۲۰۲۷ #۶: گیتِ ignition ِ گلوگاه-رقابت با soft-WTA — **فقط سایه**.

پیش‌شرطِ ساخت (رأی مالک): «فقط اگر replay پاس شد، #۶ را بساز؛ آن هم فقط shadow-only با
IGNITION_SOFT_WTA_SHADOW=1 و IGNITION_SOFT_WTA_LIVE=0.» → دروازهٔ replay در
[[2027 Standards Base & Backlog §۵]] PASS شد (۲۰۲۶-۰۷-۱۱, commit b1a0f08).

طراحی طبقِ اسپکِ خودِ مالک + استانداردها (Goyal-Bengio 2103.01197، Blum&Blum CTM — soft-WTA
با softmax/τ به‌جای argmax ِ سخت):

    score(c) = w_heart·salience + w_owner·owner_attention + w_discovery·novelty
             + w_blocked·blockedness + w_epistemic·label_weight
             − w_hype·hype_penalty − w_staleness·age_penalty
    P(c)     = softmax(score/τ)
    شلیک فقط اگر: p_best > floor  و  (p_best − p_runner) > margin   (همه-یا-هیچ)

مرزهای سخت:
  - **ماژولِ جداگانه** — `ignition.py` (منطقِ زندهٔ فعلی) یک بایت هم عوض نشده؛ این فایل فقط
    از آن *می‌خواند* (gather_candidates/select_winner). additive ِ مطلق، بدونِ بازنویسی.
  - `IGNITION_SOFT_WTA_SHADOW=1` → فقط ثبتِ رکوردِ سایه در
    `state/cortex/ignition-softwta-shadow.jsonl`. بدونِ فلگ → هیچ نوشتنی (no-op ِ کامل).
  - `IGNITION_SOFT_WTA_LIVE` در این فاز **هرگز رفتار نمی‌سازد** — فقط در رکورد echo می‌شود
    تا اگر روزی روشن شد، در سایه دیده شود. مسیرِ live = فازِ بعد، فقط با رأیِ مالک.
  - گاردِ #۳: نامزدِ block-شده (ادعای phenomenal) از رقابتِ سایه حذف؛ needs_review جریمهٔ نرم.
  - مرزِ معرفتی: access-only — رقابت/پخش = مسیریابیِ دسترسی، هرگز ادعای آگاهی.

$0 · stdlib · fail-soft · خالص (I/O فقط در shadow_compare با مسیرِ تزریق‌پذیر).
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import ignition as ig  # noqa: E402 — فقط خواندن؛ هیچ monkey-patch/بازنویسی

if str(_HERE.parent / "epistemics") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "epistemics"))
import guard_review  # noqa: E402

SCHEMA = "ignition-softwta-shadow.v1"
FLAG_SHADOW = "IGNITION_SOFT_WTA_SHADOW"
FLAG_LIVE = "IGNITION_SOFT_WTA_LIVE"      # رزرو — در این فاز فقط echo، هرگز رفتار
SHADOW_PATH = opslib.STATE_DIR / "cortex" / "ignition-softwta-shadow.jsonl"

# برچسبِ منبع — همان نگاشتِ replay (تک‌تعریف در دو لایهٔ سایه؛ سیم‌کشیِ مشترک = فازِ بعد)
SOURCE_LABELS = {"stress": "fact", "dead_spot": "fact", "owner_wait": "fact"}
LABEL_WEIGHT = {"fact": 1.0, "emerging": 0.6, "hype": 0.0}


def _envf(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def weights() -> dict:
    """وزن‌ها/پارامترها — env-tunable ($0، برگشت‌پذیر)، پیش‌فرض‌های مستند."""
    return {
        "w_heart": _envf("SOFTWTA_W_HEART", 1.0),          # سیگنالِ پایه (salience ِ اندازه‌گیری‌شده)
        "w_owner": _envf("SOFTWTA_W_OWNER", 0.25),         # boost ِ توجهِ مالک — نه override
        "w_discovery": _envf("SOFTWTA_W_DISCOVERY", 0.15), # تازگیِ کشف (بالا-به-پایین)
        "w_blocked": _envf("SOFTWTA_W_BLOCKED", 0.20),     # نقطهٔ مرده/گیر — پایین-به-بالا
        "w_epistemic": _envf("SOFTWTA_W_EPISTEMIC", 0.20), # fact > emerging > hype
        "w_hype": _envf("SOFTWTA_W_HYPE", 0.50),           # جریمهٔ hype (هرگز برنده نسازد)
        "w_staleness": _envf("SOFTWTA_W_STALENESS", 0.10), # فرسایشِ کهنگی (age_h اختیاری)
        "tau": max(1e-3, _envf("SOFTWTA_TAU", 0.15)),      # دمای softmax (کوچک‌تر = تیزتر)
        "floor": _envf("SOFTWTA_FLOOR", 0.40),             # کفِ همه-یا-هیچ روی p_best
        "margin": _envf("SOFTWTA_MARGIN", 0.10),           # حاشیهٔ برنده − نفرِ دوم
        "top_k": int(_envf("SOFTWTA_TOP_K", 3)),
    }


def label_of(cand: dict) -> str:
    lbl = str(cand.get("epistemic_label") or "").strip().lower()
    if lbl in LABEL_WEIGHT:
        return lbl
    return SOURCE_LABELS.get(str(cand.get("kind")), "emerging")


def score_candidate(cand: dict, w: "dict | None" = None) -> dict:
    """اجزای score ِ یک نامزد — شفاف و قابلِ‌ممیزی (هر جزء جدا گزارش می‌شود)."""
    w = w or weights()
    base = max(0.0, min(1.0, float(cand.get("salience", 0.0) or 0.0)))
    owner = 1.0 if cand.get("kind") == "owner_wait" else 0.0
    disc = 1.0 if cand.get("source") == "discovery" else 0.0
    blocked = 1.0 if cand.get("kind") == "dead_spot" else 0.0
    lbl = label_of(cand)
    g = guard_review.classify_access_only(str(cand.get("summary", "")))
    epi = LABEL_WEIGHT[lbl] * (0.5 if g["result"] == "needs_review" else 1.0)
    hype_pen = 1.0 if lbl == "hype" else 0.0
    try:
        age_h = max(0.0, float(cand.get("age_h", 0.0) or 0.0))
    except (TypeError, ValueError):
        age_h = 0.0
    stale_pen = min(1.0, age_h / 24.0)                     # اشباع در یک شبانه‌روز
    # boost ِ اشباع‌شونده (درسِ تستِ boost-not-override): سهمِ توجه/کشف/گیر با (1−base) ضرب
    # می‌شود — به نامزدِ کم‌salience کمک می‌کند، نامزدِ از-قبل-قوی را باد نمی‌کند؛ پس توجهِ
    # مالک (۰٫۸۵ ثابت) هرگز سیگنالِ قوی‌ترِ واقعی (مثلاً استرسِ ۰٫۹۰) را override نمی‌کند.
    headroom = 1.0 - base
    s = (w["w_heart"] * base
         + w["w_owner"] * owner * headroom
         + w["w_discovery"] * disc * headroom
         + w["w_blocked"] * blocked * headroom
         + w["w_epistemic"] * epi
         - w["w_hype"] * hype_pen - w["w_staleness"] * stale_pen)
    return {"key": f"{cand.get('source', '?')}:{cand.get('kind', '?')}",
            "score": round(s, 4), "base": base, "owner": owner, "discovery": disc,
            "blocked": blocked, "epistemic_label": lbl, "epistemic_w": round(epi, 3),
            "hype_penalty": hype_pen, "staleness_penalty": round(stale_pen, 3),
            "guard_result": g["result"]}


def softmax(scores: list[float], tau: float) -> list[float]:
    """softmax ِ عددی-پایدار (کم‌کردنِ بیشینه) — همیشه جمع=۱، بدونِ overflow."""
    if not scores:
        return []
    mx = max(scores)
    exps = [math.exp((s - mx) / tau) for s in scores]
    z = sum(exps) or 1.0
    return [e / z for e in exps]


def soft_wta(candidates: list[dict], w: "dict | None" = None) -> dict:
    """رقابتِ soft-WTA روی نامزدها (خالص). گاردِ #۳: block → حذف از رقابتِ سایه."""
    w = w or weights()
    scored = [score_candidate(c, w) for c in candidates]
    passing = [s for s in scored if s["guard_result"] != "block"]
    excluded = [s["key"] for s in scored if s["guard_result"] == "block"]
    if not passing:
        return {"winner": None, "ignited": False, "probs": [], "top_k": [],
                "decision_entropy": 0.0, "entropy_norm": 0.0, "excluded_by_guard": excluded}
    probs = softmax([s["score"] for s in passing], w["tau"])
    ranked = sorted(zip(passing, probs), key=lambda t: t[1], reverse=True)
    p_best = ranked[0][1]
    p_runner = ranked[1][1] if len(ranked) > 1 else 0.0
    ignited = (p_best > w["floor"]) and ((p_best - p_runner) > w["margin"])
    ent = -sum(p * math.log(p) for _, p in ranked if p > 0)
    ent_norm = ent / math.log(len(ranked)) if len(ranked) > 1 else 0.0
    return {
        "winner": ranked[0][0]["key"] if ignited else None,
        "best_key": ranked[0][0]["key"], "p_best": round(p_best, 4),
        "p_runner": round(p_runner, 4), "ignited": ignited,
        "probs": [{"key": s["key"], "p": round(p, 4), "score": s["score"],
                   "epistemic_label": s["epistemic_label"], "guard_result": s["guard_result"]}
                  for s, p in ranked],
        "top_k": [s["key"] for s, _ in ranked[: max(1, w["top_k"])]],
        "decision_entropy": round(ent, 4), "entropy_norm": round(ent_norm, 4),
        "excluded_by_guard": excluded,
    }


def shadow_enabled() -> bool:
    return os.environ.get(FLAG_SHADOW, "0") == "1"


def shadow_compare(candidates: "list[dict] | None" = None,
                   reentry: "dict | None" = None,
                   out_path: "Path | None" = None) -> dict:
    """یک مقایسهٔ سایه: برندهٔ منطقِ *فعلی* (ignition.select_winner، دست‌نخورده) در برابرِ
    برندهٔ soft-WTA. فقط با IGNITION_SOFT_WTA_SHADOW=1 روی دیسک append می‌کند؛ رفتارِ
    زنده در هر حالتی همان مسیرِ فعلی می‌ماند (این تابع را هیچ مسیرِ زنده‌ای صدا نمی‌زند)."""
    cands = ig.gather_candidates() if candidates is None else candidates
    current = ig.select_winner(cands, reentry)              # منطقِ فعلی — مرجعِ رفتار
    cur_w = (current.get("winner") or {}).get("key")
    soft = soft_wta(cands)
    rec = {
        "ts": opslib.now_iso(), "schema": SCHEMA, "epistemic": "access-only",
        "n_candidates": len(cands),
        "winner_current": cur_w,
        "winner_soft_wta_shadow": soft["winner"],
        "disagreement": bool(cur_w != soft["winner"]),
        "current_ignited": bool(current.get("ignited")),
        "soft": {k: soft[k] for k in ("ignited", "p_best", "p_runner", "top_k",
                                      "decision_entropy", "entropy_norm",
                                      "excluded_by_guard") if k in soft},
        "probs": soft.get("probs", []),
        "live_flag_echo": os.environ.get(FLAG_LIVE, "0"),   # فقط echo — هرگز رفتار
        "note": "shadow-only: رفتارِ زنده = winner_current (منطقِ فعلی)؛ soft-WTA فقط ثبت می‌شود",
    }
    if shadow_enabled():
        p = out_path or SHADOW_PATH
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass                                            # fail-soft — سایه هرگز چیزی را نمی‌کشد
    return rec


if __name__ == "__main__":
    demo = [
        {"source": "money", "kind": "stress", "salience": 0.90, "summary": "spend near cap"},
        {"source": "attention", "kind": "owner_wait", "salience": 0.85, "summary": "approval pending"},
        {"source": "discovery", "kind": "learn", "salience": 0.50,
         "epistemic_label": "hype", "summary": "unverified capability claim"},
    ]
    print(json.dumps(shadow_compare(demo), ensure_ascii=False, indent=1))
