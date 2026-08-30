#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ops_action_crash_recovery — اقدامی که می‌ترکد نباید «انجام شد» بگوید.

    زمینه (اسکنِ ۲۰۲۶-۰۸-۰۵، بازدارندهٔ ۲ و ۳): `OpsActionEngine.execute`
    ردیفِ idempotency را با `begin` باز می‌کرد و فقط **بعد از** اجرای موفق
    `settle` می‌زد. هیچ try/finally ای در میان نبود.

    نتیجهٔ اندازه‌گیری‌شده روی یک پایگاهِ موقت: یک `output_score` ِ متنی
    باعثِ ValueError می‌شد، ردیف تا ابد RUNNING/NULL می‌ماند، و **هر تلاشِ
    بعدی** `{"ok": true, "status": "DUPLICATE"}` می‌گرفت — با صفر ردیفِ داده
    و صفر خطِ ممیزی. یعنی مالک می‌دید «قبلاً همین ثبت شده بود» برای کاری که
    هرگز انجام نشده بود. و چون کلیدِ مینی‌اپ قطعی است، از UI بازیابی‌ناپذیر.

    ادعاهای زیرِ آزمون:
      · ترکیدنِ وسطِ اجرا ⇒ وضعِ ERROR و ok=False، نه DUPLICATE.
      · ترکیدن **ثبت** می‌شود: هم ردیفِ idempotency settle می‌شود هم ممیزی.
      · تلاشِ دوم با همان کلید واقعاً **دوباره اجرا** می‌شود (نه DUPLICATE).
      · تکرارِ یک اقدامِ **رد‌شده** نباید ok=True بدهد — پول‌شوییِ شکست.
      · تکرارِ یک اقدامِ موفق همچنان DUPLICATE می‌دهد (رگرسیونِ معکوس).

    سبکِ main-style: harness.setup اول، توابعِ t_*، harness.run، sys.exit.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("ops-action-crash-recovery")


def _engine():
    """موتور روی یک انبارِ کاملاً موقت — هرگز پایگاهِ زندهٔ ops لمس نمی‌شود."""
    rt = tempfile.mkdtemp(prefix="crash-rec-")
    for k, v in (("OCTOPUS_OPS_RUNTIME_DIR", rt),
                 ("OCTOPUS_OPS_DB_PATH", str(Path(rt) / "o.sqlite3")),
                 ("OCTOPUS_OPS_AUDIT_PATH", str(Path(rt) / "a.jsonl")),
                 ("OCTOPUS_OPS_IDEMPOTENCY_PATH", str(Path(rt) / "i.sqlite3"))):
        os.environ[k] = v
    from agi2027_control.ops_actions import OpsActionEngine
    return OpsActionEngine(), Path(rt)


OWNER = {"is_owner": True}
#: ورودی‌ای که واقعاً موتور را می‌ترکاند: `float("۱۲۰ تومان")` ⇒ ValueError.
#: عمداً یک مقدارِ **واقع‌نما** است — همان چیزی که مالک ممکن است تایپ کند.
BAD = {"leg": "lead", "event": "زنگ به مشتری", "output_score": "۱۲۰ تومان"}


def t_a_crash_is_reported_as_error_not_success():
    eng, _ = _engine()
    r = eng.execute("value.record_event", BAD, OWNER, action_id="k1")
    eng.close()
    assert r.get("status") == "ERROR", f"ترکیدن به‌عنوان {r.get('status')!r} گزارش شد"
    assert r.get("ok") is False, f"ترکیدن ok={r.get('ok')!r} داد"
    assert r.get("reason"), "شکست بدونِ دلیل ثبت شد"


def t_a_crash_is_recorded_in_the_audit_log():
    """شکستی که ثبت نشود، دو سکوتِ متفاوت را یکی می‌کند."""
    eng, rt = _engine()
    eng.execute("value.record_event", BAD, OWNER, action_id="k2")
    eng.close()
    audit = rt / "a.jsonl"
    assert audit.exists(), "هیچ فایلِ ممیزی‌ای ساخته نشد"
    rows = [json.loads(l) for l in audit.read_text(encoding="utf-8").splitlines() if l.strip()]
    errs = [r for r in rows if r.get("status") == "ERROR"]
    assert errs, f"ترکیدن در ممیزی نیامد ({len(rows)} خط)"


