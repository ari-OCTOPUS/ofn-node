"""test_tg_instant_and_sendlog.py — مرحلهٔ ۳ و ۴ (رأیِ مالک ۲۰۲۶-۰۷-۲۶).

مرحلهٔ ۳ — `instant_alert_bridge`: چیزی که تا دایجستِ ۶ساعته نباید صبر کند.
مرحلهٔ ۴ — `tg_send_log`: **اول بشمار، بعد ضدِاسپم بساز.** سه گزارشِ پیاپی
«اسپم» را علتِ اصلی خواندند و هیچ‌کدام حجمِ واقعی را نشمرده بود؛ یکی digestِ
۲۴ساعته را اسپم نامید و یکی lockِ نبضِ زنده را ردِ نمونهٔ تکراری خواند. پس این
لایه فقط اندازه می‌گیرد و تصمیمِ dedup را به عدد واگذار می‌کند.

قیدهای سختِ این فایل:
  · لاگ **هرگز متنِ پیام را ذخیره نمی‌کند** — فقط hash. وگرنه به کپیِ دومِ
    محتوای مالک تبدیل می‌شود.
  · شکستِ لاگ هرگز نباید نتیجهٔ ارسال را عوض کند.
  · پل هرگز نباید یک سیگنالِ خراب را به کشتنِ tick تبدیل کند.
  · فلگِ خاموش = صفر اثر، بایت‌به‌بایت.
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-instant-sendlog")

import opslib                     # noqa: E402
import instant_alert_bridge as ib  # noqa: E402
import tg_send_log as tsl          # noqa: E402


def _flag(name, on):
    if on:
        os.environ[name] = "1"
    else:
        os.environ.pop(name, None)


def _state(rel, obj):
    p = Path(opslib.STATE_DIR) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str)
                 else obj, encoding="utf-8")
    return p


def _reset_throttle(*names):
    """stateِ throttle را پاک کن تا هر تست خودبسنده باشد.

    اولین بار که این را ننوشتم، تستِ الفباییِ اول hash را mark می‌کرد و بقیه
    `held` می‌شدند — یعنی تست‌ها به ترتیبِ اجرا وابسته بودند. خودِ throttle درست
    کار می‌کرد؛ تست‌ها بودند که به هم نشت داشتند."""
    for n in (names or ("fear", "c6_new", "card_debt")):
        p = Path(opslib.STATE_DIR) / f"instant-{n}.json"
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


class Chan:
    def __init__(self, ok=True):
        self.ok = ok
        self.sent = []

    def send_text(self, text, reply_markup=None, chat_id=None, stream=None):
        self.sent.append({"text": text, "stream": stream, "chat_id": chat_id})
        return self.ok


# ══ مرحلهٔ ۴ — سنجش ═══════════════════════════════════════════════════════
def t_sendlog_off_by_default_writes_nothing():
    _flag(tsl.FLAG, False)
    p = tsl._path()
    if p.exists():
        p.unlink()
    assert tsl.record(chat_id=1, text="سلام") is False
    assert not p.exists(), "با فلگِ خاموش نباید فایلی ساخته شود"


def t_sendlog_never_stores_the_message_text():
    """قیدِ حریمِ خصوصی: لاگ نباید کپیِ دومِ محتوای مالک شود."""
    _flag(tsl.FLAG, True)
    try:
        p = tsl._path()
        if p.exists():
            p.unlink()
        secret = "مبلغِ فاکتور ۱۵۰۰۰ دلار برای مشتری"
        assert tsl.record(chat_id=7, topic_id=28, text=secret, stream="heart")
        raw = p.read_text("utf-8")
        assert secret not in raw, "متنِ پیام در لاگ نشت کرد"
        row = json.loads(raw.splitlines()[0])
        assert row["sha"] == tsl.digest(secret)
        assert row["chars"] == len(secret) and row["topic"] == 28
    finally:
        _flag(tsl.FLAG, False)


def t_stats_counts_duplicates_per_destination():
    """تکرار = همان محتوا به همان مقصد. مقصدِ متفاوت تکرار نیست."""
    _flag(tsl.FLAG, True)
    try:
        p = tsl._path()
        if p.exists():
            p.unlink()
        for _ in range(3):
            tsl.record(chat_id=1, topic_id=28, text="یکسان", stream="heart")
        tsl.record(chat_id=1, topic_id=29, text="یکسان", stream="brain")   # مقصدِ دیگر
        tsl.record(chat_id=1, topic_id=28, text="متفاوت", stream="heart")
        s = tsl.stats(window_h=24)
        assert s["sends"] == 5, s
        assert s["duplicates"] == 2, f"تکرار باید ۲ باشد (۳ پیامِ یکسان): {s}"
        assert s["by_stream"]["heart"] == 4
    finally:
        _flag(tsl.FLAG, False)


def t_stats_window_excludes_old_rows():
    _flag(tsl.FLAG, True)
    try:
        p = tsl._path()
        p.parent.mkdir(parents=True, exist_ok=True)
        old = {"ts": time.time() - 90000, "chat": 1, "topic": None,
               "stream": "x", "sha": "a" * 16, "chars": 3, "ok": True}
        p.write_text(json.dumps(old) + "\n", encoding="utf-8")
        tsl.record(chat_id=1, text="تازه")
        assert tsl.stats(window_h=1)["sends"] == 1, "ردیفِ کهنه در پنجره شمرده شد"
        assert tsl.stats(window_h=48)["sends"] == 2
    finally:
        _flag(tsl.FLAG, False)


def t_sendlog_failure_never_changes_the_send_result():
    """اگر دیسک بترکد، ارسال باید همان نتیجهٔ قبل را بدهد."""
    _flag(tsl.FLAG, True)
    orig = tsl._path
    tsl._path = lambda: Path("Z:/no/such/place/tg-send-log.jsonl")
    try:
        assert tsl.record(chat_id=1, text="x") is False, "باید بی‌سروصدا False بدهد"
    finally:
        tsl._path = orig
        _flag(tsl.FLAG, False)


def t_prune_drops_only_what_is_past_the_window():
    _flag(tsl.FLAG, True)
    try:
        p = tsl._path()
        p.parent.mkdir(parents=True, exist_ok=True)
        rows = [{"ts": time.time() - 200000, "sha": "old"},
                {"ts": time.time(), "sha": "new"}]
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        assert tsl.prune() == 1
        assert "old" not in p.read_text("utf-8")
        assert "new" in p.read_text("utf-8")
    finally:
        _flag(tsl.FLAG, False)


# ══ مرحلهٔ ۳ — پلِ فوری ═══════════════════════════════════════════════════
def t_bridge_off_by_default():
    _flag(ib.FLAG, False)
    ch = Chan()
    assert ib.check(ch) == {"ran": False, "reason": "flag-off"}
    assert ch.sent == []


def t_bridge_needs_a_channel_and_says_so():
    _flag(ib.FLAG, True)
    try:
        assert ib.check(None)["reason"] == "no-channel"
        assert ib.check(object())["reason"] == "no-channel"
    finally:
        _flag(ib.FLAG, False)


def t_fear_signal_fires_only_on_red():
    _state("cortex/cortisol-state.json", {"level": "🟡 استرس", "in_fear": []})
    _state("cortex/stress-latest.json", {"level": "🟢 آرام", "in_fear": []})
    assert ib._sig_fear() is None, "زرد نباید هشدارِ فوری بدهد"
    _state("cortex/cortisol-state.json", {"level": "🔴 ترس", "in_fear": ["legs"]})
    out = ib._sig_fear()
    assert out is not None
    body, stream, _h = out
    assert stream == "cortisol"
    assert "legs" in body and "🔴" in body
    assert "نکنی" in body, "کارت باید بگوید اگر کاری نکنی چه می‌شود"


def t_fear_hash_changes_with_the_subsystem_so_a_new_fear_is_not_throttled():
    _state("cortex/cortisol-state.json", {"level": "🔴 ترس", "in_fear": ["legs"]})
    h1 = ib._sig_fear()[2]
    _state("cortex/cortisol-state.json", {"level": "🔴 ترس", "in_fear": ["heart"]})
    h2 = ib._sig_fear()[2]
    assert h1 != h2, "ترسِ یک زیرسیستمِ تازه نباید پشتِ throttleِ قبلی گم شود"


def t_c6_signal_reports_only_pending_rows():
    q = Path(opslib.STATE_DIR) / "c6" / "hypothesis-queue.jsonl"
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text(json.dumps({"id": "d", "status": "DONE"}) + "\n", encoding="utf-8")
    assert ib._sig_c6_new() is None, "ردیفِ DONE فرضیهٔ تازه نیست"
    q.write_text("\n".join([
        json.dumps({"id": "d", "status": "DONE"}),
        json.dumps({"id": "p", "status": "PENDING", "probe": "cmd_lone_lf",
                    "question": "آیا فایلی LF شده؟", "baseline_count": 12,
                    "unit": "file", "floor": 0}),
    ]) + "\n", encoding="utf-8")
    body, stream, _h = ib._sig_c6_new()
    assert stream == "c6" and "cmd_lone_lf" in body and "12" in body


def t_bridge_routes_each_signal_to_its_own_topic():
    _state("cortex/cortisol-state.json", {"level": "🔴 ترس", "in_fear": ["legs"]})
    _reset_throttle()
    _flag(ib.FLAG, True)
    try:
        ch = Chan()
        r = ib.check(ch, min_interval_s=0.0)
        assert "fear" in r["sent"], r
        assert ch.sent and ch.sent[0]["stream"] == "cortisol"
    finally:
        _flag(ib.FLAG, False)


def t_a_broken_signal_is_counted_not_fatal():
    """یک سیگنالِ خراب هرگز نباید tick را بکشد یا بقیه را ساکت کند."""
    _state("cortex/cortisol-state.json", {"level": "🔴 ترس", "in_fear": ["legs"]})
    _reset_throttle()
    _flag(ib.FLAG, True)
    orig = dict(ib.SIGNALS)

    def boom():
        raise RuntimeError("سیگنالِ خراب")
    ib.SIGNALS["boom"] = boom
    try:
        ch = Chan()
        r = ib.check(ch, min_interval_s=0.0)
        assert "boom" in r["failed"], r
        assert "fear" in r["sent"], "سیگنالِ سالم باید همچنان برود"
    finally:
        ib.SIGNALS.clear()
        ib.SIGNALS.update(orig)
        _flag(ib.FLAG, False)


def t_a_refused_send_is_not_marked_so_it_retries():
    _state("cortex/cortisol-state.json", {"level": "🔴 ترس", "in_fear": ["legs"]})
    _reset_throttle()
    _flag(ib.FLAG, True)
    try:
        ch = Chan(ok=False)
        r = ib.check(ch, min_interval_s=0.0)
        assert "fear" in r["failed"] and "fear" not in r["sent"], r
        # چون mark نشده، دورِ بعد دوباره تلاش می‌کند
        ch2 = Chan(ok=True)
        r2 = ib.check(ch2, min_interval_s=0.0)
        assert "fear" in r2["sent"], "ارسالِ ناموفق نباید throttle را بسوزاند"
    finally:
        _flag(ib.FLAG, False)


def t_every_signal_stream_has_a_topic_route():
    """گاردِ ضدِ typo: هر streamِ پل یا در جدولِ پاهاست یا صریحاً هسته‌ای.

    ⚠️ ۰۷-۳۱ — قراردادِ مسیریابی عوض شد (VQ-TG-HOLD-001 §۵): مدخل‌های هسته‌ای
    عمداً از `_STREAM_TOPIC` حذف شدند و «نبودِ مدخل ⇒ DM ِ مالک، نه سکوت».
    پس غیاب دیگر typo نیست — ولی گارد بی‌دندان هم نمی‌شود: هر stream باید یا
    در جدولِ پاها باشد یا در فهرستِ صریحِ هسته‌ای (DM) این‌جا. streamِ نویی که
    در هیچ‌کدام نیست همچنان قرمز می‌شود."""
    import approval_channel as ac
    core_dm = {"c6", "fear", "hypothesis", "heart", "doctor", "needs", "brain",
               "cortisol"}
    seen = set()
    for name, fn in ib.SIGNALS.items():
        try:
            out = fn()
        except Exception:  # noqa: BLE001
            continue
        if out:
            seen.add(out[1])
    for s in seen:
        assert s in ac._STREAM_TOPIC or s in core_dm, \
            f"streamِ {s!r} نه در جدولِ پاهاست نه هسته‌ایِ اعلام‌شده"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_instant_and_sendlog: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
