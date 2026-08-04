#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_living_card.py — «یک موضوع، یک پیام» باید واقعاً یک پیام بماند.

فاز ۱ (۲۰۲۶-۰۸-۰۴). این ماژول جایگزینِ الگوی «هر تولیدکننده پیامِ خودش را
می‌فرستد» است. سه چیز اگر بشکند، کلِ فاز بی‌معنی می‌شود:

۱. **خاموش یعنی واقعاً خاموش.** دکمهٔ برگشتِ فاز ۱ همین فلگ است. اگر با
   فلگِ خاموش حتی یک فراخوانِ شبکه برود، «برگشت» یک ادعای بی‌پشتوانه است.
۲. **بی‌تغییر یعنی صفر فراخوان.** وگرنه فقط شکلِ نویز عوض شده: به‌جای پیامِ
   نو، ویرایشِ بیهوده — و گروه همین حالا ~۱۵ ویرایش در ساعت شبانه‌روز دارد.
۳. **کارتِ پاک‌شده باید برگردد.** `TgClient.edit` فقط `bool` می‌دهد، پس
   «پاک شده» از «شبکه قطع» جدا نیست. اگر شکستِ ویرایش را ساکت رد کنیم،
   کارتی که مالک پاک کرده **هرگز** برنمی‌گردد — مرگِ خاموشِ دائمی.
