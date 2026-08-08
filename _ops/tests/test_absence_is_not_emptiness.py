#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_absence_is_not_emptiness — «نخواندم» هرگز نباید «هیچ نیست» شود.

    زمینه (اسکنِ ۲۰۲۶-۰۸-۰۵، سه بازدارنده): سه جای مستقل، نبودِ داده را به
    **اطمینانِ فعال** تبدیل می‌کردند — که از خطا بدتر است، چون خطا را
    می‌بینی ولی این را نه:

      ۱. `get_approvals_state` از جدولِ `deliveries` می‌خواند که در این
         پایگاه **وجود ندارد** (تنها جدول `outcomes` است). کوئری استثنا
         می‌داد، `except` می‌بلعید، و صفِ خالی برمی‌گشت. کاکپیت می‌نوشت
         «صف خالی است» و خانه تیک می‌زد «✓» — در حالی که **۶ پیشنهادِ
         واقعی** منتظرِ تصمیم بودند، قدیمی‌ترین از ۲۰۲۶-۰۷-۲۳.
      ۲. `get_miniapp_state` هنگامِ نخواندنِ ORGANISM-STATE
         `{"status":"unknown"}` می‌دهد، ولی خانه فقط `"error"` را می‌گرفت؛
         پس `halted` تعریف‌نشده ⇒ falsy ⇒ «ارگانیسم زنده است» با چشمِ درخشان.
      ۳. قرصِ تبِ سیستم `halted` را از یک متغیرِ سراسری می‌خواند که پیش‌فرضش
         false بود ⇒ «متوقف نیست» هر وقت خانه هنوز resolve نشده.

    ادعاهای زیرِ آزمون (هرکدام با جهشِ کُشنده روی لنگرِ یکتا):
      · صفِ تأیید از اسکیمای **واقعی** می‌خواند و ۶ موردِ زنده را می‌بیند.
      · اسکیمای ناخوانا ⇒ `pending=None` (نه `[]`) + وضعِ غیرِ ok.
      · UI هیچ‌جا `status != "ok"` را «خالی» رندر نمی‌کند.
      · چشم سه‌حالته است و `unknown` نه درخشش است نه توقف.

    سبکِ main-style: harness.setup اول، توابعِ t_*، harness.run، sys.exit.
