#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_reminders — موتورِ یادآوریِ NL (لِین E؛ منشور رأی‌های ۵–۸).

    parser ِ فارسیِ قطعی · store ِ اتمیک · شلیک در beat با ساعتِ تزریقی ·
    پنجرهٔ سکوتِ ۲۳–۷ (معوق، نه حذف؛ بحرانی رد می‌شود) · صفر ارسالِ مستقیم
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import harness

ENV = harness.setup("tg-reminders")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import reminders as rm  # noqa: E402


def _ts(*a) -> float:
    return datetime(*a).timestamp()


NOW = _ts(2026, 8, 5, 10, 0)          # ۲۰۲۶-۰۸-۰۵ = چهارشنبه، ۱۰:۰۰ صبح


def _fresh():
    for p in (rm._file(), rm._cfg_file()):
        try:
            p.unlink()
        except OSError:
            pass


# ── parser ─────────────────────────────────────────────────────────────────
def t_parse_when_understands_the_owner_language():
    """جدولِ ≥۱۵ حالت — رقمِ فارسی، روزِ هفته با wrap، لنگرِ صبح/شب."""
    assert datetime.fromtimestamp(NOW).weekday() == 2, "پیش‌فرضِ تقویمِ تست"
    cases = [
        ("فردا ساعت ۹ زنگ بزن", _ts(2026, 8, 6, 9, 0)),
        ("امروز ساعت 18 جلسه", _ts(2026, 8, 5, 18, 0)),
        ("پس‌فردا صبح دارو", _ts(2026, 8, 7, 8, 0)),
        ("۵ دقیقه دیگه چای دم کن", NOW + 300),
        ("۲ ساعت دیگه", NOW + 7200),
        ("۳ روز دیگه پیگیری کن", NOW + 3 * 86400),
        ("جمعه ساعت ۱۰ جلسه", _ts(2026, 8, 7, 10, 0)),
        ("چهارشنبه ساعت ۹", _ts(2026, 8, 12, 9, 0)),   # همان روز ⇒ هفتهٔ بعد
        ("شنبه", _ts(2026, 8, 8, 8, 0)),               # روزِ بی‌ساعت = ۰۸:۰۰
        ("یکشنبه ساعت ۷ عصر", _ts(2026, 8, 9, 19, 0)),
        ("ساعت ۹ شب قرص", _ts(2026, 8, 5, 21, 0)),
        ("ساعت ۸ صبح ورزش", _ts(2026, 8, 6, 8, 0)),    # گذشته ⇒ فردا
        ("ساعت ۱۱ صبح", _ts(2026, 8, 5, 11, 0)),
        ("شب قرص بخور", _ts(2026, 8, 5, 21, 0)),       # «شب» ِ تنها = ۲۱:۰۰
        ("صبح", _ts(2026, 8, 6, 8, 0)),                # ۰۸:۰۰ گذشته ⇒ فردا
        ("ساعت ۱۷:۳۰ تماس", _ts(2026, 8, 5, 17, 30)),
        ("ساعت ۱۲ ظهر ناهار", _ts(2026, 8, 5, 12, 0)),
    ]
    for text, want in cases:
        due, _cleaned = rm.parse_when(text, now=NOW)
        assert due is not None, text
        assert abs(due - want) < 1.0, (text, due, want)


def t_parse_when_no_match_returns_none_and_untouched_text():
    for text in ("این یک متنِ ساده است", "لید جدید از سایت آمد", "چطوری؟"):
        due, cleaned = rm.parse_when(text, now=NOW)
        assert due is None and cleaned == text, (text, due, cleaned)


def t_parse_when_strips_the_time_phrase_from_the_text():
    due, cleaned = rm.parse_when("فردا ساعت ۹ زنگ بزن به علی", now=NOW)
    assert due is not None and cleaned == "زنگ بزن به علی", cleaned
    _d, c2 = rm.parse_when("۵ دقیقه دیگه چای دم کن", now=NOW)
    assert c2 == "چای دم کن", c2


