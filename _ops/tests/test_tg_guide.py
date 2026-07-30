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
    # مثالِ گروه باید **کار** شود نه سؤال (قولِ «می‌شود یک کار»)
    g_ex = [ln.strip().strip("«»") for ln in g.splitlines()
            if ln.strip().startswith("«") and ln.strip().endswith("»")]
    assert g_ex, "راهنمای گروه هیچ مثالی ندارد"
    for ex in g_ex:
        assert lt.is_question(ex) is False, \
            f"راهنما گفت این کار می‌شود ولی سؤال طبقه‌بندی شد: {ex}"


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
