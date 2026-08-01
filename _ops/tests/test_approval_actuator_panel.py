#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_approval_actuator_panel.py — «✅ زدی، هیچ اکشنی نشد» به چشمِ مالک می‌رسد.

بیماری (لِینِ آزادسازیِ اکچوایتور، ۲۰۲۶-۰۸-۰۱): ۴۳ تأییدِ ✅ در
`state/telegram/approvals/` نشسته بود و هیچ سطحِ مالکی شمارشش را نشان نمی‌داد.
`approval_actuator` کامل بود ولی `summary()`/`scan()` **صفر صداکننده** داشت و
`actuator_beat` پشتِ فلگی بود که در env ِ هیچ‌کدام از ۴ پروسه وجود نداشت — یعنی
حتی مسلح‌کردنِ فلگ هم فقط یک JSON ِ نادیده تولید می‌کرد.

این سوئیت مسیرِ **خواندن** را می‌سنجد (مسیرِ نوشتن/اکچوایشن دست‌نخورده و پشتِ
OCTOPUS_WIRE_ACTUATOR باقی است):
  (الف) شمارشِ درست در `owner_views.approved_no_action`.
  (ب)  دیدن ≠ اکشن: نه marker نوشته می‌شود، نه handler صدا زده می‌شود.
  (ج)  پنجرهٔ تازگی روی ts ِ **منطقه‌دار** هم کار می‌کند (باگِ tz که کهنه را تازه می‌شمرد).
  (د)  no/later اصلاً در این بند نمی‌آیند.
  (ه)  صداکنندهٔ واقعی: `menu_integration.dispatch("m:mytasks")` همان خط را رندر می‌کند
       (دسترسی‌پذیری، نه فقط وجودِ تابع).
  (و)  پاریتهٔ عقب‌رو: صداکنندهٔ دو-آرگومانیِ قدیمی بایت‌به‌بایت همان قبلی.

صفر شبکه · صفر تلگرام · صفر پول · همه‌چیز در sandbox ِ harness.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("actuator-panel")

# read-model ها env را سرِ import می‌خوانند → قبل از import پین شوند (هیچ مسیرِ زنده‌ای)
_TMP = Path(ENV["OPS_DIR"]) / "panel"
_OCT = _TMP / "octopus-state"
_OPS_STATE = _TMP / "ops-state"
for _d in (_OCT, _OPS_STATE):
    _d.mkdir(parents=True, exist_ok=True)
os.environ["OCTOPUS_STATE_ROOT"] = str(_OCT)
os.environ["OPS_STATE_ROOT"] = str(_OPS_STATE)
os.environ["OCTOPUS_VAULT_ROOT"] = str(_TMP)

# کدِ زیرِ تست = همین worktree (نه درختِ زنده)
_SELF_OPS = Path(__file__).resolve().parent.parent
for _p in (_SELF_OPS, _SELF_OPS / "cortex", _SELF_OPS / "telegram_center"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib                       # noqa: E402
import approval_actuator as act     # noqa: E402
import owner_views as ov            # noqa: E402
import menu_integration as m2       # noqa: E402

APPROVALS = opslib.STATE_DIR / "telegram" / "approvals"
MARKS = opslib.STATE_DIR / "cortex" / "actuation-marks.json"
LATEST = opslib.STATE_DIR / "cortex" / "actuation-latest.json"
_LINE = "✅ زده‌ای ولی هیچ اکشنی نشد"


def _reset():
    import shutil
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)
    for p in (MARKS, LATEST):
        if p.exists():
            p.unlink()
    act.HANDLERS.clear()


def _approval(did, verdict="ok", ts=None):
    APPROVALS.mkdir(parents=True, exist_ok=True)
    rec = {"id": did, "verdict": verdict, "ts": ts or opslib.now_iso(), "source": "tg-center"}
    (APPROVALS / f"{did}.json").write_text(json.dumps(rec, ensure_ascii=False), "utf-8")


def _tz(days_ago: float) -> str:
    """ts ِ **منطقه‌دار** (دقیقاً شکلی که مرکز برای رکوردهای M-* می‌نویسد: +1000)."""
    tz = timezone(timedelta(hours=10))
    return (datetime.now(tz) - timedelta(days=days_ago)).isoformat()