"""
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("absence-is-not-emptiness")

import miniapp_state as ms  # noqa: E402

MINI = harness.REAL_VAULT / "_ops" / "telegram_center" / "miniapp"
JS_RAW = (MINI / "app.js").read_text(encoding="utf-8")
JS = re.sub(r"//[^\n]*", "", re.sub(r"/\*[\s\S]*?\*/", "", JS_RAW))
CSS = re.sub(r"/\*[\s\S]*?\*/", "",
             (MINI / "style.css").read_text(encoding="utf-8"))

#: اسکیمای واقعیِ outcomes.db — از خودِ پایگاهِ زنده خوانده شد.
_COLS = ("event_id, idempotency_key, correlation_id, mission_id, proposal_id, "
         "leg_id, lead_id, event_type, verdict, value_aud_claimed, occurred_at, "
         "recorded_at, schema_version, payload_json")


def _fake_outcomes(rows):
    """یک outcomes.db ِ موقت با اسکیمای واقعی و ردیف‌های دلخواه."""
    d = Path(tempfile.mkdtemp(prefix="outcomes-"))
    (d / "outcomes").mkdir()
    c = sqlite3.connect(str(d / "outcomes" / "outcomes.db"))
    c.execute(f"CREATE TABLE outcomes({_COLS.replace(', ', ' TEXT, ')} TEXT)")
    for r in rows:
        c.execute(
            "INSERT INTO outcomes(proposal_id,leg_id,event_type,verdict,"
            "value_aud_claimed,occurred_at) VALUES(?,?,?,?,?,?)", r)
    c.commit(); c.close()
    ms.STATE_DIR = d
    return d


def t_pending_comes_from_the_real_schema():
    """پیشنهادی که تحویل شده و حکم ندارد = منتظر."""
    _fake_outcomes([
        ("P-1", "lead", "delivered", None, 0.0, "2026-07-23T04:00:00Z"),
        ("P-2", "lead", "delivered", None, 0.0, "2026-08-03T14:00:00Z"),
        # این یکی حکم دارد ⇒ منتظر نیست
        ("P-3", "lead", "accepted-measurement", "measurement", 0.0, "2026-08-03T15:00:00Z"),
    ])
    d = ms.get_approvals_state()
    assert d["status"] == "ok", f"وضع ok نیست: {d!r}"
    assert d["count"] == 2, f"شمارِ منتظر غلط: {d['count']} (باید ۲)"
    ids = {p["proposal_id"] for p in d["pending"]}
    assert ids == {"P-1", "P-2"}, f"مجموعهٔ منتظرها غلط: {ids}"


def t_a_later_verdict_removes_it_from_the_queue():
    """قرینه: اگر بعداً تصمیم گرفته شود، دیگر منتظر نیست.

    بدونِ این، رفعی که «هر ردیفِ delivered را بشمار» هم پاس می‌شد.
    """
    _fake_outcomes([
        ("P-9", "lead", "delivered", None, 0.0, "2026-08-01T10:00:00Z"),
        ("P-9", "lead", "accepted-measurement", "measurement", 0.0, "2026-08-02T10:00:00Z"),
    ])
    d = ms.get_approvals_state()
    assert d["count"] == 0, f"پیشنهادِ تصمیم‌گرفته هنوز در صف است: {d!r}"


def t_unreadable_schema_yields_none_not_empty_list():
    """اسکیمای ناخوانا ⇒ `pending=None`. `[]` یعنی «هیچ کاری نیست» که دروغ است."""
    d = Path(tempfile.mkdtemp(prefix="outcomes-bad-"))
    (d / "outcomes").mkdir()
    c = sqlite3.connect(str(d / "outcomes" / "outcomes.db"))
    c.execute("CREATE TABLE something_else(x TEXT)")   # جدولِ outcomes وجود ندارد
    c.commit(); c.close()
    ms.STATE_DIR = d
    got = ms.get_approvals_state()
    assert got["status"] != "ok", f"اسکیمای خراب را ok گزارش کرد: {got!r}"
    assert got.get("pending") is None, (
        f"برای اسکیمای ناخوانا فهرستِ خالی داد: {got.get('pending')!r}")


def t_the_ui_never_renders_a_non_ok_queue_as_empty():
    """کارتِ تأیید باید قبل از هر رندری وضع را بسنجد."""
    i = JS.find('api("/api/approvals")')
    assert i >= 0, "صداکنندهٔ صفِ تأیید پیدا نشد"
    seg = JS[i:i + 700]
    assert 'd.status !== "ok"' in seg or "d.status!==\"ok\"" in seg, \
        "کارتِ تأیید وضع را نمی‌سنجد و هر چیزی را خالی می‌خواند"


def t_home_does_not_tick_a_green_check_from_an_unread_queue():
    """تیکِ «✓ صفِ تأیید خالی است» فقط با وضعِ ok مجاز است."""
    i = JS.find("صفِ تأیید خالی است")
    assert i >= 0, "خطِ تیکِ سبز پیدا نشد"
    seg = JS[max(0, i - 900):i]
    assert 'ap.status !== "ok"' in seg or 'ap.status!=="ok"' in seg, \
        "خانه بدونِ سنجشِ وضع تیکِ سبز می‌زند"


def t_home_stops_on_unknown_organism_state():
    """`unknown` جدا از `error` گرفته شود، وگرنه «زنده است» از هیچ ساخته می‌شود."""
    # ⚠️ لنگر باید **یکتا** باشد. نسخهٔ اولِ این تست روی
    # `st.status==="error"` می‌گشت و به وقوعِ اولش می‌خورد که مالِ renderPF
    # است نه خانه — پس دربارهٔ خانه هیچ نمی‌گفت. `window.__octoHalted`
    # فقط در خانه نوشته می‌شود.
    anchor = "window.__octoHalted = !!st.halted"
    i = JS.find(anchor)
    assert i >= 0, "لنگرِ خانه پیدا نشد"
    assert JS.count(anchor) == 1, f"لنگر یکتا نیست ({JS.count(anchor)})"
    seg = JS[max(0, i - 1400):i]
    assert 'st.status==="unknown"' in seg or 'st.status === "unknown"' in seg, \
        "خانه شاخهٔ unknown ندارد — نبودِ داده «ارگانیسم زنده است» می‌شود"
    assert "setHalted(null)" in seg, "خانه در حالتِ unknown چشم را نامعلوم نمی‌کند"


def t_the_eye_has_a_real_unknown_face():
    """چشم سه‌حالته است و «نمی‌دانم» رنگِ خودش را دارد."""
    m = re.search(r"function\s+setHalted\s*\([^)]*\)\s*\{([\s\S]{0,420}?)\n  \}", JS)
    assert m, "‏setHalted پیدا نشد"
    body = m.group(1)
    assert "unknown" in body, "‏setHalted حالتِ سوم ندارد"
    assert "null" in body or "undefined" in body, "‏setHalted نبودِ داده را تشخیص نمی‌دهد"
    # ⚠️ صرفِ وجودِ کلاس کافی نیست — جهشِ «یکی از چهار قاعده را بردار» زنده
    # ماند. ادعای باربر این است که چشمِ نامعلوم **نمی‌درخشد**: هالهٔ درخشان
    # همان چیزی است که مالک به‌عنوان «زنده» می‌خواند.
    halo = re.search(r"\.eye\.unknown\s+\.halo\s*\{([^}]*)\}", CSS)
    assert halo, "قاعدهٔ هالهٔ چشمِ نامعلوم در CSS نیست"
    assert re.search(r"opacity\s*:\s*0\b", halo.group(1)), \
        f"چشمِ نامعلوم هنوز هاله دارد ⇒ شبیهِ زنده دیده می‌شود: {halo.group(1)}"
    ring = re.search(r"\.eye\.unknown\s+\.ring\s*\{([^}]*)\}", CSS)
    assert ring, "قاعدهٔ حلقهٔ چشمِ نامعلوم در CSS نیست"
    assert "var(--cyan)" not in ring.group(1), \
        "حلقهٔ چشمِ نامعلوم هنوز فیروزه‌ایِ سلامت است"


def t_current_truth_is_found_not_guessed_by_date():
    """نامِ تاریخ‌دار در کد = بمبِ ساعتی.

    ⚠️ `_TRUTH` روی `OCTOPUS-CURRENT-TRUTH-2026-08-02.md` کوبیده بود و آن
    فایل جابه‌جا شده بود، پس تبِ حقیقت **مرده** بود و کسی نفهمید — چون
    «missing» شبیهِ حالتِ عادی دیده می‌شد نه شبیهِ خرابی.
    """
    src = (_OPS / "telegram_center" / "miniapp_state.py").read_text(encoding="utf-8")
    # کامنت و docstring را بردار — وگرنه assert به توضیحِ خودِ فایل می‌خورد
    code = re.sub(r"#[^\n]*", "", re.sub(r'"""[\s\S]*?"""', "", src))
    dated = re.findall(r"OCTOPUS-CURRENT-TRUTH-\d{4}-\d{2}-\d{2}", code)
    assert not dated, f"نامِ تاریخ‌دارِ هاردکد هنوز در کد است: {set(dated)}"
    assert "_find_truth" in code, "تابعِ یابنده وجود ندارد"
    got = ms.get_current_truth()
    assert got.get("status") in ("ok", "missing"), got
    if got.get("status") == "missing":
        assert got.get("looked_in"), "غیبت بدونِ گفتنِ اینکه کجا گشت"


def t_brain_keeps_scan_bookkeeping_when_a_tier_is_not_due():
    """حافظه‌ای که خودش را پاک کند از نداشتنِ حافظه بدتر است.

    ⚠️ باگ: وقتی نوبتِ یک اسکن نبود، فقط **مقادیرش** کپی می‌شد و کلیدهای
    `_scan_<key>`/`_scan_<key>_ts` نه. نتیجه: `/api/selfmap` آن اسکن را
    همیشه **خالی** نشان می‌داد در حالی که واقعاً دویده بود، و اسکن
    بی‌دلیل زودتر از فاصله‌اش دوباره می‌دوید.
    """
    import time as _t
    sys.path.insert(0, str(_OPS)) if str(_OPS) not in sys.path else None
    import cockpit_brain as cb
    now = _t.time()
    mem = {"_scan_dark": {"dark_gates": 128}, "_scan_dark_ts": now,
           "_scan_orphan": {"orphans": 60}, "_scan_orphan_ts": now,
           "_scan_self": {"dead_symbols": 217}, "_scan_self_ts": now,
           # T4 — تایرِ calibration باید همان قاعدهٔ دفترداری را داشته باشد.
           "_scan_calibration": {"calibration_verdict": "stable", "calibration_alert": False},
           "_scan_calibration_ts": now}
    out = cb.self_awareness(mem, now=now)
    assert out.get("_scans_ran") == [], f"اسکنی دوید که نوبتش نبود: {out.get('_scans_ran')}"
    for k in ("dark", "orphan", "self", "calibration"):
        assert f"_scan_{k}_ts" in out, f"مهرِ زمانِ {k} گم شد ⇒ selfmap خالی می‌شود"
        assert out.get(f"_scan_{k}") == mem[f"_scan_{k}"], f"مقادیرِ {k} گم شد"
    assert out.get("dark_gates") == 128 and out.get("orphans") == 60
    assert out.get("calibration_verdict") == "stable", "مقدارِ کش‌شدهٔ calibration گم شد"


def t_calibration_tier_is_registered_with_6h_cadence():
    """T4 — تایرِ calibration با فاصلهٔ ۶ساعته (۲۱۶۰۰ث) در `_TIERS` ثبت شده باشد."""
    import cockpit_brain as cb
    assert "calibration" in cb._TIERS, cb._TIERS
    _mod, every = cb._TIERS["calibration"]
    assert every == 21600.0, f"فاصلهٔ تایرِ calibration باید ۲۱۶۰۰.۰ ثانیه باشد: {every}"


def t_calibration_tier_is_fail_soft_when_absent():
    """calibration-latest.json نبود ⇒ همه چیز None، بدونِ کرش — نه اسکنِ «شکست‌خورده».

    ⚠️ نبودِ فایل با شکستِ اسکنر فرق دارد: `_run_scan` وقتی subprocess می‌ترکد
    تایر را `"{key}:failed"` علامت می‌زند، ولی `_read_calibration` هرگز None
    برنمی‌گرداند — همیشه دیکشنری با فیلدهای None. پس تایر باید در `_scans_ran`
    عادی («calibration») ظاهر شود، نه در فهرستِ شکست‌خورده‌ها. سه تایرِ دیگر
    عمداً «نه‌due» نگه داشته می‌شوند تا این تست subprocess ِ واقعی (۴۶ثانیه‌ای
    self_scan) را صدا نزند.
    """
    import time as _t
    import cockpit_brain as cb
    now = _t.time()
    if cb.CALIBRATION_LATEST.exists():
        cb.CALIBRATION_LATEST.unlink()
    mem = {"_scan_dark": {}, "_scan_dark_ts": now,
           "_scan_orphan": {}, "_scan_orphan_ts": now,
           "_scan_self": {}, "_scan_self_ts": now}
    out = cb.self_awareness(mem, now=now)
    assert out.get("_scans_ran") == ["calibration"], (
        f"فقط calibration باید بدود: {out.get('_scans_ran')}")
    assert out.get("calibration_alert") is None, out.get("calibration_alert")
    assert out.get("calibration_verdict") is None, out.get("calibration_verdict")
    assert out.get("calibration_brier") is None
    assert out.get("calibration_ungraded_ratio") is None


def t_calibration_worse_verdict_triggers_always_notify_like_halted():
    """verdict=«worse» باید مثلِ halted بدونِ آستانه در diff() ظاهر شود — T4.

    ⚠️ خودِ calibration-latest.json فیلدِ `verdict` ندارد (verify شد روی
    calibration_probe.py:probe) — پس اینجا با مقایسهٔ Brierِ تازه با Brierِ
    کش‌شده ساخته می‌شود؛ Brier بالاتر یعنی بدتر.
    """
    import cockpit_brain as cb
    assert "calibration_alert" in cb._ALWAYS, (
        "calibration_alert از _ALWAYS بیرون رفته — دیگر مثلِ halted فوری نیست")

    cb.CALIBRATION_LATEST.parent.mkdir(parents=True, exist_ok=True)
    cb.CALIBRATION_LATEST.write_text(json.dumps(
        {"brier": 0.30, "aurc": 0.4, "ungraded": 5, "n_claims": 55}), encoding="utf-8")
    s = cb._read_calibration({"calibration_brier": 0.20})
    assert s["calibration_verdict"] == "worse", s
    assert s["calibration_alert"] is True, s

    # سطحِ diff(): همان مکانیزمِ halted — بدونِ آستانه، فوری.
    changes = cb.diff({"halted": False, "calibration_alert": True},
                      {"halted": False, "calibration_alert": False})
    keys = {c["key"] for c in changes}
    assert "calibration_alert" in keys, f"calibration_alert مثلِ halted بایپس نشد: {changes}"


def t_calibration_not_worse_follows_normal_threshold_cadence():
    """verdictِ «stable»/«better» بایپسِ فوری نمی‌سازد — روی همان آستانهٔ عادیِ بقیهٔ تایرها می‌ماند."""
    import cockpit_brain as cb

    prev = {"calibration_brier": 0.30}
    cb.CALIBRATION_LATEST.parent.mkdir(parents=True, exist_ok=True)

    # نوسانِ ریز (زیرِ CALIBRATION_BRIER_EPS) ⇒ stable، بدونِ هشدار.
    cb.CALIBRATION_LATEST.write_text(json.dumps(
        {"brier": 0.305, "aurc": 0.3, "ungraded": 5, "n_claims": 55}), encoding="utf-8")
    s_stable = cb._read_calibration(prev)
    assert s_stable["calibration_verdict"] == "stable", s_stable
    assert s_stable["calibration_alert"] is False, s_stable

    changes = cb.diff({"calibration_alert": False, "calibration_brier": 0.305},
                      {"calibration_alert": False, "calibration_brier": 0.30})
    keys = {c["key"] for c in changes}
    assert "calibration_alert" not in keys, f"نوسانِ ریز نباید بایپس کند: {changes}"
    assert "calibration_brier" not in keys, f"نوسانِ زیرِ آستانه باید ساکت بماند: {changes}"

    # بهبودِ بزرگ ⇒ better، هنوز alert=False — فقط «بدترشدن» بایپس می‌کند.
    cb.CALIBRATION_LATEST.write_text(json.dumps(
        {"brier": 0.10, "aurc": 0.2, "ungraded": 5, "n_claims": 55}), encoding="utf-8")
    s_better = cb._read_calibration(prev)
    assert s_better["calibration_verdict"] == "better", s_better
    assert s_better["calibration_alert"] is False, s_better

    # ولی جابه‌جاییِ بزرگِ Brier باید از مسیرِ عادیِ آستانه دیده شود، نه _ALWAYS.
    changes2 = cb.diff({"calibration_alert": False, "calibration_brier": 0.10},
                       {"calibration_alert": False, "calibration_brier": 0.30})
    keys2 = {c["key"] for c in changes2}
    assert "calibration_brier" in keys2, "تغییرِ بزرگِ Brier حتی در بهبود هم باید دیده شود"
    assert "calibration_alert" not in keys2, "بهبود نباید بایپسِ فوری بسازد"


def t_calibration_trend_reads_history_log():
    """۲۰۲۶-۰۸-۰۸: calibration-log.jsonl تا حالا صفر خوانندهٔ تولیدی داشت.
    این تست قفل می‌کند که _calibration_trend_brier تاریخچه را می‌خواند و
    verdictِ روند می‌سازد. fail-soft: نبودِ فایل/داده ⇒ 'insufficient'."""
    import cockpit_brain as cb
    import tempfile, json as _json
    orig = cb.CALIBRATION_LOG
    try:
        with tempfile.TemporaryDirectory() as td:
            logp = Path(td) / "calibration-log.jsonl"
            with logp.open("w", encoding="utf-8") as fh:
                for b in (0.28, 0.27, 0.26, 0.25):
                    fh.write(_json.dumps({"brier": b}) + "\n")
            cb.CALIBRATION_LOG = logp
            t = cb._calibration_trend_brier(n=4)
            assert t["samples"] == 4, t
            assert t["verdict"] == "improving", t   # 0.28→0.25 Brier کاهش = بهتر
            assert t["first_brier"] == 0.28 and t["last_brier"] == 0.25, t
    finally:
        cb.CALIBRATION_LOG = orig


def t_calibration_trend_detects_worsening_and_alerts():
    """روندِ worsening باید در _read_calibration هم alert بسازد، نه فقط
    مقایسهٔ دو-نقطه‌ای. این قفل می‌کند که trend واقعاً در alert فولد می‌شود."""
    import cockpit_brain as cb
    import tempfile, json as _json
    orig_log = cb.CALIBRATION_LOG
    orig_latest = cb.CALIBRATION_LATEST
    try:
        with tempfile.TemporaryDirectory() as td:
            logp = Path(td) / "calibration-log.jsonl"
            with logp.open("w", encoding="utf-8") as fh:
                for b in (0.20, 0.25, 0.30, 0.35):
                    fh.write(_json.dumps({"brier": b}) + "\n")
            cb.CALIBRATION_LOG = logp
            latestp = Path(td) / "calibration-latest.json"
            latestp.write_text(_json.dumps({"brier": 0.35}), encoding="utf-8")
            cb.CALIBRATION_LATEST = latestp
            r = cb._read_calibration({})
            assert r["calibration_trend"]["verdict"] == "worsening", r
            assert r["calibration_alert"] is True, "روندِ worsening باید alert بسازد"
    finally:
        cb.CALIBRATION_LOG = orig_log
        cb.CALIBRATION_LATEST = orig_latest


def t_calibration_trend_is_insufficient_when_log_absent():
    """fail-soft: نبودِ فایل ⇒ verdict='insufficient'، صفر کرش."""
    import cockpit_brain as cb
    orig = cb.CALIBRATION_LOG
    try:
        cb.CALIBRATION_LOG = Path("/nonexistent-trend-test/calibration-log.jsonl")
        t = cb._calibration_trend_brier()
        assert t["verdict"] == "insufficient", t
    finally:
        cb.CALIBRATION_LOG = orig


def t_vault_proposals_card_shows_pending_count_and_is_discovered():
    """۲۰۲۶-۰۸-۰۸: vault-proposals.jsonl (۶ رکوردِ GATE) تا حالا صفر خواننده داشت.
    این تست قفل می‌کند که کارتِ نو صف را می‌خواند، شمارش را نشان می‌دهد، و توسطِ
    capability_registry کشف می‌شود (بدونِ لمسِ center.py)."""
    import cockpit_brain  # noqa: F401 — only to ensure _OPS on path
    sys.path.insert(0, str(_OPS)) if str(_OPS) not in sys.path else None
    sys.path.insert(0, str(_OPS / "doctor"))
    import vault_proposals_card as vpc
    body = vpc.card()
    assert isinstance(body, str) and body, "کارت خالی برگشت"
    # یا «صفِ خالی» می‌گوید یا شمارش نشان می‌دهد — ولی باید شکلِ صحیح داشته باشد
    assert "نکنی:" in body, "خطِ پایانیِ استاندارد گم شد"
    # کشف توسطِ registry
    import capability_registry as cr
    keys = [r["key"] for r in cr.discover(refresh=True)]
    assert "vault_proposals_card" in keys, "کارت کشف نشد"


def t_vault_proposals_card_is_fail_soft_when_log_absent():
    """نبودِ فایل ⇒ کارتِ «صفِ خالی»، نه کرش."""
    import tempfile
    sys.path.insert(0, str(_OPS / "doctor"))
    import vault_proposals_card as vpc
    orig = vpc.PROPOSALS_LOG
    try:
        with tempfile.TemporaryDirectory() as td:
            vpc.PROPOSALS_LOG = Path(td) / "nonexist.jsonl"
            body = vpc.card()
            assert "خالی" in body, body
            assert "نکنی:" in body, body
    finally:
        vpc.PROPOSALS_LOG = orig


if __name__ == "__main__":
    CHECKS = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_absence_is_not_emptiness: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