# ── store ──────────────────────────────────────────────────────────────────
def t_store_roundtrip_add_fire_done_snooze():
    _fresh()
    it = rm.add("قرصِ شب", due_ts=NOW + 60, now=NOW)
    assert it and it["id"] == "RM-1" and not it["fired"] and not it["done"]
    assert [x["id"] for x in rm.list_open(now=NOW)] == ["RM-1"]

    sent = []
    n = rm.beat(now=NOW + 120,
                send_dm_fn=lambda t, rid: sent.append((t, rid)),
                send_leg_fn=lambda leg, t: None)
    assert n == 1 and sent[0][1] == "RM-1" and "قرص" in sent[0][0], sent
    n2 = rm.beat(now=NOW + 180,
                 send_dm_fn=lambda t, rid: sent.append((t, rid)),
                 send_leg_fn=lambda leg, t: None)
    assert n2 == 0 and len(sent) == 1, "دبل-شلیک از یک یادآوری"

    s = rm.snooze("RM-1", 600, now=NOW + 200)
    assert s and not s["fired"] and s["due"] >= NOW + 799, s
    n3 = rm.beat(now=NOW + 900,
                 send_dm_fn=lambda t, rid: sent.append((t, rid)),
                 send_leg_fn=lambda leg, t: None)
    assert n3 == 1 and len(sent) == 2, "snooze دوباره شلیک نشد"

    d = rm.done("RM-1")
    assert d and d["done"] and rm.list_open() == []


def t_leg_scope_fires_into_the_leg_not_dm():
    """رأی ۶: شخصی در DM، بیزنسی در تاپیکِ همان پا."""
    _fresh()
    rm.add("پیگیری لید سیدنی", due_ts=NOW + 10, scope="leg", leg="lead",
           now=NOW)
    dm, lg = [], []
    rm.beat(now=NOW + 20, send_dm_fn=lambda t, rid: dm.append(t),
            send_leg_fn=lambda leg, t: lg.append((leg, t)))
    assert not dm and lg and lg[0][0] == "lead" and "لید" in lg[0][1], lg


def t_a_failed_send_does_not_mark_fired():
    _fresh()
    rm.add("مهم", due_ts=NOW + 5, now=NOW)

    def _boom(t, rid):
        raise RuntimeError("network")

    n = rm.beat(now=NOW + 10, send_dm_fn=_boom, send_leg_fn=lambda a, b: None)
    assert n == 0
    ok = []
    n2 = rm.beat(now=NOW + 20, send_dm_fn=lambda t, rid: ok.append(rid),
                 send_leg_fn=lambda a, b: None)
    assert n2 == 1 and ok, "ارسالِ ناموفق باید ضربانِ بعد جبران شود"


# ── پنجرهٔ سکوت (رأی ۸ — شروعِ محافظه‌کار ۲۳–۷) ────────────────────────────
def t_quiet_window_defers_normal_but_lets_critical_through():
    _fresh()
    late = _ts(2026, 8, 5, 23, 30)
    rm.add("یادِ معمولی", due_ts=late - 60, now=late - 3600)
    rm.add("بحرانی: سرور خوابید", due_ts=late - 60, now=late - 3600)
    sent = []
    n = rm.beat(now=late, send_dm_fn=lambda t, rid: sent.append(t),
                send_leg_fn=lambda leg, t: None)
    assert n == 1 and len(sent) == 1 and "بحرانی" in sent[0], sent

    deep = _ts(2026, 8, 6, 3, 0)              # وسطِ پنجره هم ساکت
    n_mid = rm.beat(now=deep, send_dm_fn=lambda t, rid: sent.append(t),
                    send_leg_fn=lambda leg, t: None)
    assert n_mid == 0 and len(sent) == 1, "معمولی وسطِ پنجره شلیک شد"

    morning = _ts(2026, 8, 6, 7, 0)           # پایانِ پنجره — معوقه می‌رسد
    n2 = rm.beat(now=morning, send_dm_fn=lambda t, rid: sent.append(t),
                 send_leg_fn=lambda leg, t: None)
    assert n2 == 1 and len(sent) == 2 and "معمولی" in sent[1], \
        "معوقِ شب سرِ ۰۷:۰۰ نرسید (حذف شده؟)"


# ── انضباط ─────────────────────────────────────────────────────────────────
def t_flag_is_default_off():
    os.environ.pop("OCTOPUS_TG_REMINDERS", None)
    assert not rm.enabled()


def t_keyboard_verbs_are_the_documented_contract():
    kb = rm.reminder_keyboard("RM-7")
    data = [b["callback_data"] for row in kb for b in row]
    assert "rm:done:RM-7" in data and "rm:snz:RM-7" in data, data
    assert all(len(x.encode()) <= 64 for x in data)


def t_the_module_has_no_external_effectors():
    import ast
    tree = ast.parse(Path(rm.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(rm._file()).lower().startswith(live), rm._file()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_reminders: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