def t_a_transient_failure_does_not_poison_the_key():
    """ادعای اصلی: کلیدِ مسموم دیگر وجود ندارد.

    شکستِ **گذرا** را می‌سنجم (قفلِ sqlite روی دیسکِ مکانیکیِ این دستگاه —
    یک ریسکِ واقعی، نه فرضی): تلاشِ اول با همان ورودی می‌ترکد، تلاشِ دوم با
    **همان کلید و همان ورودی** باید واقعاً اجرا شود.

    ⚠️ عمداً ورودی را بینِ دو تلاش عوض نمی‌کنم: ورودیِ متفاوت hash ِ متفاوت
    دارد و CONFLICT می‌گیرد، که رفتارِ **درست** است. اگر آن را می‌سنجیدم،
    تست دربارهٔ مسمومیتِ کلید هیچ نمی‌گفت.
    """
    eng, _ = _engine()
    good = dict(BAD, output_score=3)
    real = eng.db.record_value
    calls = {"n": 0}

    def flaky(p):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("database is locked")
        return real(p)

    eng.db.record_value = flaky
    first = eng.execute("value.record_event", good, OWNER, action_id="k3")
    assert first["status"] == "ERROR", first
    second = eng.execute("value.record_event", good, OWNER, action_id="k3")
    total = eng.summary().get("value_events_total")
    eng.close()
    assert second.get("status") != "DUPLICATE", (
        "تلاشِ دوم DUPLICATE ِ دروغین گرفت — کلید هنوز مسموم است")
    assert second.get("ok") is True, f"تلاشِ دوم موفق نشد: {second!r}"
    assert total == 1, f"رویداد واقعاً نوشته نشد (total={total!r})"


def t_a_different_payload_on_the_same_key_is_still_a_conflict():
    """قرینه: رفعِ مسمومیت نباید گاردِ CONFLICT را باز کند."""
    eng, _ = _engine()
    eng.execute("value.record_event", BAD, OWNER, action_id="k6")   # می‌ترکد
    other = eng.execute("value.record_event", dict(BAD, output_score=9),
                        OWNER, action_id="k6")
    eng.close()
    assert other["status"] == "CONFLICT", (
        f"ورودیِ متفاوت روی همان کلید CONFLICT نداد: {other!r}")


def t_a_repeated_rejection_is_not_laundered_into_success():
    """‏DUPLICATE ِ یک اقدامِ **ردشده** نباید ok=True بدهد.

    قبلاً `ok` کوبیده بود، پس تکرارِ یک BLOCKED به موفقیت تبدیل می‌شد و UI
    رویش اقدام می‌کرد.
    """
    eng, _ = _engine()
    p = {"title": "زنگ", "kind": "kind_که_وجود_ندارد"}
    first = eng.execute("task.create", p, OWNER, action_id="k4")
    assert first["status"] == "BLOCKED", first
    second = eng.execute("task.create", p, OWNER, action_id="k4")
    eng.close()
    assert second["status"] == "DUPLICATE", second
    assert second.get("ok") is False, (
        f"شکستِ ثبت‌شده به موفقیت پول‌شویی شد: ok={second.get('ok')!r}")


def t_a_repeated_success_is_still_a_duplicate():
    """قرینه — وگرنه رفعی که همیشه دوباره اجرا کند هم پاس می‌شد."""
    eng, _ = _engine()
    p = {"title": "فاکتور زیمان", "kind": "check_payment"}
    first = eng.execute("task.create", p, OWNER, action_id="k5")
    assert first.get("ok") is True, first
    second = eng.execute("task.create", p, OWNER, action_id="k5")
    total = eng.summary().get("tasks_total")
    eng.close()
    assert second["status"] == "DUPLICATE", second
    assert second.get("ok") is True, second
    assert total == 1, f"تکرار یک ردیفِ دوم ساخت (total={total!r})"


if __name__ == "__main__":
    CHECKS = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_ops_action_crash_recovery: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
