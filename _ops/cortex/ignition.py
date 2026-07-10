#!/usr/bin/env python3
"""ignition.py — پرایمریتِ غایبِ GNWT: رقابت + آتش‌گیری (ignition) + بازورود (re-entry).

رأی مالک (۲۰۲۶-۰۷-۱۱، تحقیقِ نوروساینس/آگاهی): فضای کاریِ سراسری (Global Workspace)
باید واقعی شود. امروز کورتکس همهٔ اندام‌ها را ثابت‌ترتیب اجرا می‌کند و چیزی «برنده»
نمی‌شود. این ماژول همان مکانیزمِ تعیین‌کننده را می‌سازد:

  ۱) رقابت (competition): محتواهای نامزدِ واقعیِ فضای کاری — استرسِ هر زیرسیستم (تهدید،
     پایین-به-بالا)، نقاطِ مرده، کشف/یادگیریِ تازه (نو، بالا-به-پایین)، و توجهِ مالک
     (blocked/approval) — بر سرِ فضای کاری رقابت می‌کنند؛ salience هرکدام ۰..۱.
  ۲) آتش‌گیری (ignition): فقط اگر برندهٔ effective از آستانه بگذرد، «ignite» می‌شود و
     تک‌برنده به همهٔ مشترک‌ها پخش می‌شود (winner-take-all). وگرنه چرخهٔ خاموش.
  ۳) بازورود (re-entry): برندهٔ این چرخه به‌عنوان priorِ کوچکِ رو-به-فرسایش، salienceِ
     همان محتوا را در چرخهٔ بعد تقویت می‌کند → حلقهٔ بازخوردیِ ماندگار، نه feed-forward.

سیگنال‌های سنجش: ignition_rate (کسرِ چرخه‌های ignite)، broadcast_width (اندازهٔ ائتلاف)،
stability (چند چرخه برندهٔ یکسان).

مرزِ معرفتی: این فقط **access-consciousness** را مدل می‌کند (دسترس‌پذیری/پخشِ سراسری) —
هرگز phenomenal/qualia. هر متریک یک سنجهٔ مهندسی است، نه شاهدِ تجربهٔ ذهنی.

propose-only + flag-gated: تا `CORTEX_IGNITION=1` نباشد، `persist()` هیچ‌کاری نمی‌کند و
رفتارِ کورتکسِ زنده تغییر نمی‌کند. هستهٔ توابع خالص و مستقیم آزمون‌پذیر است.
$0 · stdlib · fail-soft · بی‌محتوا.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
LATEST = STATE / "cortex" / "ignition-latest.json"

# پارامترها (env-override برای تنظیمِ shadow؛ همه بی‌هزینه)
IGNITION_THRESHOLD = float(os.environ.get("CORTEX_IGNITION_THRESHOLD", "0.5"))  # آستانهٔ آتش‌گیری
REENTRY_GAIN = 0.15    # تقویتِ prior برنده برای چرخهٔ بعد
REENTRY_DECAY = 0.6    # فرسایشِ prior هر چرخه (تا برنده تا ابد قفل نشود)
REENTRY_CAP = 0.4      # سقفِ boostِ بازورود (نمی‌گذارد رقابت بی‌معنی شود)
COALITION_FRAC = 0.6   # عضوِ ائتلافِ برنده = هرکه effective ≥ این کسر × برنده
RATE_WINDOW = 20       # پنجرهٔ رولینگِ ignition_rate


def enabled() -> bool:
    """propose-only: تا مالک این فلگ را روشن نکند (رستارت) هیچ اثری روی کورتکسِ زنده ندارد."""
    return os.environ.get("CORTEX_IGNITION", "0") == "1"


def _key(c: dict) -> str:
    """کلیدِ پایدارِ یک نامزد (خطِ نسبِ بازورود روی همین کلید است)."""
    return f"{c.get('source', '?')}:{c.get('kind', '?')}"


def effective_salience(candidates: list[dict], reentry_prior: dict | None) -> list[dict]:
    """salienceِ مؤثر = پایه + boostِ بازوروِد (مقیدِ سقف)، مرتب‌شده نزولی."""
    rp = reentry_prior or {}
    out = []
    for c in candidates:
        base = max(0.0, min(1.0, float(c.get("salience", 0.0))))
        boost = min(REENTRY_CAP, max(0.0, float(rp.get(_key(c), 0.0))))
        e = dict(c)
        e["base_salience"] = round(base, 3)
        e["reentry_boost"] = round(boost, 3)
        e["effective"] = round(min(1.0, base + boost), 3)
        e["key"] = _key(c)
        out.append(e)
    out.sort(key=lambda x: x["effective"], reverse=True)
    return out


def select_winner(candidates: list[dict], reentry_prior: dict | None = None,
                  threshold: float | None = None) -> dict:
    """رقابت + آتش‌گیریِ تک‌برنده. اگر برندهٔ effective از آستانه نگذرد → چرخهٔ خاموش."""
    thr = IGNITION_THRESHOLD if threshold is None else threshold
    ranked = effective_salience(candidates, reentry_prior)
    if not ranked:
        return {"ignited": False, "winner": None, "broadcast_width": 0,
                "margin": 0.0, "ranked": []}
    top = ranked[0]
    ignited = top["effective"] >= thr
    if not ignited:
        return {"ignited": False, "winner": None, "broadcast_width": 0,
                "margin": round(thr - top["effective"], 3), "ranked": ranked}
    # اندازهٔ ائتلاف = محتواهای هم‌فعال که با برنده pluralityِ پخش می‌سازند
    coalition = [r for r in ranked if r["effective"] >= COALITION_FRAC * top["effective"]]
    runner = ranked[1]["effective"] if len(ranked) > 1 else 0.0
    return {"ignited": True, "winner": top, "broadcast_width": len(coalition),
            "margin": round(top["effective"] - runner, 3), "ranked": ranked}


def next_reentry(reentry_prior: dict | None, winner_key: str | None) -> dict:
    """بازورود: prior قدیمی فرسایش می‌یابد، برنده تقویت می‌شود (حلقهٔ بازخوردی)."""
    rp = dict(reentry_prior or {})
    decayed = {k: round(v * REENTRY_DECAY, 4) for k, v in rp.items() if v * REENTRY_DECAY >= 0.01}
    if winner_key:
        decayed[winner_key] = round(min(REENTRY_CAP, decayed.get(winner_key, 0.0) + REENTRY_GAIN), 4)
    return decayed


def _metrics(prev: dict, ignited: bool, winner_key: str | None) -> dict:
    recent = list(prev.get("recent_ignitions", []))[-(RATE_WINDOW - 1):] + [1 if ignited else 0]
    rate = round(sum(recent) / max(1, len(recent)), 3)
    prev_key = (prev.get("winner") or {}).get("key")
    stability = (prev.get("stability", 0) + 1) if (ignited and winner_key == prev_key) else (1 if ignited else 0)
    return {"ignition_rate": rate, "stability": stability, "recent_ignitions": recent}


def gather_candidates() -> list[dict]:
    """محتواهای نامزدِ فضای کاری از stateِ زنده (استرسِ زیرسیستم‌ها، نقاطِ مرده). fail-soft/بی‌محتوا."""
    cands: list[dict] = []
    # استرسِ هر زیرسیستم = salienceِ پایین‌به‌بالا (تهدید)
    try:
        s = json.loads((STATE / "cortex" / "stress-latest.json").read_text("utf-8"))
        for sid, v in (s.get("subsystems") or {}).items():
            cands.append({"source": sid, "kind": "stress",
                          "salience": float(v.get("stress", 0.0)),
                          "summary": v.get("name", sid)})
    except (OSError, ValueError, TypeError):
        pass
    # نقاطِ مردهٔ عصب‌کشی = salienceِ بالا (چیزی beat نمی‌خورد)
    try:
        nv = json.loads((STATE / "cortex" / "innervation-latest.json").read_text("utf-8"))
        for name in (nv.get("dead_spots") or []):
            cands.append({"source": "innervation", "kind": "dead_spot",
                          "salience": 0.8, "summary": str(name)})
    except (OSError, ValueError, TypeError):
        pass
    # کشف/یادگیریِ تازه = محتوای نو که برای توجه رقابت می‌کند (recency-weighted، بالا-به-پایین)
    try:
        import time as _t
        dp = STATE / "discoveries.jsonl"
        if dp.exists():
            rows = [json.loads(l) for l in dp.read_text("utf-8").splitlines()[-10:] if l.strip()]
            now = _t.time()
            for r in rows[-3:]:
                age_h = max(0.0, (now - float(r.get("ts", 0))) / 3600.0)
                sal = round(max(0.2, 0.55 - 0.05 * age_h), 3)   # تازه‌تر = برجسته‌تر، فرسایشِ ملایم
                cands.append({"source": "discovery", "kind": str(r.get("kind", "learn"))[:12],
                              "salience": sal, "summary": str(r.get("summary", ""))[:80]})
    except (OSError, ValueError, TypeError):
        pass
    # چیزی که منتظرِ مالک است یا گیر کرده = برجستگیِ پایین-به-بالا (جدیدترین)
    try:
        ep = STATE / "events.jsonl"
        if ep.exists():
            for l in reversed(ep.read_text("utf-8").splitlines()[-60:]):
                try:
                    e = json.loads(l)
                except ValueError:
                    continue
                if e.get("event_name") == "task.blocked" or e.get("approval_state") == "required":
                    cands.append({"source": "attention", "kind": "owner_wait",
                                  "salience": 0.85, "summary": str(e.get("summary", ""))[:80]})
                    break
    except (OSError, ValueError, TypeError):
        pass
    return cands


def step(prev: dict, candidates: list[dict] | None = None) -> dict:
    """یک چرخهٔ فضای کاری: رقابت → آتش‌گیری → بازورود + متریک. خالص نسبت به prev/candidates."""
    cands = gather_candidates() if candidates is None else candidates
    rp = prev.get("reentry_prior") or {}
    sel = select_winner(cands, reentry_prior=rp)
    winner = sel["winner"]
    winner_key = winner["key"] if winner else None
    m = _metrics(prev, sel["ignited"], winner_key)
    return {
        "ts": opslib.now_iso(), "schema": "ignition.v1", "epistemic": "access-only",
        "ignited": sel["ignited"],
        "winner": ({"source": winner["source"], "kind": winner["kind"], "key": winner_key,
                    "effective": winner["effective"], "summary": winner.get("summary", "")}
                   if winner else None),
        "broadcast_width": sel["broadcast_width"], "margin": sel["margin"],
        "n_candidates": len(cands),
        "ignition_rate": m["ignition_rate"], "stability": m["stability"],
        "recent_ignitions": m["recent_ignitions"],
        "reentry_prior": next_reentry(rp, winner_key),
    }


def persist() -> dict:
    """flag-gated: تا CORTEX_IGNITION=1 نباشد no-op است (propose-only). STOP را اول چک می‌کند."""
    if not enabled():
        return {"enabled": False}
    try:
        if opslib.halted():
            return {"enabled": True, "halted": True}
    except Exception:  # noqa: BLE001
        pass
    try:
        prev = json.loads(LATEST.read_text("utf-8")) if LATEST.exists() else {}
    except (OSError, ValueError):
        prev = {}
    rec = step(prev)
    try:
        LATEST.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(LATEST) as lj:
            lj.write(rec)
        # آتش‌گیریِ برندهٔ نو → پخش (edge-triggered، ضدِ اسپم)
        new_key = (rec.get("winner") or {}).get("key")
        prev_key = (prev.get("winner") or {}).get("key")
        if rec["ignited"] and new_key and new_key != prev_key:
            sys.path.insert(0, str(_HERE.parent))
            import events
            events.emit("task.started", "ignition",
                        summary=f"🔥 آتش‌گیری: {rec['winner']['source']} (eff {rec['winner']['effective']}) → پخش به {rec['broadcast_width']}",
                        next_action="فضای کاری: محتوای برنده")
    except Exception as e:  # noqa: BLE001
        opslib.alert([f"ignition persist failed: {e}"])
    return rec


def summary() -> dict:
    try:
        d = json.loads(LATEST.read_text("utf-8"))
    except (OSError, ValueError):
        return {"enabled": enabled(), "ignited": None}
    w = d.get("winner") or {}
    return {"enabled": enabled(), "ignited": d.get("ignited"),
            "winner": w.get("source"), "broadcast_width": d.get("broadcast_width"),
            "ignition_rate": d.get("ignition_rate"), "stability": d.get("stability")}


if __name__ == "__main__":
    demo = [
        {"source": "money", "kind": "stress", "salience": 0.72, "summary": "spend near cap"},
        {"source": "heart", "kind": "stress", "salience": 0.30, "summary": "sigma ok"},
        {"source": "innervation", "kind": "dead_spot", "salience": 0.80, "summary": "cortex dead"},
    ]
    r = step({}, candidates=demo)
    print(json.dumps(r, ensure_ascii=False, indent=2))