"""
import ast
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402  ← اول، وگرنه ایزوله نیست

ENV = harness.setup("living-card")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops" / "telegram_center"))

import living_card as lc  # noqa: E402

SRC = (harness.REAL_VAULT / "_ops" / "telegram_center" / "living_card.py"
       ).read_text("utf-8", errors="replace")


class FakeClient:
    """کلاینتِ **بدبین‌شدنی** — می‌شود وادارش کرد ویرایش را شکست بدهد.

    ⚠️ درسِ ثبت‌شدهٔ همین سیزن: فیکی که همیشه موفق برمی‌گرداند، سکوت و شکست
    را پنهان می‌کند و پروب را به نتیجهٔ **معکوس** می‌رساند."""

    def __init__(self, *, edit_ok=True, send_ok=True):
        self.sends, self.edits = [], []
        self._edit_ok, self._send_ok = edit_ok, send_ok
        self._next = 100

    @property
    def calls(self):
        return len(self.sends) + len(self.edits)

    def send(self, text, *, keyboard=None, chat_id=None, topic_id=None,
             stream=None, pin=False):
        self.sends.append({"text": text, "keyboard": keyboard,
                           "chat_id": chat_id, "topic_id": topic_id,
                           "stream": stream})
        if not self._send_ok:
            return None
        self._next += 1
        return self._next

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.edits.append({"message_id": message_id, "text": text,
                           "keyboard": keyboard, "chat_id": chat_id})
        return bool(self._edit_ok)


def _fresh(monkey_on=True):
    """‏state ِ خالی + فلگِ روشن/خاموش. هر تست از صفر شروع می‌کند."""
    import os
    p = lc._state_path()
    assert str(harness.REAL_VAULT).lower() not in str(p).lower(), (
        "‼️ state ِ تست داخلِ درختِ زنده افتاد", str(p))
    try:
        if p.exists():
            p.unlink()
    except OSError:
        pass
    os.environ[lc.FLAG] = "1" if monkey_on else "0"
    return FakeClient()


# ── ۱. دکمهٔ برگشت ───────────────────────────────────────────────────────────
def t_a_disabled_means_zero_network_calls():
    """اگر خاموش حتی یک فراخوان بزند، «برگشت» یک ادعای بی‌پشتوانه است."""
    c = _fresh(monkey_on=False)
    r = lc.put(c, name="home", text="سلام", chat_id=7)
    assert r["action"] == "off", r
    assert c.calls == 0, ("با فلگِ خاموش فراخوان رفت", c.sends, c.edits)
    assert not lc._state_path().exists(), "با فلگِ خاموش state نوشته شد"


# ── ۲. هستهٔ «یک موضوع، یک پیام» ─────────────────────────────────────────────
def t_b_first_put_sends_then_second_edits_the_same_message():
    c = _fresh()
    r1 = lc.put(c, name="home", text="نسخهٔ ۱", chat_id=7)
    assert r1["action"] == "sent", r1
    r2 = lc.put(c, name="home", text="نسخهٔ ۲", chat_id=7)
    assert r2["action"] == "edited", r2
    assert r2["message_id"] == r1["message_id"], (
        "ویرایش روی پیامِ دیگری رفت ⇒ «یک موضوع، یک پیام» شکست", r1, r2)
    assert len(c.sends) == 1 and len(c.edits) == 1, (c.sends, c.edits)


def t_c_unchanged_content_costs_nothing():
    """قلبِ ضدِ نویز. گروه همین حالا ~۱۵ ویرایش در ساعت شبانه‌روز می‌خورد؛
    ویرایشی که چیزی را عوض نمی‌کند فقط سهمیه و لاگ می‌سوزاند."""
    c = _fresh()
    lc.put(c, name="home", text="ثابت", chat_id=7)
    before = c.calls
    for _ in range(5):
        r = lc.put(c, name="home", text="ثابت", chat_id=7)
        assert r["action"] == "unchanged", r
    assert c.calls == before, (
        "محتوای بی‌تغییر فراخوانِ شبکه زد", c.edits)


def t_d_a_keyboard_change_alone_still_counts_as_a_change():
    """کارتی که متنش یکی است ولی دکمه‌هایش عوض شده، از دیدِ مالک **عوض
    شده**. اگر فقط متن هش شود، آن تغییر بی‌صدا گم می‌شود."""
    c = _fresh()
    lc.put(c, name="home", text="ثابت", keyboard=[[{"text": "الف"}]], chat_id=7)
    r = lc.put(c, name="home", text="ثابت", keyboard=[[{"text": "ب"}]], chat_id=7)
    assert r["action"] == "edited", (
        "تغییرِ دکمه دیده نشد ⇒ دکمهٔ کهنه روی کارت می‌ماند", r)


# ── ۳. بازیابی ──────────────────────────────────────────────────────────────
def t_e_a_deleted_card_comes_back():
    """⚠️ حالتی که یک no-op ِ ساکت می‌ساخت: `edit` فقط bool می‌دهد، پس
    «پیام پاک شده» و «شبکه قطع» یک شکل دارند. رد کردنِ ساکتِ شکست یعنی
    کارتی که مالک پاک کرده هرگز برنمی‌گردد."""
    c = _fresh()
    first = lc.put(c, name="home", text="نسخهٔ ۱", chat_id=7)["message_id"]
    c._edit_ok = False                          # مالک کارت را پاک کرد
    r = lc.put(c, name="home", text="نسخهٔ ۲", chat_id=7)
    assert r["action"] == "resent", (
        "کارتِ پاک‌شده برنگشت ⇒ مرگِ خاموشِ دائمی", r)
    assert r["message_id"] != first, r
    # و از این پس همان پیامِ نو ویرایش می‌شود، نه پیامِ مرده
    c._edit_ok = True
    r2 = lc.put(c, name="home", text="نسخهٔ ۳", chat_id=7)
    assert r2["action"] == "edited" and r2["message_id"] == r["message_id"], r2
    assert c.edits[-1]["message_id"] == r["message_id"], (
        "ویرایش هنوز به پیامِ مرده می‌رود", c.edits[-1])


def t_f_a_total_failure_is_reported_not_swallowed():
    c = _fresh()
    c._send_ok = False
    r = lc.put(c, name="home", text="متن", chat_id=7)
    assert r["action"] == "failed", r
    assert r["message_id"] is None, r


def t_g_empty_text_never_reaches_telegram():
    """`send` روی متنِ خالی **قبل از نوشتنِ رسید** برمی‌گردد، پس یک ارسالِ
    خالی هیچ ردی نمی‌گذارد — همان no-op ِ نامرئی که فاز ۰ ریشه‌کن کرد."""
    c = _fresh()
    for bad in ("", "   ", None):
        r = lc.put(c, name="home", text=bad, chat_id=7)
        assert r["action"] == "failed", (bad, r)
    assert c.calls == 0, ("متنِ خالی به تلگرام رفت", c.sends)


# ── ۴. حالت ─────────────────────────────────────────────────────────────────
def t_h_the_state_never_stores_the_message_text():
    """§۱۰ — کارت یک کپیِ دومِ محتوای مالک نمی‌سازد؛ فقط هش."""
    c = _fresh()
    secret_ish = "خصوصی-۴۴۲۱-متنِ-کارت"
    lc.put(c, name="home", text=f"وضعیت: {secret_ish}", chat_id=7)
    raw = lc._state_path().read_text("utf-8")
    assert secret_ish not in raw, "متنِ کارت در state نشت کرد"
    assert "sha" in raw, "هش ذخیره نشد ⇒ تشخیصِ «بی‌تغییر» ممکن نیست"


def t_i_counters_make_the_effect_measurable():
    """بدونِ عدد، «کارتِ زنده پیامِ نو را کم کرد» یک ادعاست."""
    c = _fresh()
    lc.put(c, name="home", text="۱", chat_id=7)
    lc.put(c, name="home", text="۲", chat_id=7)
    lc.put(c, name="home", text="۳", chat_id=7)
    s = lc.stats()
    assert s["sends"] == 1 and s["edits"] == 2, s
    assert s["cards"] == 1, s


def t_j_moving_a_card_to_another_chat_starts_a_new_message():
    """شناسهٔ پیام مالِ یک چت است. ویرایشِ آن id در چتِ دیگر یا خطا می‌دهد یا
    — بدتر — پیامِ اشتباهی را عوض می‌کند."""
    c = _fresh()
    a = lc.put(c, name="home", text="متن", chat_id=7)
    b = lc.put(c, name="home", text="متن", chat_id=9)
    assert b["action"] == "sent" and b["message_id"] != a["message_id"], (a, b)
    assert len(c.edits) == 0, ("در چتِ نو ویرایش زد", c.edits)


def t_k_two_names_are_two_independent_cards():
    c = _fresh()
    lc.put(c, name="home", text="خانه", chat_id=7)
    lc.put(c, name="money", text="پول", chat_id=7)
    lc.put(c, name="home", text="خانهٔ ۲", chat_id=7)
    assert len(c.sends) == 2 and len(c.edits) == 1, (c.sends, c.edits)
    assert lc.stats()["cards"] == 2, lc.stats()


def t_l_corrupt_state_does_not_explode():
    """یک بایتِ خراب نباید کلِ لایه را بکشد — fail-soft، مثلِ بقیهٔ سیستم."""
    c = _fresh()
    lc._state_path().write_text("{ این JSON نیست", encoding="utf-8")
    r = lc.put(c, name="home", text="متن", chat_id=7)
    assert r["action"] == "sent", r


def t_m_the_module_has_no_side_effects_at_import():
    """‏import نباید چیزی بفرستد یا بنویسد — این ماژول در مسیرِ داغِ beat است."""
    tree = ast.parse(SRC)
    for n in tree.body:
        assert not isinstance(n, (ast.Expr, ast.Call)) or isinstance(
            getattr(n, "value", None), ast.Constant), (
            f"دستورِ سطحِ ماژول در خطِ {n.lineno} — اثرِ جانبیِ import")


# ── ۵. سیم‌کشیِ واقعی: رسیدِ بوت ─────────────────────────────────────────────
# ⚠️ چرا این بخش وجود دارد: ماژولی که هیچ‌کس صدایش نمی‌زند یک «قابلیتِ تاریک»
# است — همان چیزی که کلِ ۰۸-۰۴ صرفِ رفعش شد. تست‌های بالا خودِ ابزار را
# می‌سنجند؛ این‌ها می‌سنجند که ابزار **واقعاً در مسیرِ تولید** است.
#
# هدف با اندازه‌گیری انتخاب شد، نه با حدس: از ۲۴ پیامِ خودجوشِ DM در ۲۴ ساعت،
# **۱۶ تا** رسیدِ بوت بود (هر کدام sha ِ یکتا چون PID فرق می‌کند) — دو-سومِ
# کلِ شلوغیِ DM.
def _boot_center():
    import importlib.util
    center = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"
    spec = importlib.util.spec_from_file_location("cp_boot_card", center)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    class _C(FakeClient):
        owner_chat_id = 555
        center_chat_id = -100

        def wired(self):
            return True

        def set_commands(self, *a, **k):
            return True

        def delete_commands(self, *a, **k):
            return True

        def create_topic(self, *a, **k):
            return None

        def edit_topic(self, *a, **k):
            return True

    return m, _C


def _boot_once(m, client):
    """یک «راه‌اندازی» — با پاک‌کردنِ اثرِ PID، انگار پروسه نو است."""
    c = m.Center(client=client)
    c.stopped = lambda: False
    c._wired = lambda: True
    cfg = m._load_config()
    cfg.pop("boot_receipt_pid", None)
    m._save_config(cfg)
    c.ensure_setup()
    return c


def t_n_with_the_flag_off_the_boot_receipt_is_an_ordinary_message():
    """دکمهٔ برگشت، روی مسیرِ **واقعی** نه روی ابزار: خاموش ⇒ رفتارِ دیروز."""
    _fresh(monkey_on=False)
    m, C = _boot_center()
    cl = C()
    _boot_once(m, cl)
    boots = [t for t in cl.sends if "بیدار" in t["text"]]
    assert boots, "رسیدِ بوت اصلاً نرفت"
    assert not cl.edits, ("با فلگِ خاموش ویرایش زد", cl.edits)
    assert not lc._state_path().exists(), "با فلگِ خاموش state ساخت"


def t_o_with_the_flag_on_every_later_boot_edits_the_same_message():
    """قلبِ فاز ۱ روی بزرگ‌ترین منبعِ شلوغی: ۱۶ پیام در روز ⇒ ۱ پیام + ویرایش."""
    _fresh(monkey_on=True)
    m, C = _boot_center()
    cl = C()
    _boot_once(m, cl)
    first = [t for t in cl.sends if "بیدار" in t["text"]]
    assert len(first) == 1, ("بوتِ اول باید یک پیام بسازد", cl.sends)
    mid = lc.get("boot").get("message_id")

    for _ in range(3):
        _boot_once(m, cl)
    later = [t for t in cl.sends if "بیدار" in t["text"]]
    assert len(later) == 1, (
        "بوت‌های بعدی پیامِ نو ساختند ⇒ فاز ۱ روی این مسیر کار نمی‌کند", later)
    edits = [e for e in cl.edits if "بیدار" in e["text"]]
    assert len(edits) == 3, (edits,)
    assert all(e["message_id"] == mid for e in edits), (
        "ویرایش روی پیام‌های مختلف رفت", mid, edits)


def t_p_the_card_carries_a_restart_counter():
    """کارت باید از پیامی که جایش را می‌گیرد **پرمعناتر** باشد، وگرنه فقط
    اطلاعات را پنهان کرده‌ایم. «۱۶ ری‌استارت امروز» یک هشدار است؛ ۱۶ پیامِ
    جدا فقط شلوغی."""
    _fresh(monkey_on=True)
    m, C = _boot_center()
    cl = C()
    _boot_once(m, cl)
    # ⚠️ عددِ مطلق را assert نکن: شمارنده در `center-config` می‌ماند و
    # تست‌های قبلیِ همین اجرا بالا برده‌اندش. یک assert ِ وابسته به ترتیب،
    # روزی به‌خاطرِ همسایه‌اش قرمز می‌شود نه به‌خاطرِ کد. **افزایش** را بسنج.
    before = int(m._load_config().get("boot_count") or 0)
    _boot_once(m, cl)
    _boot_once(m, cl)
    after = int(m._load_config().get("boot_count") or 0)
    assert after == before + 2, ("شمارنده بالا نرفت", before, after)

    txt = ([e["text"] for e in cl.edits if "بیدار" in e["text"]] or [""])[-1]
    assert "ری‌استارتِ امروز" in txt, ("شمارنده در کارت نیست", txt)
    _fa = str(after).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    assert _fa in txt, ("عددِ کارت با شمارندهٔ واقعی نمی‌خواند", _fa, txt)


def t_q_the_counter_resets_on_a_new_day():
    """شمارنده‌ای که ریست نشود، بعد از یک هفته یک عددِ بی‌معنی است."""
    _fresh(monkey_on=True)
    m, C = _boot_center()
    cl = C()
    _boot_once(m, cl)
    cfg = m._load_config()
    cfg["boot_count_date"] = "2020-01-01"       # دیروزِ خیلی دور
    cfg["boot_count"] = 99
    m._save_config(cfg)
    _boot_once(m, cl)
    assert int(m._load_config().get("boot_count")) == 1, (
        "شمارنده در روزِ نو ریست نشد", m._load_config().get("boot_count"))


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_living_card: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
