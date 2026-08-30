"""test_mirror_rooms_memory.py — WS-6: حافظهٔ آینه در هر اتاق.

حکمِ ثبت‌شدهٔ مالک دو نیمه دارد که عمداً **نامتقارن**اند، و کلِ ارزشِ این تست
همین نامتقارنی است:

    حافظهٔ ۸ نوبتی → per-room.  گفتگوی ماینینگ نباید در اتاقِ پول سر دربیاورد.
    لایهٔ تصحیح    → global.     «نه، این‌طور نیست» هر جا گفته شود باید در فهمِ
                                 کلیِ او از خودش بنشیند.

یک پیاده‌سازیِ **متقارن** — هر دو global، یا هر دو per-room — از هر تستِ ساده‌ای
سبز بیرون می‌آید. پس هر ادعا این‌جا **جفتی** سنجیده می‌شود: در همان لحظه که
تصحیح باید عبور کند، تاریخچه نباید. یک assert به‌تنهایی این قرارداد را نمی‌بندد.

و هر ادعا دندان دارد: رفتارِ پیش از WS-6 بازسازی می‌شود و نشان داده می‌شود که
همان assert رویش می‌افتد. assertی که روی کدِ قدیمی هم سبز است، چیزی را نگه
نمی‌دارد.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness                       # noqa: E402
ENV = harness.setup("mirror-rooms")   # ← اولین کارِ بعد از sys.path

import mirror_room as mr             # noqa: E402
import ask_brain as ab               # noqa: E402

MINE = "چند تا ماینر الان روشن است؟"
MONEY = "این ماه چقدر خرج شد؟"
CORR = "نه، این‌طور نیست — دستگاهِ دوم از دیروز خاموش است"


# ─── ابزار ──────────────────────────────────────────────────────────────────
def _on(mirror=True, rooms=True):
    for flag, want in ((mr.FLAG, mirror), (ab.FLAG, mirror),
                       (mr.ROOM_FLAG, rooms)):
        if want:
            os.environ[flag] = "1"
        else:
            os.environ.pop(flag, None)
    os.environ["TG_ASK_BRAIN_DAILY"] = "40"


def _off_all():
    for flag in (mr.FLAG, ab.FLAG, mr.ROOM_FLAG):
        os.environ.pop(flag, None)
    os.environ.pop("TG_ASK_BRAIN_DAILY", None)


def _hist_files():
    d = mr.HISTORY.parent
    return sorted(d.glob("mirror-history*.jsonl")) if d.exists() else []


def _reset():
    for p in _hist_files() + [mr.CORRECTIONS, ab.STATE]:
        try:
            p.unlink()
        except OSError:
            pass
    ab._MEMO.update(date="", used=0, last_ts=0.0)


def _rows(p: Path) -> list:
    if not p.exists():
        return []
    out = []
    for line in p.read_text("utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _fn(text=None, calls=None, tier="primary"):
    """مغزِ ساختگی. متنِ پیش‌فرض بلندتر از MIN_CHARS است وگرنه `ask` جوابِ خودش
    را «too-short-answer» می‌شمارد و هیچ‌چیز در حافظه نمی‌نشیند."""
    calls = calls if calls is not None else []
    body = text if text is not None else ("ج" * 200)

    def f(task, prompt, system="", max_tokens=400, **kw):
        calls.append({"prompt": prompt, "system": system})
        return {"ok": True, "text": body, "model": "fugu", "tier": tier}

    f._calls = calls
    return f


# ── بازسازیِ رفتارِ پیش از WS-6 ────────────────────────────────────────────
# بدنهٔ `recent_turns` **کلمه‌به‌کلمه** پیش از این تغییر: یک فایل، بی‌هیچ مفهومی
# از اتاق. این‌جا فقط ردیف‌ها را ورودی می‌گیرد تا مسیرِ فایل دخالتی نکند.
def _legacy_recent_turns(rows: list, n: int = 8) -> list:
    return [{"تو": str(r.get("q") or "")[:700],
             "من": str(r.get("a") or "")[:700]}
            for r in rows if r.get("q") and r.get("a")][-n:]


def _fails(fn) -> bool:
    """آیا این assert می‌افتد؟ (برای اثباتِ دندان)"""
    try:
        fn()
    except AssertionError:
        return True
    return False


# ─── ۱ · پیش‌فرض خاموش، و خاموش = رفتارِ امروز ──────────────────────────────
def t_the_room_layer_is_off_unless_explicitly_armed():
    """فلگ در PAPER_FULL_FLAGS نیست، پس غیابش واقعاً یعنی خاموش — همان قاعده‌ای
    که در این مخزن سه بار اشتباه خوانده شده."""
    import wiring
    assert mr.ROOM_FLAG not in wiring.PAPER_FULL_FLAGS, (
        f"{mr.ROOM_FLAG} در PAPER_FULL_FLAGS است ⇒ غیابش یعنی روشن، نه خاموش")
    os.environ.pop(mr.ROOM_FLAG, None)
    assert mr.all_rooms_enabled() is False
    for junk in ("mining", "money", "", "آینه"):
        assert mr.room_slug(junk) == mr.DEFAULT_ROOM, junk
        assert mr.history_path(junk) == mr.HISTORY, junk


def t_flag_off_writes_the_same_row_to_the_same_file():
    """خاموش = بایت‌به‌بایتِ امروز. صداکننده هر اتاقی پاس بدهد، هیچ فایلِ تازه‌ای
    ساخته نمی‌شود و رکورد هیچ کلیدِ تازه‌ای نمی‌گیرد."""
    _reset()
    _on(mirror=True, rooms=False)
    r = mr.ask(MINE, room="mining", ask_fn=_fn(), now=1000.0)
    assert r["ok"], r
    files = _hist_files()
    assert files == [mr.HISTORY], [p.name for p in files]
    rows = _rows(mr.HISTORY)
    assert len(rows) == 1
    assert "room" not in rows[0], rows[0]
    assert set(rows[0]) == {"ts", "schema", "q", "a", "model", "tier",
                            "was_correction"}, sorted(rows[0])
    # و تصحیحِ ثبت‌شده هم کلیدِ تازه نمی‌گیرد
    mr.record_correction("نه، غلط است", room="mining")
    assert "room" not in _rows(mr.CORRECTIONS)[0]


def t_observe_is_a_hard_noop_while_the_flag_is_off():
    """اگر observe با فلگِ خاموش می‌نوشت، ردیف‌های تازه در همان فایلِ امروز
    می‌نشستند و «خاموش = رفتارِ امروز» بی‌صدا نقض می‌شد."""
    _reset()
    _on(mirror=True, rooms=False)
    before = _rows(mr.HISTORY)
    r = mr.observe("mining", MINE, by="⛏ بازوی معدن")
    assert r == {"ok": False, "reason": "flag-off"}, r
    assert _rows(mr.HISTORY) == before
    assert _hist_files() in ([], [mr.HISTORY])


# ─── ۲ · دندان: تاریخچه از اتاق بیرون نمی‌زند ───────────────────────────────
def t_TEETH_a_mining_turn_never_surfaces_in_the_money_room():
    _reset()
    _on()
    mr.ask(MINE, room="mining", ask_fn=_fn("پاسخِ معدن " + "م" * 90), now=1000.0)
    calls = []
    mr.ask(MONEY, room="money", ask_fn=_fn("پاسخِ پول " + "پ" * 90, calls=calls),
           now=1100.0)
    assert len(calls) == 1, calls
    prompt = calls[0]["prompt"]
    assert MONEY in prompt, "سؤالِ خودِ اتاق به مغز نرسید"
    assert MINE not in prompt, "نشتیِ گفتگوی ماینینگ به اتاقِ پول"
    assert len(mr.recent_turns(room="mining")) == 1
    assert len(mr.recent_turns(room="money")) == 1
    assert mr.history_path("mining") != mr.history_path("money")

    # نبودِ نشتی به‌تنهایی کافی نیست: یک پیاده‌سازی که **هیچ** تاریخچه‌ای ندهد
    # هم همان assert را سبز می‌کند. پس در همان نفس، پیوستگیِ خودِ اتاق:
    calls2 = []
    mr.ask("و از آن چقدر برگشت؟", room="money", ask_fn=_fn(calls=calls2),
           now=1200.0)
    p2 = calls2[0]["prompt"]
    assert MONEY in p2, "اتاقِ پول نوبتِ قبلیِ **خودش** را ندید"
    assert MINE not in p2, "نشتیِ گفتگوی ماینینگ به اتاقِ پول"

    # ── دندان ──
    # پیش از WS-6 هر دو نوبت در **یک** فایل می‌نشستند و خواننده مفهومِ اتاق
    # نداشت. همان دو ردیف را به خوانندهٔ قدیمی بده:
    legacy_rows = _rows(mr.history_path("mining")) + _rows(mr.history_path("money"))
    blob = json.dumps(_legacy_recent_turns(legacy_rows), ensure_ascii=False)
    assert MONEY in blob and MINE in blob, "بازسازیِ رفتارِ قبلی درست نیست"
    assert _fails(lambda: _assert_no_leak(blob)), (
        "همان assert روی کدِ پیش از WS-6 هم سبز است ⇒ بی‌دندان")


def _assert_no_leak(blob: str):
    assert MINE not in blob, "نشتیِ بینِ اتاق‌ها"


def t_two_persian_room_names_do_not_share_one_bucket():
    """اسمِ اتاق‌های گروه فارسی است. scrubِ ساده همه را به یک سطلِ خالی می‌برد و
    دقیقاً همان نشتی‌ای رخ می‌دهد که این ماژول برای منعش نوشته شده."""
    _on()
    a, b = mr.room_slug("آینهٔ من"), mr.room_slug("قلبِ سیستم")
    assert a != b, (a, b)
    assert a != mr.DEFAULT_ROOM and b != mr.DEFAULT_ROOM
    assert mr.history_path("آینهٔ من") != mr.history_path("قلبِ سیستم")
    # اتاقِ آینه سرِ جای امروزش می‌ماند — هیچ مهاجرتِ فایلی لازم نیست
    assert mr.history_path("mirror") == mr.HISTORY
    assert mr.room_slug("") == mr.GENERAL_ROOM, "خصوصی/General نباید با آینه یکی شود"
    assert mr.history_path("") != mr.HISTORY


# ─── ۳ · دندان: تصحیح از اتاق بیرون **می‌زند** ──────────────────────────────
def t_TEETH_a_correction_said_in_the_mining_room_reaches_the_money_room():
    _reset()
    _on()
    r = mr.observe("mining", CORR, by="⛏ بازوی معدن")
    assert r["ok"] and r["recorded_correction"], r
    corr_rows = _rows(mr.CORRECTIONS)
    assert len(corr_rows) == 1 and corr_rows[0].get("room") == "mining", corr_rows
    assert any(CORR[:24] in c for c in mr.corrections()), mr.corrections()

    calls = []
    mr.ask(MONEY, room="money", ask_fn=_fn(calls=calls), now=2000.0)
    prompt = calls[0]["prompt"]
    assert CORR[:24] in prompt, "تصحیحِ سراسری به اتاقِ دیگر نرسید"
    # و در همان نفس: جملهٔ اتاقِ ماینینگ **نرسیده**. این جفت، کلِ قرارداد است.
    assert MINE not in prompt

    # ── دندان ──
    # طراحیِ متقارنِ اشتباه: تصحیح هم per-room نگه داشته شود. آن‌وقت اتاقِ پول
    # فقط تصحیح‌های خودش را می‌بیند — یعنی هیچ.
    per_room = [str(c.get("text") or "") for c in corr_rows
                if c.get("room") == "money"]
    assert not per_room, per_room
    blob = json.dumps(per_room, ensure_ascii=False)
    assert _fails(lambda: _assert_correction_reaches(blob)), (
        "همان assert روی طراحیِ per-room هم سبز است ⇒ بی‌دندان")


def _assert_correction_reaches(blob: str):
    assert CORR[:24] in blob, "تصحیحِ سراسری نرسید"


def t_a_correction_in_the_general_room_is_still_global():
    """«هر جا» یعنی خصوصی و General هم — نه فقط تاپیک‌های نام‌دار."""
    _reset()
    _on()
    assert mr.observe("", CORR, by="🗺 وضعیت")["recorded_correction"]
    assert any(CORR[:24] in c for c in mr.corrections())
    calls = []
    mr.ask(MINE, room="mining", ask_fn=_fn(calls=calls), now=3000.0)
    assert CORR[:24] in calls[0]["prompt"]


def t_the_correction_detector_is_not_loosened_by_the_new_path():
    """رگرسیونِ ۰۷-۲۷: زیررشتهٔ «نه » هر کلمه‌ای را می‌گرفت («روزانه»، «خانه»)
    و نویز را برای همیشه در فهمِ او از خودش می‌کاشت. مسیرِ تازه نباید همان درِ
    پشتی را باز کند."""
    _reset()
    _on()
    for benign in ("برنامهٔ روزانه چیست؟", "گزارشِ ماهانه را بده",
                   "چگونه کار می‌کند؟", "خانه کجاست"):
        mr.observe("mining", benign, by="x")
        assert mr.corrections() == [], f"مثبتِ کاذب روی: {benign}"
    mr.observe("mining", "نخیر، این عدد غلط است", by="x")
    assert len(mr.corrections()) == 1


# ─── ۴ · observe فقط می‌بیند: نه مغز، نه سهمیه، نه پیام ─────────────────────
def t_observe_spends_nothing_and_calls_no_brain():
    """تصمیمِ ثبت‌شده: جمله‌ای که کارمند جوابش را داد، آینه می‌بیند و جواب
    نمی‌دهد. اگر observe سهمیه بخورد، همان تصمیم بی‌معنی است — چون هزینه‌اش را
    داده‌ایم بی‌آنکه جوابی گرفته باشیم."""
    _reset()
    _on()
    used_before = int(ab._MEMO.get("used", 0))
    for i in range(5):
        assert mr.observe("mining", f"جملهٔ شمارهٔ {i} برای ثبت", by="⛏")["ok"]
    assert int(ab._MEMO.get("used", 0)) == used_before, "observe سهمیه خورد"
    assert not ab.STATE.exists() or _rows_used(ab.STATE) == used_before
    # و ماژول اصلاً مسیرِ ارسال ندارد (AST، نه grep روی متن)
    import ast
    tree = ast.parse(Path(mr.__file__).read_text("utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for danger in ("send", "post", "urlopen", "system", "popen", "Popen"):
        assert danger not in called, f"مسیرِ ارسال/اجرا در آینه: {danger}"


def _rows_used(p: Path) -> int:
    try:
        return int((json.loads(p.read_text("utf-8")) or {}).get("used", 0))
    except Exception:  # noqa: BLE001
        return 0


def t_an_observed_turn_is_never_quoted_as_the_mirrors_own_answer():
    """مرکز متنِ جوابِ کارمند را در دست ندارد. اگر آن جای خالی با یک
    placeholder پر شود، مدل جمله‌ای را به **خودش** نسبت می‌دهد که نگفته —
    همان fabrication که این مخزن یک بار خورده. ندانستن باید ندانستن بماند."""
    _reset()
    _on()
    mr.observe("mining", MINE, by="⛏ بازوی معدن")
    turns = mr.recent_turns(room="mining")
    assert len(turns) == 1, turns
    t0 = turns[0]
    assert t0["تو"] == MINE
    assert "من" not in t0, t0
    assert t0["جوابش_را_ندیدم"] == "⛏ بازوی معدن", t0
    calls = []
    mr.ask("خب حالا چه کنم؟", room="mining", ask_fn=_fn(calls=calls), now=4000.0)
    p = calls[0]["prompt"]
    assert MINE in p and "جوابش_را_ندیدم" in p, "نوبتِ دیده‌شده به مغز نرسید"


def t_the_room_never_bypasses_the_paid_brain_gate():
    """مسیرِ تازه نباید گاردهای موجود را دور بزند: خاموشیِ آینه، و مغزِ رایگان
    که جای مغزِ پولی می‌نشیند."""
    _reset()
    _on(mirror=False, rooms=True)
    assert mr.ask(MINE, room="mining", ask_fn=_fn(), now=5000.0) == {
        "ok": False, "reason": "flag-off"}
    assert mr.observe("mining", MINE, by="x") == {"ok": False, "reason": "flag-off"}
    _on()
    r = mr.ask(MINE, room="mining", ask_fn=_fn(tier="local"), now=5100.0)
    assert r["ok"] is False and r["reason"] == "not-a-paid-brain", r
    assert _rows(mr.history_path("mining")) == [], "جوابِ ردشده در حافظه نشست"


def t_the_mirror_topic_itself_is_untouched_by_the_room_layer():
    """اتاقِ آینه با فلگِ **روشن** هم باید همان فایل و همان رکوردِ امروز را
    داشته باشد — وگرنه تاریخچهٔ موجودش بی‌صدا یتیم می‌شود."""
    _reset()
    _on()
    r = mr.ask(MINE, room="mirror", ask_fn=_fn(), now=6000.0)
    assert r["ok"] and r["room"] == "mirror", r
    assert _hist_files() == [mr.HISTORY], [p.name for p in _hist_files()]
    row = _rows(mr.HISTORY)[0]
    assert "room" not in row, row
    assert mr.recent_turns(room="mirror")[-1]["تو"] == MINE
    # ولی صداکنندهٔ **بی‌آرگومان** با فلگِ روشن اتاقِ General را می‌بیند، نه آینه.
    # `room=""` واقعاً یعنی خصوصی/General؛ اگر به آینه می‌رفت، گفتگوی خصوصی در
    # تاپیکِ آینه سر درمی‌آورد — همان نشتی‌ای که WS-6 منع می‌کند.
    # (با فلگِ خاموش همان آینه است؛ `t_flag_off_...` همان را می‌سنجد.)
    assert mr.recent_turns() == [], "خصوصی/General با تاپیکِ آینه یکی شد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    _off_all()
    print(f"\n{'✅' if not failed else '❌'} test_mirror_rooms_memory: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
