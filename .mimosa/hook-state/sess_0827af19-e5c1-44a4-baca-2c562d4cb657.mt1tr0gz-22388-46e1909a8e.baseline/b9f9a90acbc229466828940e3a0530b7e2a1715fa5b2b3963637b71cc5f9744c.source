#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_inbound_log_and_hang_detection.py — «پیامم رسید؟» باید جواب داشته باشد.

دو شکافِ ساختاریِ ۲۰۲۶-۰۸-۰۴، هر دو از شکایتِ «انگار هرکاری می‌کنم دیده
نمی‌شود»:

**۱) هیچ لاگِ ورودی در کلِ سیستم نبود.** `tg-send-log.jsonl` فقط خروجی است.
هیچ‌کجا نمی‌نوشت «آپدیتِ N رسید». پس سؤال بعد از وقوع جواب‌ناپذیر بود.

**۲) واچ‌داگ زنده‌بودن را از **وجود** استنتاج می‌کرد.** گامِ ۲ ِ
`tg-center-watchdog.ps1` این بود:

    if ($center) { exit 0 }          # پروسه هست ⇒ سالم

نبض **فقط وقتی** خوانده می‌شد که پروسه رفته باشد. پس یک مرکزِ
زنده‌ولی‌هنگ‌کرده هر ۵ دقیقه «سالم» شمرده می‌شد.

شاهدِ اندازه‌گیری‌شدهٔ ۰۸-۰۴ (اثبات با حذف + لاگِ ارسال):
    ۰۵:۰۰–۰۷:۱۸  ۱۴۴ ارسال
    ۰۷:۱۸–۰۹:۵۲    **۰** ارسال   ← زنده، و هیچ کاری نمی‌کرد
    ۰۹:۵۲–۱۱:۰۰   ۳۱ ارسال
واچ‌داگ در آن ۲س۳۴د ~۳۰ بار دوید (`result=0`) و **یک خط هم لاگ نکرد**.