def t_a_panel_counts_the_unactuated():
    """۳ تأییدِ ✅ ِ بی‌handler → هم شمارش، هم خطِ فارسی در کارتِ ③."""
    _reset()
    for i in range(3):
        _approval(f"appr-{i}", "ok")
    d = ov.approved_no_action()
    assert d["n"] == 3, f"انتظار ۳، دیدیم {d}"
    assert sorted(d["ids"]) == ["appr-0", "appr-1", "appr-2"], d["ids"]
    txt = ov.render_backlog([], [], d)
    assert _LINE in txt, txt
    assert "(3)" in txt, txt
    assert "appr-1" in txt, txt


def t_b_seeing_is_not_actuating():
    """دیدن هیچ اثری ندارد: نه marker، نه latest، نه صدا زدنِ handler."""
    _reset()
    called = {"n": 0}
    act.register("lead-", lambda rec: called.__setitem__("n", called["n"] + 1))
    _approval("lead-001", "ok")     # handler دارد
    _approval("appr-x", "ok")       # handler ندارد
    d = ov.approved_no_action()
    ov.render_backlog([], [], d)
    m2.dispatch("m:mytasks")
    assert called["n"] == 0, "خواندنِ کارت هرگز نباید handler را صدا بزند"
    assert not MARKS.exists(), "کارت نباید actuation-marks.json بنویسد"
    assert not LATEST.exists(), "کارت نباید actuation-latest.json بنویسد"
    assert d["ids"] == ["appr-x"], d           # handler-دار در این بند نمی‌آید
    act.HANDLERS.clear()


def t_c_timezone_aware_ancient_is_excluded():
    """ts ِ منطقه‌دارِ کهنه (۳۰ روز) بیرون؛ منطقه‌دارِ تازه (۱ روز) داخل.

    گاردِ باگِ tz: کسرِ aware از naive استثنا می‌داد، استثنا بلعیده می‌شد و سن ۰
    برمی‌گشت → هر رکوردِ منطقه‌دار «تازه» شمرده می‌شد و پنجرهٔ RECENT_DAYS مرده بود."""
    _reset()
    _approval("tz-ancient", "ok", ts=_tz(30))
    assert ov.approved_no_action()["n"] == 0, "کهنهٔ منطقه‌دار نباید شمرده شود"
    _approval("tz-fresh", "ok", ts=_tz(1))
    d = ov.approved_no_action()
    assert d["ids"] == ["tz-fresh"], d
    # ناخوانا → fail-open (تازه) تا بی‌صدا گم نشود
    _approval("bad-ts", "ok", ts="نه-تاریخ")
    assert ov.approved_no_action()["n"] == 2, ov.approved_no_action()


def t_d_no_and_later_never_appear():
    """❌ و «بعداً» تصمیمِ بی‌اکشن نیستند — این بند فقط ✅ را می‌شمارد."""
    _reset()
    _approval("appr-no", "no")
    _approval("appr-later", "later")
    d = ov.approved_no_action()
    assert d["n"] == 0, d
    assert _LINE not in ov.render_backlog([], [], d)


def t_e_menu_dispatch_actually_shows_it():
    """صداکنندهٔ واقعیِ زنده: m:mytasks (کارتِ ③) — نه فقط تابعِ تنها."""
    _reset()
    _approval("appr-live", "ok")
    txt, kb = m2.dispatch("m:mytasks")
    assert _LINE in txt, f"کارتِ ③ خط را ندارد:\n{txt}"
    assert "appr-live" in txt, txt
    assert kb, "کارت باید دکمهٔ برگشت داشته باشد"


def t_f_backward_compatible_two_args():
    """پاریتهٔ عقب‌رو: صداکنندهٔ دو-آرگومانی دقیقاً رفتارِ قبل را می‌گیرد."""
    _reset()
    _approval("appr-hidden", "ok")
    assert ov.render_backlog([], []) == "③ کارهای من: چیزی منتظرِ تو نیست ✅"
    txt = ov.render_backlog([{"title": "کارِ الف", "risk": "low"}], [])
    assert _LINE not in txt and "کارِ الف" in txt, txt


def t_g_never_raises_when_module_is_missing():
    """اگر actuator قابلِ import نبود، کارت ساکت می‌شود نه crash."""
    _reset()
    real = ov._load_actuator
    try:
        ov._load_actuator = lambda: (_ for _ in ()).throw(ImportError("boom"))
        d = ov.approved_no_action()
        assert d == {"n": 0, "ids": []}, d
        assert ov.render_backlog([], [], d) == "③ کارهای من: چیزی منتظرِ تو نیست ✅"
    finally:
        ov._load_actuator = real


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_approval_actuator_panel: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
