#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_coherence.py — پروبِ انسجام نتواند در سه جهت دروغ بگوید.

`coherence.py` دنبالِ «ادعاهایی که نمی‌توانند غلط باشند» می‌گردد. پس خودش بیش از
هر ماژولِ دیگری در خطرِ همان بیماری است. سه جهتِ دروغ که این تست می‌بندد — و هر سه
را نسخه‌های اولِ خودِ آن ماژول واقعاً مرتکب شدند:

  ۱) **سکوت به‌جای گزارش** — نسخهٔ اول چهار چک را بی‌صدا رد کرد (مسیر/کلید را غلط
     حدس زده بودم) و «۵ چک» گزارش داد که شبیهِ موفقیت بود. حالا نبودِ ورودی یک
     یافتهٔ `no_input` است.
  ۲) **حکم روی دادهٔ کهنه** — نسخهٔ دوم `deadline_proximity = 0.182 (10d)` را «ok»
     اعلام کرد از یک اسنپ‌شاتِ ۱۵ روزه، در حالی که ارگانیسمِ زنده ۰.۹۹۸ و `-5d`
     داشت. حالا سنِ شاهد بخشی از حکم است و «ok»ِ کهنه به `stale` تبدیل می‌شود.
  ۳) **نشانهٔ خوب به‌جای تأیید** — σ=0.0 دلگرم‌کننده است ولی بی‌شکلِ گراف
     دژنره‌نبودن اثبات نمی‌شود. حالا `no_input` می‌دهد نه `ok`.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

import coherence as co  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(msg)


def _sd(files: dict, age_h: float = 0.0):
    """state_dirِ موقت. files: {relpath: obj}. age_h سنِ mtime را عقب می‌برد."""
    d = Path(tempfile.mkdtemp(prefix="coh-"))
    for rel, obj in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False), "utf-8")
        if age_h:
            t = time.time() - age_h * 3600
            import os
            os.utime(p, (t, t))
    return d


def _by(findings, cid):
    for f in findings:
        if f["id"] == cid:
            return f
    return None


# ── T1 · سکوت ممنوع: نبودِ ورودی یافته است ─────────────────────────────────
def t1_no_silence():
    empty = Path(tempfile.mkdtemp(prefix="coh-empty-"))
    r = co.run(root=empty, state_dir=empty)
    ck(r["total"] >= 5, f"T1: با stateِ خالی فقط {r['total']} چک — سکوت کرد")
    ni = [f for f in r["findings"] if f["verdict"] == "no_input"]
    ck(len(ni) >= 4, f"T1: باید ≥۴ no_input بدهد، داد {len(ni)}")
    for f in ni:
        ck(f["evidence"], f"T1: no_inputِ {f['id']} مسیرهای کاندید را نمی‌گوید")
    ck(all(f["verdict"] != "ok" for f in r["findings"] if f["id"].startswith("saturation")),
       "T1: بی‌ورودی «ok» اعلام شد")


# ── T2 · اشباع: عددِ روی سقف اندازه‌گیری نیست ───────────────────────────────
def t2_saturation():
    sd = _sd({"ORGANISM-STATE.json": {"chrono": {"phi": 300.0}}})
    f = _by(co.check_saturation(sd), "saturation:phi")
    ck(f and f["verdict"] == "saturated", f"T2: phi=300 باید saturated باشد ({f})")
    ck(f and f["thesis_row"] == "phi-liveness", "T2: به ردیفِ دفترِ تز وصل نیست")
    for v, want in ((299.9, "saturated"), (299.4, "ok"), (15.99, "ok"), (0.3, "ok")):
        sd = _sd({"ORGANISM-STATE.json": {"chrono": {"phi": v}}})
        g = _by(co.check_saturation(sd), "saturation:phi")
        ck(g and g["verdict"] == want, f"T2: phi={v} → {g['verdict'] if g else '—'}، انتظار {want}")


