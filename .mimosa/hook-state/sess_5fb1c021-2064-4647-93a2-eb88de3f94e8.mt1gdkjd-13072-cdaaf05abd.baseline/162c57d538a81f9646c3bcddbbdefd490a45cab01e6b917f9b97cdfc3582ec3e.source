#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_thesis_queue.py — سه قاعدهٔ قفل‌شدهٔ دفترِ تز، ساختاری نه توصیه‌ای.

مأموریت: اندامِ ایستادهٔ اثبات (رأیِ مالک 2026-07-25) نتواند در سه جهت دروغ بگوید:
  ۱) ردیفِ بی‌شرطِ مرگ را وارد صف کند،
  ۲) وضعیت را بدونِ شاهدِ واقعی عوض کند،
  ۳) ردیفِ ابطال‌شده را حذف/بازنویسی کند.
به‌علاوه: گاردِ ادعای پدیدارشناختی، صداقتِ «آزمایش ندارم»، و شرطِ مرگِ خودِ تخصیص.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent / "outcomes"), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import thesis_queue as tq  # noqa: E402

FAILURES: list[str] = []
CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(msg)


def _mk(rows, **extra):
    """دفترِ موقت روی دیسک + state_dir که thesis_queue می‌فهمد."""
    d = Path(tempfile.mkdtemp(prefix="thesisq-"))
    (d / "thesis").mkdir()
    (d / "thesis" / "thesis-ledger.json").write_text(
        json.dumps({"rows": rows, **extra}, ensure_ascii=False), "utf-8")
    return d


ROW_OK = dict(id="ok-row", family="t", claim="ساختارِ X بهتر از Y عمل می‌کند",
              proof="مقایسهٔ جفت‌شده با n>=48", status="UNTESTED",
              kill="اگر تفاوتِ معنادار نساخت، رد است.")


# ── T1 · قاعدهٔ ۱: ردیفِ بی‌شرطِ مرگ هرگز وارد صف نمی‌شود ─────────────────
def t1_kill_required():
    for bad_kill in ("", "   ", "—", "-", "— —"):
        r = dict(ROW_OK, id="nokill", kill=bad_kill)
        c = tq.classify(r)
        ck(not c["eligible"], f"T1: ردیفِ kill={bad_kill!r} واجدِ شرط شد")
        ck("no-kill-condition" in c["reason"], f"T1: دلیلِ رد برای kill={bad_kill!r} غلط")
    # و با شرطِ مرگِ واقعی، دلیلِ رد دیگر «بی‌شرطِ مرگ» نیست
    c = tq.classify(ROW_OK)
    ck("no-kill-condition" not in c["reason"], "T1: ردیفِ دارای kill هم رد شد")


# ── T2 · صداقتِ «آزمایش ندارم»: پنهان نمی‌شود ────────────────────────────
def t2_honest_about_missing_experiment():
    d = _mk([ROW_OK])
    s = tq.select(state_dir=d)
    ck(s["runnable_total"] == 0, "T2: ردیفِ بی‌آزمایش اجراپذیر اعلام شد")
    ck(len(s["needs_design"]) == 1, "T2: ردیفِ بی‌آزمایش در needs_design نیامد")
    ck(s["needs_design"][0]["id"] == "ok-row", "T2: idِ needs_design غلط")
    # صفِ خالیِ دروغین ممنوع: ردیف نه اجراپذیر است نه ناپدید
    ck(s["ledger_rows"] == 1, "T2: ردیف از شمارش افتاد")
    # با ثبتِ آزمایش، اجراپذیر می‌شود
    tq.EXPERIMENT_REGISTRY["ok-row"] = "probe_x"
    try:
        s2 = tq.select(state_dir=d)
        ck(s2["runnable_total"] == 1, "T2: با آزمایشِ ثبت‌شده هم اجراپذیر نشد")
        ck(s2["runnable"][0]["experiment"] == "probe_x", "T2: کلیدِ آزمایش منتقل نشد")
    finally:
        tq.EXPERIMENT_REGISTRY.pop("ok-row", None)


