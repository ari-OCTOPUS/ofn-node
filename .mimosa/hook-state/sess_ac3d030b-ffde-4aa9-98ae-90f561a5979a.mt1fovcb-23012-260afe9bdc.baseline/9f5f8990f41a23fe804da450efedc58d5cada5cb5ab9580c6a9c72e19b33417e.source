"""test_c6_card_redelivery.py — کارتی که محاسبه شد ولی هرگز نرسید.

باگِ واقعی (۲۰۲۶-۰۷-۲۶، کشف با خواندنِ صفِ زنده): ردیفِ `seed-state-read-cache-bench`
با `status: DONE` و `verdict: accepted` و **`card_delivered: false`**. یعنی اختاپوس
یک آزمایشِ واقعی کرد، حکم داد، و نتیجه را به مالک نگفت — بدونِ هیچ خطا در هیچ لاگ.

علتش: مسیرِ تحویل (`_chan.rfc_card`) از قبل بود و در `c6_research_beat` صدا زده
می‌شد، ولی **پایین‌ترِ** `if h is None: return "no-pending-hypothesis"`. صف که خالی
شد، beat زودتر برمی‌گشت و آن ردیف تا ابد دفن ماند.

پس مهم‌ترین آزمونِ این فایل `t_redelivery_runs_with_an_empty_queue` است: بازفرست
باید **دقیقاً وقتی هیچ فرضیهٔ pending نیست** بدود. اگر آن سبز بماند و بقیه بشکنند
هم باز باگ برنگشته؛ برعکسش نه.

صفر شبکه: channel تزریقی. صفر لمسِ صفِ زنده: QUEUE به temp سوییچ می‌شود.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("c6-card-redelivery")

import c6_trigger as c6   # noqa: E402

FLAG = c6.REDELIVER_FLAG
_TMP = Path(tempfile.mkdtemp(prefix="c6-redeliver-"))
_LIVE_QUEUE = c6.QUEUE


class Chan:
    """channelِ تزریقی. `ok=False` یعنی تلگرام کارت را نپذیرفت."""

    def __init__(self, ok=True):
        self.ok = ok
        self.cards = []

    def rfc_card(self, rfc_id, summary):
        self.cards.append({"rfc_id": rfc_id, "summary": summary})
        return self.ok


def _seed(rows):
    q = _TMP / "hypothesis-queue.jsonl"
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                 encoding="utf-8")
    c6.QUEUE = q
    return q


def _rows(q):
    return [json.loads(l) for l in q.read_text("utf-8").splitlines() if l.strip()]


DONE_UNDELIVERED = {"id": "h-owed", "status": "DONE", "verdict": "accepted",
                    "card_delivered": False, "done_at": "2026-07-25T06:40:50Z",
                    "question": "does the cache do less work per tick?"}
DONE_DELIVERED = {"id": "h-sent", "status": "DONE", "verdict": "rejected",
                  "card_delivered": True, "done_at": "2026-07-24T00:00:00Z"}
STILL_PENDING = {"id": "h-pending", "status": "PENDING", "card_delivered": False}


def _flag(on):
    if on:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


# ─── تشخیصِ بدهی ────────────────────────────────────────────────────────────
def t_pending_cards_finds_only_the_real_debt():
    _seed([DONE_UNDELIVERED, DONE_DELIVERED, STILL_PENDING])
    ids = [r["id"] for r in c6.pending_cards()]
    assert ids == ["h-owed"], f"بدهیِ اشتباه تشخیص داده شد: {ids}"


def t_pending_cards_survives_a_corrupt_line():
    q = _seed([DONE_UNDELIVERED])
    q.write_text(q.read_text("utf-8") + "{ not json\n", encoding="utf-8")
    assert [r["id"] for r in c6.pending_cards()] == ["h-owed"]


# ─── بازفرست ────────────────────────────────────────────────────────────────
def t_flag_off_sends_nothing():
    _seed([DONE_UNDELIVERED]); _flag(False)
    ch = Chan()
    r = c6.redeliver_undelivered_cards(ch)
    assert r["ran"] is False and r["reason"] == "flag-off"
    assert ch.cards == [], "با فلگِ خاموش نباید هیچ کارتی برود"


def t_redelivers_then_marks_it_so_it_never_repeats():
    q = _seed([DONE_UNDELIVERED]); _flag(True)
    try:
        ch = Chan(ok=True)
        r = c6.redeliver_undelivered_cards(ch)
        assert r["sent"] == 1, r
        assert len(ch.cards) == 1
        row = [x for x in _rows(q) if x["id"] == "h-owed"][0]
        assert row["card_delivered"] is True
        assert row.get("card_delivered_at"), "زمانِ تحویل باید ثبت شود"
        # دورِ دوم: هیچ
        r2 = c6.redeliver_undelivered_cards(ch)
        assert r2["sent"] == 0 and len(ch.cards) == 1, "کارت دوباره رفت (idempotent نیست)"
    finally:
        _flag(False)


def t_a_refused_card_is_not_marked_so_it_retries():
    """اگر تلگرام کارت را نپذیرفت، نباید delivered علامت بخورد — وگرنه بدهی
    بی‌صدا پاک می‌شود و همان باگِ اصلی برمی‌گردد، این بار با ردِ جعلیِ موفقیت."""
    q = _seed([DONE_UNDELIVERED]); _flag(True)
    try:
        ch = Chan(ok=False)
        r = c6.redeliver_undelivered_cards(ch)
        assert r["sent"] == 0 and r["failed"] == 1
        row = [x for x in _rows(q) if x["id"] == "h-owed"][0]
        assert row["card_delivered"] is False, "شکستِ ارسال نباید delivered شود"
    finally:
        _flag(False)


def t_no_channel_is_counted_not_crashed():
    _seed([DONE_UNDELIVERED]); _flag(True)
    try:
        r = c6.redeliver_undelivered_cards(object())   # بدونِ rfc_card
        assert r["ran"] is False and r["reason"] == "no-channel" and r["pending"] == 1
    finally:
        _flag(False)


def t_cap_stops_a_backlog_storm():
    _seed([dict(DONE_UNDELIVERED, id=f"h{i}") for i in range(10)]); _flag(True)
    try:
        ch = Chan()
        r = c6.redeliver_undelivered_cards(ch, limit=3)
        assert r["pending"] == 10 and r["sent"] == 3, r
        assert len(ch.cards) == 3
    finally:
        _flag(False)


# ─── متنِ کارت ──────────────────────────────────────────────────────────────
def t_summary_states_the_real_date_and_never_pretends_to_be_fresh():
    s = c6._redeliver_summary(DONE_UNDELIVERED)
    assert "2026-07-25" in s, "تاریخِ واقعی باید در متن باشد"
    assert "accepted" in s
    assert "does the cache do less work per tick?" in s


# ─── گاردِ اصلی ─────────────────────────────────────────────────────────────
def t_redelivery_runs_with_an_empty_queue():
    """قلبِ این فایل. صفِ بدونِ فرضیهٔ PENDING دقیقاً حالتی است که کارت را دفن کرد.
    بازفرست باید همان‌جا بدود — نه بعد از early-return."""
    q = _seed([DONE_UNDELIVERED]); _flag(True)
    try:
        assert c6._pop_next_hypothesis() is None, \
            "پیش‌شرطِ آزمون: هیچ فرضیهٔ PENDING نباید باشد"
        ch = Chan()
        r = c6.redeliver_undelivered_cards(ch)
        assert r["sent"] == 1, "با صفِ خالی هم باید تحویل بدهد — همان باگِ اصلی"
    finally:
        _flag(False)


def t_rfc_id_always_fits_the_telegram_callback_cap():
    """علتِ واقعیِ گم‌شدنِ کارت (۲۰۲۶-۰۷-۲۶): `callback_data` تلگرام سقفِ ۶۴ بایت
    دارد و کارت `rfc:<verb>:<rfc_id>:<token24>` می‌سازد. شناسهٔ قدیمی ۷۵ بایت
    می‌شد (و مسیرِ اصلی با `contract_id[:60]` تا ۹۸)، تلگرام کلِ پیام را ۴۰۰
    می‌کرد و `send_text` استثنا را می‌بلعید → False بی‌صدا."""
    raws = ["seed-state-read-cache-bench", "x" * 200, "", "a",
            "contract-that-is-really-quite-long-indeed-0123456789"]
    for raw in raws:
        for pre in ("c6", "c6re"):
            rid = c6._short_rfc_id(pre, raw)
            assert len(rid.encode()) <= c6.RFC_ID_MAX, f"{rid} طولانی است"
            for verb in ("merge", "deny", "edit"):
                cb = f"rfc:{verb}:{rid}:{'x' * 24}"
                assert len(cb.encode()) <= 64, \
                    f"callback {len(cb.encode())}B برای {raw[:20]!r} — تلگرام رد می‌کند"


def t_short_rfc_id_is_stable_so_the_anti_duplicate_guard_works():
    """اگر شناسه هر بار عوض شود، گاردِ ضدِ کارتِ تکراریِ `rfc_card` بی‌اثر می‌شود
    و بازفرست می‌تواند رأیِ ثبت‌نشدهٔ مالک را با nonceِ نو بسوزاند."""
    assert c6._short_rfc_id("c6re", "abc") == c6._short_rfc_id("c6re", "abc")
    assert c6._short_rfc_id("c6re", "abc") != c6._short_rfc_id("c6re", "abd")


def t_live_queue_was_never_touched():
    """گاردِ ایزولاسیون: این فایل هرگز نباید صفِ زندهٔ ارگانیسم را بنویسد."""
    assert c6.QUEUE != _LIVE_QUEUE, "QUEUE به temp سوییچ نشده"
    assert str(_TMP) in str(c6.QUEUE)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_c6_card_redelivery: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