# ── T3 · دژنره: σ روی گرافِ تهی ─────────────────────────────────────────────
def t3_degenerate():
    sd = _sd({"cortex/cortex-state.json": {"sigma": 1.0, "spectral_gap": 0.0}})
    f = _by(co.check_degenerate_sensor(sd), "degenerate:sigma")
    ck(f and f["verdict"] == "degenerate", f"T3: gap=0 باید degenerate باشد ({f})")
    sd = _sd({"cortex/cortex-state.json": {"sigma": 0.0, "spectral_gap": 0.7321}})
    f = _by(co.check_degenerate_sensor(sd), "degenerate:sigma")
    ck(f and f["verdict"] == "ok", f"T3: gapِ غیرصفر باید ok باشد ({f})")
    # نشانهٔ خوب ≠ تأیید: بی‌شکلِ گراف، ok نمی‌دهد
    sd = _sd({"cortex/cortex-state.json": {"sigma": 0.0}})
    f = _by(co.check_degenerate_sensor(sd), "degenerate:sigma")
    ck(f and f["verdict"] == "no_input",
       f"T3: بی‌شکلِ گراف باید no_input بدهد نه ok ({f['verdict'] if f else '—'})")
    # edges=0 هم دژنره است
    sd = _sd({"cortex/cortex-state.json": {"sigma": 1.0, "n_edges": 0, "n_nodes": 5}})
    f = _by(co.check_degenerate_sensor(sd), "degenerate:sigma")
    ck(f and f["verdict"] == "degenerate", "T3: edges=0 باید degenerate باشد")


# ── T4 · clamp: علامتِ منفی نباید پنهان شود ────────────────────────────────
def t4_clamp():
    sd = _sd({"pulse/heart-shadow-latest.json":
              {"delta_self_raw": -0.027, "delta_self_live": 0.0}})
    f = _by(co.check_self_reference(sd), "clamped:delta_self")
    ck(f and f["verdict"] == "clamped", f"T4: خام منفی + منتشرشده صفر = clamped ({f})")
    sd = _sd({"pulse/heart-shadow-latest.json":
              {"delta_self_raw": -0.027, "delta_self_live": -0.027}})
    f = _by(co.check_self_reference(sd), "clamped:delta_self")
    ck(f and f["verdict"] == "ok", f"T4: منفیِ صادقانه باید ok باشد ({f})")


# ── T5 · خودمرجعی ──────────────────────────────────────────────────────────
def t5_self_reference():
    sd = _sd({"pulse/heart-shadow-latest.json":
              {"metronome_share": 0.96, "authoritative": True}})
    f = _by(co.check_self_reference(sd), "selfref:metronome")
    ck(f and f["verdict"] == "self_referential",
       f"T5: سهمِ ۰.۹۶ با authoritative=True باید گرفته شود ({f})")
    sd = _sd({"pulse/heart-shadow-latest.json":
              {"metronome_share": 0.96, "authoritative": False}})
    f = _by(co.check_self_reference(sd), "selfref:metronome")
    ck(f and f["verdict"] == "ok", "T5: گاردِ فعال باید ok بدهد")


# ── T6 · فوریتِ ابدی ───────────────────────────────────────────────────────
def t6_expired_urgency():
    sd = _sd({"ORGANISM-STATE.json": {"pressure": {
        "deadline_proximity": 0.998, "deadline_ref": "PROJECT_F@2026-07-20 (-5d)"}}})
    f = _by(co.check_expired_urgency(sd), "expired:urgency")
    ck(f and f["verdict"] == "saturated", f"T6: ددلاینِ -5d با ۰.۹۹۸ باید گرفته شود ({f})")
    sd = _sd({"ORGANISM-STATE.json": {"pressure": {
        "deadline_proximity": 0.182, "deadline_ref": "PROJECT_F@2026-07-20 (10d)"}}})
    f = _by(co.check_expired_urgency(sd), "expired:urgency")
    ck(f and f["verdict"] == "ok", f"T6: ددلاینِ آیندهٔ 10d باید ok باشد ({f})")
    # ددلاینِ گذشته ولی فوریتِ صفر (فیکس فعال) → ok
    sd = _sd({"ORGANISM-STATE.json": {"pressure": {
        "deadline_proximity": 0.0, "deadline_ref": "PROJECT_F@2026-07-20 (-5d)"}}})
    f = _by(co.check_expired_urgency(sd), "expired:urgency")
    ck(f and f["verdict"] == "ok", "T6: ددلاینِ گذشته با فوریتِ صفر باید ok باشد")