# ── T3 · گاردِ پدیدارشناختی: ادعای آگاهی وارد صف نمی‌شود ─────────────────
def t3_phenomenal_blocked():
    for claim in ("سیستم به آگاهی می‌رسد", "this proves consciousness emerges",
                  "qualia are present", "خودآگاهیِ واقعی دارد"):
        r = dict(ROW_OK, id="phen", claim=claim)
        c = tq.classify(r)
        ck(not c["eligible"], f"T3: ادعای پدیدارشناختی واجد شد: {claim[:28]}")
        ck("phenomenal-claim" in c["reason"], f"T3: دلیلِ رد غلط برای {claim[:28]}")
    # fail-closed: نبودِ بلوکِ _dream_track گارد را خاموش نمی‌کند
    d = _mk([dict(ROW_OK, id="phen", claim="consciousness discovered")])
    s = tq.select(state_dir=d)
    ck(s["runnable_total"] == 0, "T3: بی‌بلوکِ اعلام، گاردِ پدیدارشناختی fail-open شد")


# ── T4 · قاعدهٔ ۲: وضعیت فقط با شاهدِ واقعی عوض می‌شود ────────────────────
def t4_only_evidence_moves_status():
    good = {"verdict": "rejected", "experiment_key": "k|0|abc", "contract_id": "thesis-ok-row"}
    bad_cases = [
        (None, "no-evidence"),
        ({}, "non-terminal-verdict"),
        ({"verdict": "accepted"}, "no-experiment-key"),                  # حکم بی‌ردِ اجرا
        ({"verdict": "in_progress", "experiment_key": "k"}, "non-terminal-verdict"),
        ({"verdict": "", "experiment_key": "k"}, "non-terminal-verdict"),
        ("accepted", "no-evidence"),                                     # رشته، نه ردیف
    ]
    for ev, want in bad_cases:
        d = _mk([ROW_OK])
        r = tq.record_evidence(row_id="ok-row", new_status="FALSIFIED",
                               ledger_entry=ev, state_dir=d)
        ck(not r["ok"], f"T4: شاهدِ نامعتبر پذیرفته شد: {ev!r}")
        ck(want in r["reason"], f"T4: دلیلِ رد غلط برای {ev!r} → {r['reason']}")
        # و وضعیت روی دیسک دست‌نخورده مانده
        on_disk = json.loads((d / "thesis" / "thesis-ledger.json").read_text("utf-8"))
        ck(on_disk["rows"][0]["status"] == "UNTESTED",
           f"T4: وضعیت با شاهدِ نامعتبر عوض شد: {ev!r}")

    # شاهدِ معتبر → عوض می‌شود
    d = _mk([ROW_OK])
    r = tq.record_evidence(row_id="ok-row", new_status="FALSIFIED",
                           ledger_entry=good, state_dir=d)
    ck(r["ok"], f"T4: شاهدِ معتبر رد شد: {r.get('reason')}")
    on_disk = json.loads((d / "thesis" / "thesis-ledger.json").read_text("utf-8"))
    ck(on_disk["rows"][0]["status"] == "FALSIFIED", "T4: وضعیت با شاهدِ معتبر عوض نشد")
    # ردیفِ ناموجود
    r2 = tq.record_evidence(row_id="ghost", new_status="SUPPORTED",
                            ledger_entry=good, state_dir=d)
    ck(not r2["ok"] and "unknown-row" in r2["reason"], "T4: ردیفِ ناموجود پذیرفته شد")