⚠️ و طنزِ تلخش: خودِ همین اسکریپت این درس را برای **حلقه** یاد گرفته بود
(«یک حلقهٔ زنده که respawn نمی‌کند دقیقاً شبیهِ مرکزِ سالم است») و هرگز به
**خودِ مرکز** اعمالش نکرد. درسِ خواهر که به اصل نرسید.
"""
import ast
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("inbound-hang")
CENTER = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"
WD = harness.REAL_VAULT / "_ops" / "tg-center-watchdog.ps1"
SRC = CENTER.read_text("utf-8", errors="replace")
WSRC = WD.read_text("utf-8", errors="replace")


def _fn(name):
    for n in ast.walk(ast.parse(SRC)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _center():
    import importlib.util
    spec = importlib.util.spec_from_file_location("cp_probe", CENTER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    c = m.Center.__new__(m.Center)

    class _C:
        owner_chat_id = 555
    c._client = _C()
    return m, c


def t_a_anchors_exist():
    assert _fn("_log_inbound") is not None, "_log_inbound تعریف نشده"
    assert _fn("run_once") is not None
    assert WD.exists(), WD


def t_b_every_update_is_logged_before_dispatch():
    """ترتیب باربر است: اگر پردازش بترکد، ردیفِ «رسید» باید از قبل نشسته باشد
    تا کنارِ نامهٔ مرده تصویرِ کامل بدهد."""
    ro = ast.get_source_segment(SRC, _fn("run_once")) or ""
    assert "_log_inbound" in ro, "run_once ورودی را ثبت نمی‌کند"
    i_log = ro.find("self._log_inbound")
    i_disp = ro.find("self.handle_update")
    assert i_log >= 0 and i_disp > i_log, (
        "‏_log_inbound باید **قبل** از handle_update بیاید، وگرنه پیامی که "
        "پردازشش می‌ترکد هیچ ردیفِ «رسید» نمی‌گذارد")


def t_c_the_log_records_shape_and_answers_did_it_arrive():
    m, c = _center()
    p = Path(m.opslib.STATE_DIR) / "telegram" / "inbound-log.jsonl"
    assert str(harness.REAL_VAULT).lower() not in str(p).lower(), (
        "مقصد داخلِ درختِ زنده افتاد", str(p))
    for u in ({"update_id": 1, "message": {"text": "hi", "chat": {"type": "private"},
                                           "from": {"id": 555}}},
              {"update_id": 2, "message": {"text": "/stop x", "chat": {"type": "group"},
                                           "from": {"id": 999}}},
              {"update_id": 3, "message": {"voice": {}, "chat": {"type": "private"},
                                           "from": {"id": 555}}},
              {"update_id": 4, "callback_query": {"data": "a:b", "from": {"id": 555},
                                                  "message": {"chat": {"type": "private"}}}}):
        c._log_inbound(u)
    rows = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]
    assert len(rows) == 4, rows
    assert [r["update_id"] for r in rows] == [1, 2, 3, 4]
    assert [r["kind"] for r in rows] == ["text", "text", "voice", "callback_query"]
    assert rows[1]["cmd"] == "/stop" and rows[1]["is_command"]
    assert rows[0]["from_owner"] is True and rows[1]["from_owner"] is False
    assert rows[1]["chat_kind"] == "group"


def t_d_the_log_never_stores_the_message_text():
    """§۱۰. هدف «آیا رسید؟» است نه بایگانیِ مکالمه — ذخیرهٔ همهٔ متن‌ها یک
    نشتیِ PII ِ دائمی می‌ساخت که هیچ‌کس نخواسته بود. متنِ پیامی که **شکست
    خورد** جای دیگری است: نامهٔ مرده."""
    m, c = _center()
    p = Path(m.opslib.STATE_DIR) / "telegram" / "inbound-log.jsonl"
    secret = "PRIVATE-CONTENT-MUST-NOT-APPEAR"
    c._log_inbound({"update_id": 9, "message": {"text": secret,
                                                "chat": {"type": "private"},
                                                "from": {"id": 555}}})
    body = p.read_text("utf-8")
    assert secret not in body, "متنِ پیام در لاگِ ورودی نشت کرد"
    assert '"chars": 31' in body or '"chars":31' in body, (
        "طول ثبت نشد — بدونِ آن «رسید ولی خالی بود؟» جواب ندارد")


def t_e_the_inbound_log_is_silent():
    """قرینه: مالک از شلوغی هم شکایت داشت. یک ردیفِ روزمره **خبر** نیست."""
    seg = ast.get_source_segment(SRC, _fn("_log_inbound")) or ""
    assert "alert" not in seg, "لاگِ ورودی نباید هرگز هشدار بدهد"


def t_f_the_log_is_bounded():
    """لاگِ بی‌سقف روی یک دیسکِ مکانیکیِ ۵۴۰۰ دور خودش یک باگ است."""
    seg = ast.get_source_segment(SRC, _fn("_log_inbound")) or ""
    assert "_INBOUND_KEEP" in seg, "چرخشِ لاگ وجود ندارد"
    assert "st_size" in seg, "سقفِ اندازه سنجیده نمی‌شود"


def t_g_the_watchdog_no_longer_infers_health_from_existence():
    """قلبِ رفعِ دوم. `if ($center) { exit 0 }` ِ بی‌قید نباید برگردد."""
    # ⚠️ نسخهٔ اول خطِ **کامل** را مقایسه می‌کرد و جهشِ متناظر نیمه‌زنده ماند،
    # چون کامنتِ انتهایی روی خط باقی مانده بود. کامنت اول بریده می‌شود.
    live = []
    for ln in WSRC.splitlines():
        s = ln.split("#", 1)[0].strip()
        if s:
            live.append(s)
    bad = [ln for ln in live if ln.replace(" ", "") == "if($center){exit0}"]
    assert not bad, (
        "واچ‌داگ دوباره زنده‌بودن را از **وجود** استنتاج می‌کند — یک مرکزِ "
        "هنگ‌کرده باز هم ۲.۵ ساعت نامرئی می‌شود", bad)
    assert "$HUNG_AFTER_S" in WSRC, "آستانهٔ هنگ تعریف نشده"
    assert "centre HUNG" in WSRC, "شاخهٔ هنگ لاگ نمی‌کند"


def t_h_the_healthy_case_is_still_a_silent_exit():
    """قرینه، و لازم: واچ‌داگی که مرکزِ **سالم** را بکشد بدتر از باگِ اصلی
    است. شرط باید هم وجود و هم نبضِ تازه را بخواهد."""
    assert "if ($center -and $silent -lt $HUNG_AFTER_S) { exit 0 }" in WSRC, (
        "خروجِ ساکتِ حالتِ سالم عوض شده — یا مرکزِ سالم کشته می‌شود یا "
        "هنگ دوباره نامرئی می‌شود")


def t_i_the_hang_threshold_leaves_real_headroom():
    """آستانه باید از طولانی‌ترین تکرارِ سالم به‌قدرِ کافی بزرگ‌تر باشد،
    وگرنه واچ‌داگ مرکزِ مشغول را می‌کشد (گاردِ گرگ‌گرگ با دندانِ کشنده)."""
    import re
    m = re.search(r"\$HUNG_AFTER_S\s*=\s*(\d+)", WSRC)
    assert m, "آستانه پیدا نشد"
    thr = int(m.group(1))
    poll = re.search(r"POLL_TIMEOUT_S\s*=\s*(\d+)", SRC)
    assert poll, "POLL_TIMEOUT_S پیدا نشد"
    assert thr >= 4 * int(poll.group(1)), (
        f"آستانهٔ {thr}s نسبت به long-poll ِ {poll.group(1)}s کم است")


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t(); passed += 1; print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__); print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_inbound_log_and_hang_detection: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