# ── T7 · کهنگی: «ok» روی دادهٔ کهنه ممنوع ──────────────────────────────────
def t7_staleness():
    ck(co.STALE_AFTER_H > 0, "T7: سقفِ کهنگی تنظیم نشده")
    fresh = _sd({"ORGANISM-STATE.json": {"chrono": {"phi": 0.3}}}, age_h=0.0)
    r = co.run(root=fresh, state_dir=fresh)
    f = _by(r["findings"], "saturation:phi")
    ck(f and f["verdict"] == "ok", f"T7: شاهدِ تازه باید ok بماند ({f})")
    ck(f and f.get("age_h") is not None, "T7: سنِ شاهد ثبت نشده")
    old = _sd({"ORGANISM-STATE.json": {"chrono": {"phi": 0.3}}},
              age_h=co.STALE_AFTER_H + 24)
    r = co.run(root=old, state_dir=old)
    f = _by(r["findings"], "saturation:phi")
    ck(f and f["verdict"] == "stale",
       f"T7: «ok» روی شاهدِ کهنه باید stale شود ({f['verdict'] if f else '—'})")
    ck(f and "کهنه" in f["why"], "T7: دلیلِ stale سنِ شاهد را نمی‌گوید")
    # و یافتهٔ غیرِok با کهنگی درجه‌اش پایین نمی‌آید
    old2 = _sd({"ORGANISM-STATE.json": {"chrono": {"phi": 300.0}}},
               age_h=co.STALE_AFTER_H + 24)
    r = co.run(root=old2, state_dir=old2)
    f = _by(r["findings"], "saturation:phi")
    ck(f and f["verdict"] == "saturated",
       "T7: یافتهٔ saturated نباید با کهنگی به stale تبدیل شود")
    # تازه‌ترین کاندید برنده است، نه اولین
    two = _sd({"export/octopus-status-bundle.json": {"chrono": {"phi": 300.0}}},
              age_h=48)
    fresh_p = two / "ORGANISM-STATE.json"
    fresh_p.write_text(json.dumps({"chrono": {"phi": 0.3}}), "utf-8")
    v, path, age = co._locate(two, "phi", ["export/octopus-status-bundle.json",
                                           "ORGANISM-STATE.json"])
    ck(abs((co._f(v) or -1) - 0.3) < 1e-9,
       f"T7: باید تازه‌ترین را بردارد (۰.۳)، برداشت {v}")


# ── T8 · قاعدهٔ ۱ روی دفترِ تز + fail-soft ─────────────────────────────────
def t8_thesis_and_failsoft():
    sd = _sd({"thesis/thesis-ledger.json": {"rows": [
        {"id": "a", "kill": "اگر تفاوتِ معنادار نساخت رد است", "status": "UNTESTED"},
        {"id": "b", "kill": "—", "status": "UNTESTED"}]}})
    f = _by(co.check_thesis_falsifiability(sd), "thesis:falsifiability")
    ck(f and f["verdict"] == "unfalsifiable", f"T8: ردیفِ بی‌kill باید گرفته شود ({f})")
    ck(f and "b" in str(f["claim"]), "T8: idِ ردیفِ خاطی گزارش نشد")
    sd = _sd({"thesis/thesis-ledger.json": {"rows": [
        {"id": "a", "kill": "اگر تفاوتِ معنادار نساخت رد است", "status": "UNTESTED"}]}})
    f = _by(co.check_thesis_falsifiability(sd), "thesis:falsifiability")
    ck(f and f["verdict"] == "ok", "T8: همه دارای kill باید ok بدهد")
    # fail-soft: JSONِ خراب و مسیرِ ناموجود هرگز raise نمی‌کنند
    bad = Path(tempfile.mkdtemp(prefix="coh-bad-"))
    (bad / "thesis").mkdir()
    (bad / "thesis" / "thesis-ledger.json").write_text("{ not json", "utf-8")
    try:
        r = co.run(root=bad, state_dir=bad)
        ck(isinstance(r, dict) and r["total"] > 0, "T8: run روی دادهٔ خراب چیزی نداد")
    except Exception as e:  # noqa: BLE001
        FAILURES.append(f"T8: run روی دادهٔ خراب raise کرد: {type(e).__name__}")
    # فلگ default-off و خروجی همیشه شکل‌دار
    ck(co.FLAG == "OCTOPUS_WIRE_COHERENCE", "T8: نامِ فلگ عوض شد")
    r = co.run()
    for k in ("findings", "counts", "dishonest", "total"):
        ck(k in r, f"T8: کلیدِ {k} در خروجی نیست")
    ck(all(f["verdict"] in co.VERDICTS for f in r["findings"]),
       "T8: حکمی بیرونِ واژگانِ اعلام‌شده تولید شد")


def main() -> int:
    for fn in (t1_no_silence, t2_saturation, t3_degenerate, t4_clamp,
               t5_self_reference, t6_expired_urgency, t7_staleness,
               t8_thesis_and_failsoft):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            FAILURES.append(f"{fn.__name__}: EXCEPTION {type(e).__name__}: {e}")
    if FAILURES:
        print(f"FAIL {len(FAILURES)}/{CHECKS} — coherence")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print(f"PASS {CHECKS}/{CHECKS} — پروبِ انسجام در سه جهتِ دروغ بسته شد")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