# ── T5 · قاعدهٔ ۳: ردیفِ ابطال‌شده حذف/بازنویسی نمی‌شود ───────────────────
def t5_falsified_never_deleted():
    d = _mk([ROW_OK])
    ev = lambda k: {"verdict": "rejected", "experiment_key": k, "contract_id": "c"}  # noqa: E731
    tq.record_evidence(row_id="ok-row", new_status="FALSIFIED",
                       ledger_entry=ev("k1"), state_dir=d)
    tq.record_evidence(row_id="ok-row", new_status="SUPPORTED",
                       ledger_entry=ev("k2"), state_dir=d)
    on_disk = json.loads((d / "thesis" / "thesis-ledger.json").read_text("utf-8"))
    rows = on_disk["rows"]
    ck(len(rows) == 1, "T5: ردیف تکثیر یا حذف شد")
    hist = rows[0].get("status_history") or []
    ck(len(hist) == 2, f"T5: تاریخِ وضعیت append نشد (len={len(hist)})")
    ck(hist[0]["from"] == "UNTESTED" and hist[0]["to"] == "FALSIFIED",
       "T5: حرکتِ اول در تاریخ ثبت نشد")
    ck(hist[1]["from"] == "FALSIFIED" and hist[1]["to"] == "SUPPORTED",
       "T5: ابطالِ قبلی از تاریخ پاک شد")
    ck(all(h.get("experiment_key") for h in hist), "T5: ردِ اجرا در تاریخ نیست")
    ck(all(isinstance(h.get("at"), (int, float)) for h in hist), "T5: زمانِ حرکت ثبت نشد")
    # ادعاِ اصلی و شرطِ مرگ دست‌نخورده
    ck(rows[0]["claim"] == ROW_OK["claim"], "T5: ادعا بازنویسی شد")
    ck(rows[0]["kill"] == ROW_OK["kill"], "T5: شرطِ مرگ بازنویسی شد")


# ── T6 · شرطِ مرگِ خودِ تخصیصِ ۲۵٪: بی‌داده ≠ رسیدنِ شرط ──────────────────
def t6_allocation_kill_condition():
    # بی‌هیچ حرکت: نباید بگوید شرطِ مرگ رسیده
    k = tq.kill_check({"rows": [ROW_OK]}, now=time.time())
    ck(k["verdict"] == "no-movement-recorded-yet",
       f"T6: بی‌داده حکمِ غلط داد: {k['verdict']}")
    ck(k["movements"] == 0, "T6: شمارِ حرکت غلط")
    now = 1_800_000_000.0
    # حرکتِ تازه → alive
    fresh = {"rows": [dict(ROW_OK, status_history=[{"at": now - 10 * 86400, "to": "X"}])]}
    ck(tq.kill_check(fresh, now=now)["verdict"] == "alive", "T6: حرکتِ ۱۰ روزه alive نشد")
    # سکونِ >۹۰ روز → شرطِ مرگ
    stale = {"rows": [dict(ROW_OK, status_history=[{"at": now - 91 * 86400, "to": "X"}])]}
    kk = tq.kill_check(stale, now=now)
    ck(kk["verdict"] == "kill-condition-met", f"T6: سکونِ ۹۱ روزه: {kk['verdict']}")
    ck(kk["idle_days"] > 90, "T6: idle_days غلط محاسبه شد")
    # مرزِ دقیق: ۹۰ روز و کمی کمتر هنوز زنده
    edge = {"rows": [dict(ROW_OK, status_history=[{"at": now - 89.9 * 86400, "to": "X"}])]}
    ck(tq.kill_check(edge, now=now)["verdict"] == "alive", "T6: مرزِ ۸۹.۹ روز مرده اعلام شد")
    # ابطال هم حرکت است: تاریخِ verdict=rejected باید پنجره را تازه کند
    rej = {"rows": [dict(ROW_OK, status_history=[
        {"at": now - 5 * 86400, "to": "FALSIFIED", "verdict": "rejected"}])]}
    ck(tq.kill_check(rej, now=now)["verdict"] == "alive",
       "T6: ابطال به‌عنوان حرکت شمرده نشد")


