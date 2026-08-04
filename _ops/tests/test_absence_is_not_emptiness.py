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


if __name__ == "__main__":
    CHECKS = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_absence_is_not_emptiness: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
