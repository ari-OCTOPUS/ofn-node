"""test_tg_guide.py — دستورالعملِ استفاده، داخلِ خودِ تلگرام.

مالک گفت «گروه تلگرام هیچی نداره که دستورالعمل». راهنما وجود داشت — در
ابسیدین. راهنمایی که در جای دیگری باشد راهنما نیست، پس متنِ کوتاهش در
General ِ گروه پین می‌شود.

پوششِ این فایل سه چیز است:
  ۱. یک‌بار ساخته و پین می‌شود؛ راه‌اندازیِ دوباره پیامِ تازه نمی‌سازد
     (وگرنه هر restart گروه را کثیف می‌کند).
  ۲. متن هرگز secret یا توکن ندارد.
  ۳. **ادعاهایش با کد بخوانَد** — راهنمای دروغ بدتر از نبودنِ راهنماست.
     مثلاً «۴ دکمه» را با خودِ `leg_tasks.card_keyboard` می‌سنجم، نه با چشم.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-guide")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402
import guide    # noqa: E402
import leg_tasks as lt   # noqa: E402

CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"


class FakeClient:
    def __init__(self):
        self.calls = []
        self._mid = 500

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream=None):
        self.calls.append(("send", {"text": text, "pin": pin,
                                    "topic_id": topic_id}))
        self._mid += 1
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def pin_message(self, message_id, chat_id=None):
        return True

    def create_topic(self, name, chat_id=None):
        self.calls.append(("create_topic", {"name": name}))
        self._mid += 1
        return self._mid

    def set_commands(self, commands):
        return True

    def named(self, kind):
        return [d for k, d in self.calls if k == kind]


def _render():
    import types
    m = types.SimpleNamespace()
    m.render_status_line = lambda *a, **k: "STATUS"
    m.render_leg_digest = lambda leg, data: ""
    m.render_decision_box = lambda *a, **k: ("", [])
    m.collect_open_decisions = lambda *a, **k: []
    m.collect_legs = lambda *a, **k: {}
    return m


def _reset():
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)


def t_the_guide_is_pinned_in_the_group_once_not_on_every_restart():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=_render())
    c.ensure_setup()
    pinned = [s for s in fc.named("send") if s["pin"]]
    gid = json.loads(CFG_PATH.read_text("utf-8")).get("guide_message_id")
    assert isinstance(gid, int), "راهنما در گروه ساخته نشد"
    assert any("این گروه چطور کار می‌کند" in s["text"] for s in pinned), \
        "راهنما پین نشد"
    n_before = len(fc.named("send"))
    c.ensure_setup()                       # راه‌اندازیِ دوباره
    assert len(fc.named("send")) == n_before, \
        "راه‌اندازیِ دوباره پیامِ تازه ساخت ⇒ هر restart گروه را کثیف می‌کند"
    assert json.loads(CFG_PATH.read_text("utf-8"))["guide_message_id"] == gid


def t_a_changed_guide_is_edited_never_resent():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=_render())
    c.ensure_setup()
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    cfg["guide_hash"] = "0" * 16          # یعنی متن عوض شده
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")
    n_send = len(fc.named("send"))
    c.ensure_setup()
    assert len(fc.named("send")) == n_send, "متنِ عوض‌شده را دوباره send کرد"
    assert any(e["message_id"] == cfg["guide_message_id"]
               for e in fc.named("edit")), "ویرایش نشد"
    assert json.loads(CFG_PATH.read_text("utf-8"))["guide_hash"] != "0" * 16


def t_the_guide_carries_no_secret():
    """نامِ کاربریِ بات عمومی است؛ توکن هرگز. یک راهنما جای بدی برای لو رفتن
    است چون **پین** می‌شود و همه‌جا می‌مانَد."""
    for txt in (guide.group_text(), guide.dm_text()):
        assert not re.search(r"\d{8,}:[A-Za-z0-9_-]{20,}", txt), "شکلِ توکنِ بات"
        assert not re.search(r"(?i)\b(token|secret|api[_-]?key|seed)\b", txt)
        assert not re.search(r"\b0x[0-9a-fA-F]{20,}\b", txt), "آدرسِ کیف پول"


def t_every_claim_in_the_guide_is_true_in_the_code():
    """⚠️ مهم‌ترین بندِ این فایل. راهنما به مالک **قول** می‌دهد؛ اگر کد قولش را
    نگه ندارد، راهنما فعالانه گمراه می‌کند — بدتر از نبودنش."""
    g = guide.group_text()
    # قولِ «۴ دکمه»
    kb = lt.card_keyboard("lead")
    n_btn = sum(len(row) for row in kb)
    assert "۴ دکمه" in g and n_btn == 4, f"راهنما ۴ دکمه گفت، کد {n_btn} دارد"
    # قولِ «فقط ۴ حالت»
    assert "۴ حالت" in g and len(lt._STATES) == 4, \
        f"راهنما ۴ حالت گفت، کد {len(lt._STATES)} دارد"
    # قولِ اینکه سؤال کار نمی‌سازد
    assert lt.is_question("وضعیتش چیه؟") is True, \
        "راهنما گفت سؤال کار نمی‌سازد ولی طبقه‌بند سؤال را نمی‌شناسد"
    # ⚠️ نسخهٔ اولِ این بند نوشته بود `assert "بساز:" in guide.dm_text()` —
    # و جهشِ «حذفِ دستورِ بساز از متن» **زنده ماند**، چون خودِ خطِ مثال هم
    # همان رشته را دارد. تاتولوژیِ رشته‌ای گارد نیست.
    # سنجهٔ واقعی: هر فرمانی که راهنما به مالک **یاد می‌دهد** را طبقه‌بندِ
    # واقعی بپذیرد. راهنمایی که فرمانی را بیاموزد که کد نمی‌فهمد، فعالانه
    # وقتِ مالک را می‌سوزاند.
    import build_cmd as bc
    dm = guide.dm_text()
    examples = [ln.strip() for ln in dm.splitlines() if ln.strip().startswith("بساز:")]
    assert examples, "راهنمای DM هیچ مثالِ «بساز:» ندارد"
    for ex in examples:
        assert bc.is_build_request(ex) is True, f"کد این را نمی‌فهمد: {ex}"
        assert bc.strip_prefix(ex), f"بدنهٔ خالی بعد از strip: {ex}"
    # و دستورش هم باید در متن باشد، نه فقط مثالش
    assert "بنویس «بساز:»" in dm, "دستورِ «بساز:» از متن حذف شده — فقط مثال مانده"
    # مثالِ کارِ آزادِ گروه باید **کار** شود نه سؤال (قولِ «می‌شود یک کار»)
    assert "«این لینک را بررسی کن»" in g, "مثالِ کارِ آزادِ گروه حذف شده"
    assert lt.is_question("این لینک را بررسی کن") is False, \
        "راهنما گفت این کار می‌شود ولی سؤال طبقه‌بندی شد"


def t_w2_group_promises_natural_commands_the_classifier_really_knows():
    """موج ۲: هر فرمانِ طبیعی که راهنمای گروه یاد می‌دهد، طبقه‌بندِ واقعیِ
    leg_commands باید بشناسد — قول‌به‌قول، نه با چشم."""
    import leg_commands as lc
    g = guide.group_text()
    for ex, want in (("وضعیت", "status"), ("صف", "queue"),
                     ("گزارش امروز", "report")):
        assert f"«{ex}»" in g, f"مثالِ «{ex}» از راهنما حذف شده"
        assert lc.classify(ex) == want, \
            f"راهنما «{ex}» را یاد می‌دهد ولی طبقه‌بند نمی‌فهمد"
    assert "«هدف روزانه ۵»" in g and lc.parse_kpi_set("هدف روزانه ۵") == 5, \
        "قولِ «هدف روزانه N» با parse_kpi_set نمی‌خوانَد"
    assert "«این را به صف اضافه کن: متنِ کار»" in g \
        and lc.strip_enqueue_prefix("این را به صف اضافه کن: متنِ کار") == "متنِ کار", \
        "قولِ «به صف اضافه کن» با strip_enqueue_prefix نمی‌خوانَد"
    # قولِ ریپلای به کارتِ 🚧: کارتِ مسدود واقعاً 🚧 و شناسهٔ TASK دارد و
    # مسیرِ رفعِ مانع در کد هست (resolve_blocked).
    assert "🚧" in g, "قولِ کارتِ 🚧 از راهنما حذف شده"
    bt = lt.blocked_text({"id": "TASK-9", "question": "کدام سایز؟"})
    assert "🚧" in bt and "TASK-9" in bt, \
        "کارتِ مسدود 🚧/شناسه ندارد — ریپلایِ مالک به چه چیزی بند شود؟"
    assert callable(lt.resolve_blocked), "resolve_blocked وجود ندارد"
    # قولِ «لید فقط اتاقِ 🎨»: طبقه‌بندِ capture لید را به پای lead می‌چسباند.
    import capture as cap
    kr = cap.classify("یک لید از مشتری برای نقاشی")
    assert kr["kind"] == "lead" and kr["leg"] == "lead", \
        f"قولِ «لید فقط 🎨» با طبقه‌بندِ capture نمی‌خوانَد: {kr}"


def t_w2_dm_promises_capture_reminder_brief_vault_and_menu_are_real():
    """موج ۲: قول‌های DM — capture ِ یک‌ژسته و «ثبت:»، یادآوریِ زبانِ طبیعی،
    بریفِ صبح/شب، «از والت بپرس»، منوی ۸تایی — هر یک به کدِ واقعی بند."""
    import re as _re
    dm = guide.dm_text()
    import capture as cap
    # «ثبت: خرید رنگ ۵۰ دلار» — از خودِ درزِ مرکز (نه فقط ماژول): flag روشن،
    # پیام از هوکِ واقعی می‌گذرد و ack ِ هزینه می‌گیرد.
    ex_sabt = "ثبت: خرید رنگ ۵۰ دلار"
    assert f"«{ex_sabt}»" in dm, "مثالِ «ثبت:» از راهنما حذف شده"
    _reset()
    fc = FakeClient()
    fc.owner_chat_id = 777
    c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=_render())
    os.environ["OCTOPUS_TG_CAPTURE"] = "1"
    try:
        r = c._capture_hook({"message_id": 4001, "chat": {"id": 777},
                             "text": ex_sabt})
    finally:
        os.environ.pop("OCTOPUS_TG_CAPTURE", None)
    assert r is not None and r.get("kind") == "capture" \
        and r.get("capture_kind") == "expense", \
        f"قولِ «ثبت:» در درزِ مرکز برقرار نیست: {r}"
    # capture ِ متن/عکس/ویس: تشخیصِ رسانه واقعی است، نه ادعا.
    assert cap._media_kind({"voice": {"file_id": "x"}}, "") == "voice"
    assert cap._media_kind({"photo": [{"file_id": "y"}]}, "") == "photo"
    # یادآوریِ زبانِ طبیعی: مثالِ خودِ راهنما باید با ساعتِ درست parse شود.
    import reminders as rm
    from datetime import datetime as _dt
    ex_rm = "فردا ساعت ۹ زنگ بزن به علی"
    assert f"«{ex_rm}»" in dm, "مثالِ یادآوری از راهنما حذف شده"
    base = _dt(2026, 7, 31, 12, 0).timestamp()
    due, cleaned = rm.parse_when(ex_rm, now=base)
    assert due is not None and _dt.fromtimestamp(due).hour == 9, \
        f"مثالِ یادآوریِ راهنما درست parse نمی‌شود: {due}"
    assert "زنگ بزن" in cleaned, f"متنِ پاک‌شدهٔ یادآوری غلط است: {cleaned!r}"
    # بریفِ صبح/شب: قولِ راهنما به خروجیِ واقعیِ ماژول بند است.
    import brief as bf
    assert "بریف" in dm and "بریف صبح" in bf.morning_text(now=base, cfg={})
    assert "جمع‌بندی" in dm and "جمع‌بندی شب" in bf.evening_text(now=base, cfg={})
    # «از والت بپرس …»: مثالِ راهنما باید ماشهٔ واقعیِ مرکز را بکشد.
    m = _re.search(r"«(از والت[^»]+)»", dm)
    assert m, "مثالِ «از والت بپرس» از راهنما حذف شده"
    assert center.Center._vault_intent(m.group(1)) is True, \
        f"مثالِ راهنما ماشهٔ vault را نمی‌کشد: {m.group(1)!r}"
    # و جوابِ vault واقعاً منبع‌دار است (فهرست را ماژول می‌سازد نه مدل).
    import ask_vault as av
    import inspect as _ins
    assert "منابع:" in _ins.getsource(av.query), \
        "قولِ «با ذکرِ منبع» در ask_vault.query برقرار نیست"
    # منوی ۸تایی: شمارِ واقعیِ COMMANDS.
    assert "۸ دکمه" in dm and len(center.COMMANDS) == 8, \
        f"راهنما ۸ دکمه گفت، منو {len(center.COMMANDS)} دارد"


def _run():
    ok = fail = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("t_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ✅ {name}")
            ok += 1
        except AssertionError as e:
            print(f"  ❌ {name}: {e}")
            fail += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ {name}: {type(e).__name__}: {e}")
            fail += 1
    total = ok + fail
    mark = "✅" if fail == 0 else "❌"
    print(f"\n{mark} test_tg_guide: {ok}/{total}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