# ── T7 · fail-soft و flag: نبودِ دفتر crash نمی‌کند، فلگ default-off ─────
def t7_failsoft_and_flag():
    d = Path(tempfile.mkdtemp(prefix="thesisq-empty-"))
    s = tq.select(state_dir=d)
    ck(s["ledger_rows"] == 0, "T7: دفترِ غایب crash/شمارِ غلط داد")
    ck(s["ledger_missing"], "T7: غیبتِ دفتر گزارش نشد")
    ck(s["runnable_total"] == 0, "T7: از دفترِ غایب کار درآمد")
    # دفترِ خراب
    (d / "thesis").mkdir(exist_ok=True)
    (d / "thesis" / "thesis-ledger.json").write_text("{ not json", "utf-8")
    s2 = tq.select(state_dir=d)
    ck(s2["ledger_rows"] == 0 and s2["ledger_missing"], "T7: دفترِ خراب fail-soft نشد")
    # flag default-off
    import os
    ck(tq.FLAG == "OCTOPUS_WIRE_THESIS_QUEUE", "T7: نامِ فلگ عوض شد")
    old = os.environ.pop(tq.FLAG, None)
    try:
        ck(tq.enabled() is False, "T7: فلگ بدونِ env روشن است")
        os.environ[tq.FLAG] = "1"
        ck(tq.enabled() is True, "T7: فلگ با 1 روشن نشد")
    finally:
        os.environ.pop(tq.FLAG, None)
        if old is not None:
            os.environ[tq.FLAG] = old
    # summary هیچ‌وقت raise نمی‌کند
    sm = tq.summary(state_dir=d)
    ck(isinstance(sm, dict) and sm["flag"] == tq.FLAG, "T7: summary شکست")


# ── T8 · دفترِ واقعیِ زنده: ادعای مادر باید بیرونِ صف باشد ────────────────
def t8_live_ledger_shape():
    real = tq.load()           # دفترِ واقعیِ روی دیسک
    rows = real.get("rows") or []
    if not rows:
        return                 # در checkoutِ تازه دفتر نیست — تست را قرمز نمی‌کنیم
    ck(len(rows) >= 10, f"T8: دفترِ زنده کوچک شد ({len(rows)} ردیف)")
    ids = {r.get("id") for r in rows}
    ck("dream-consciousness-discovery" in ids, "T8: ادعای مادر از دفتر رفت")
    ck("c15-allelic-partition" in ids, "T8: ردیفِ C15 از دفتر رفت")
    # قاعدهٔ ۱ روی کلِ دفترِ زنده: هر ردیفِ واجدِ شرط، شرطِ مرگ دارد
    s = tq.select(limit=99)
    for c in s["runnable"]:
        row = next(r for r in rows if r.get("id") == c["id"])
        ck(tq._has_kill(row), f"T8: ردیفِ اجراپذیرِ {c['id']} شرطِ مرگ ندارد")
    # ادعای پدیدارشناختی در صورتِ اولیه، بیرونِ صف
    blocked_ids = {c["id"] for c in s["blocked"]}
    ck("dream-consciousness-discovery" in blocked_ids,
       "T8: ادعای مادر وارد صف شد — گاردِ پدیدارشناختی روی دفترِ واقعی کار نکرد")
    # ردیف‌های ابطال‌شده حاضرند (قاعدهٔ ۳ روی دفترِ واقعی)
    for keep in ("gf-bridge-original", "br-02-shared-structure"):
        ck(keep in ids, f"T8: نتیجهٔ منفیِ {keep} حذف شده")


def main() -> int:
    for fn in (t1_kill_required, t2_honest_about_missing_experiment, t3_phenomenal_blocked,
               t4_only_evidence_moves_status, t5_falsified_never_deleted,
               t6_allocation_kill_condition, t7_failsoft_and_flag, t8_live_ledger_shape):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            FAILURES.append(f"{fn.__name__}: EXCEPTION {type(e).__name__}: {e}")
    if FAILURES:
        print(f"FAIL {len(FAILURES)}/{CHECKS} — thesis_queue")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print(f"PASS {CHECKS}/{CHECKS} — thesis_queue (سه قاعدهٔ دفترِ تز ساختاراً قفل)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
