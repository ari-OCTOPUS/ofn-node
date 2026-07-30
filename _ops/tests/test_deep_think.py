"""test_deep_think.py — تستِ متخاصم علیهِ اندامِ «فکرِ عمیق».

قصد: **گول‌زدنِ خودِ تغییر**. این ماژول یک مغزِ گران را صدا می‌زند و یک مسیرِ
حساس (لولهٔ لید) را می‌خوانَد؛ پس سه چیز باید ساختاراً غیرممکن باشد نه قراردادی:
  ۱) با flag خاموش هیچ اثری روی دیسک نگذارد،
  ۲) هرگز محتوای یک فایلِ لید را نبیند (فقط بشمارد)،
  ۳) یک شکستِ گران هر تیک تکرار نشود.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("deep-think")

import deep_think as dt          # noqa: E402 — بعد از harness تا مسیرها ایزوله باشند
import opslib                    # noqa: E402

FLAG = dt.FLAG
CANARY = "کاناریِ-محرمانه-نباید-دیده-شود-9f3a"


def _on(v=True):
    if v:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


def _reset_slots():
    try:
        dt.SLOT_STATE.unlink()
    except OSError:
        pass
    # پشتیبانِ درون-پروسه‌ایِ ۰۷-۲۷ هم باید پاک شود، وگرنه اولین تست بازه را در
    # حافظه می‌سوزاند و بقیه «slot-done» می‌گیرند — همان تلهٔ ایزولاسیونِ ناقص.
    dt._MEMO["date"], dt._MEMO["done"] = "", set()


class Chan:
    def __init__(self, ok=True, boom=False):
        self.cards, self.ok, self.boom = [], ok, boom

    def rfc_card(self, rfc_id, summary):
        if self.boom:
            raise RuntimeError("کانال ترکید")
        self.cards.append({"rfc_id": rfc_id, "summary": summary})
        return self.ok


def _fake_router(text="x" * 400, ok=True, boom=False, got_tier="primary",
                 fallback_from=None):
    """model_router جعلی — تزریق از راهِ sys.modules چون deep_think آن را lazy وارد می‌کند.

    `got_tier`/`fallback_from` شکلِ **واقعیِ** روتر را بازمی‌سازند: وقتی ردهٔ پولی
    می‌افتد، روتر جواب می‌دهد ولی با tierِ محلی و کلیدِ `fallback_from`."""
    import types
    m = types.ModuleType("model_router")
    calls = []

    def ask(task, prompt, system="", max_tokens=400, tier=None, **kw):
        calls.append({"task": task, "prompt": prompt, "system": system,
                      "max_tokens": max_tokens, "tier": tier})
        if boom:
            raise RuntimeError("مغز در دسترس نیست")
        out = {"ok": ok, "text": text, "model": "fugu", "cost_usd": 0.0,
               "tier": got_tier}
        if fallback_from:
            out["fallback_from"] = fallback_from
        return out

    m.ask = ask
    m._calls = calls
    sys.modules["model_router"] = m
    return m


# ─── حملهٔ ۱ (مهم‌ترین): flag خاموش باید صفر I/O باشد ────────────────────────
def t_flag_off_writes_absolutely_nothing():
    _on(False)
    _reset_slots()
    before = sorted(p.name for p in dt.LEDGER.parent.iterdir()) if dt.LEDGER.parent.exists() else []
    m = _fake_router()
    r = dt.run(channel=Chan())
    assert r == {"ran": False, "reason": "flag-off"}, r
    assert not m._calls, "با flag خاموش مغز صدا زده شد"
    after = sorted(p.name for p in dt.LEDGER.parent.iterdir()) if dt.LEDGER.parent.exists() else []
    assert before == after, f"flag خاموش ولی دیسک تغییر کرد: {before} → {after}"


# ─── حملهٔ ۲: مرزِ PII — هرگز فایلِ لید باز نشود ─────────────────────────────
def t_business_context_counts_files_but_never_opens_them():
    """کاناری داخلِ یک فایلِ لید می‌کارم. اگر در context ظاهر شد، مرز شکسته."""
    inbox = opslib.STATE_DIR / "legs" / "lead-inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "lead-001.json").write_text(
        json.dumps({"name": CANARY, "email": f"{CANARY}@x.com"}, ensure_ascii=False), "utf-8")
    (inbox / "lead-002.json").write_text("{}", "utf-8")

    ctx = dt._business_context()
    blob = json.dumps(ctx, ensure_ascii=False)
    assert CANARY not in blob, "محتوای فایلِ لید به context نشت کرد"
    assert ctx["لیدهای_ورودی"] == 2, f"شمارش غلط: {ctx}"

    # همان چک روی promptِ کامل (مسیرِ واقعی‌ای که به مغز می‌رود)
    p = dt.build_prompt(dt.TOPIC_BUSINESS)
    assert CANARY not in p, "کاناری از راهِ prompt به مغز رفت"


def t_business_context_survives_a_missing_directory():
    import shutil
    legs = opslib.STATE_DIR / "legs"
    bak = legs.with_name("legs.bak")
    if legs.exists():
        shutil.move(str(legs), str(bak))
    try:
        ctx = dt._business_context()
        assert ctx["لیدهای_ورودی"] == 0 and ctx["فاکتورها"] == 0, ctx
    finally:
        if bak.exists():
            if legs.exists():
                shutil.rmtree(legs)
            shutil.move(str(bak), str(legs))


# ─── حملهٔ ۳: یک شکستِ گران نباید هر تیک تکرار شود ───────────────────────────
def t_an_exploding_brain_still_burns_the_slot():
    """اگر بازه فقط بعد از موفقیت علامت بخورد، یک مغزِ خرابْ هر تیک یک فراخوانِ
    ۳۰ ثانیه‌ای می‌سوزاند تا آخرِ روز."""
    _on(True)
    _reset_slots()
    _fake_router(boom=True)
    slot = dt.current_slot()
    r = dt.run(channel=Chan())
    assert r["reason"] == "ask-exception", r
    assert dt.slot_done(slot), "بازه بعد از شکست علامت نخورد — تکرارِ بی‌پایان"
    m2 = _fake_router()
    r2 = dt.run(channel=Chan())
    assert r2["reason"] == "slot-done", r2
    assert not m2._calls, "بازهٔ مصرف‌شده دوباره مغز را صدا زد"
    _on(False)


def t_same_slot_never_runs_twice():
    _on(True)
    _reset_slots()
    m = _fake_router()
    c = Chan()
    a = dt.run(channel=c)
    b = dt.run(channel=c)
    assert a["ran"] and not b["ran"], (a, b)
    assert len(m._calls) == 1, f"{len(m._calls)} فراخوان در یک بازه"
    assert len(c.cards) == 1
    _on(False)


def t_a_new_day_reopens_the_slots():
    _on(True)
    _reset_slots()
    _fake_router()
    slot = dt.current_slot()
    dt.mark_slot(slot, today="2026-01-01")
    assert not dt.slot_done(slot), "بازهٔ دیروز امروز را هم بسته نگه داشت"
    _on(False)


# ─── حملهٔ ۴: جوابِ بی‌ارزش نباید کارت بسازد ─────────────────────────────────
def t_short_or_empty_answer_produces_no_card():
    for text in ("", "باشه.", "x" * (dt.MIN_ANSWER_CHARS - 1)):
        _on(True)
        _reset_slots()
        _fake_router(text=text)
        c = Chan()
        r = dt.run(channel=c)
        assert r["ran"] and not r.get("delivered"), (text[:20], r)
        assert not c.cards, f"کارت برای جوابِ {len(text)} کاراکتری ساخته شد"
    _on(False)


def t_not_ok_response_produces_no_card():
    _on(True)
    _reset_slots()
    _fake_router(text="y" * 500, ok=False)
    c = Chan()
    r = dt.run(channel=c)
    assert not r.get("delivered") and not c.cards, r
    _on(False)


def t_an_exploding_channel_does_not_kill_the_session():
    _on(True)
    _reset_slots()
    _fake_router()
    r = dt.run(channel=Chan(boom=True))
    assert r["ran"] and not r["delivered"], r
    _on(False)


# ─── حملهٔ ۵: زمان‌بندی — بدونِ شکاف، بدونِ خارج‌از‌کران ─────────────────────
def t_every_hour_of_the_day_maps_to_a_valid_slot():
    import datetime
    for n in (1, 2, 3, 4, 6, 12):
        os.environ["DEEP_THINK_SLOTS"] = str(n)
        seen = set()
        for h in range(24):
            s = dt.current_slot(datetime.datetime(2026, 7, 27, h, 30))
            assert 0 <= s < n, f"slots={n} ساعت={h} → {s} خارج از کران"
            seen.add(s)
        assert seen == set(range(n)), f"slots={n}: بازه‌های بی‌استفاده {set(range(n))-seen}"
    os.environ.pop("DEEP_THINK_SLOTS", None)


def t_slot_count_is_clamped_against_a_hostile_env():
    for bad in ("0", "-5", "999", "abc", "", "1e9", "4.7"):
        os.environ["DEEP_THINK_SLOTS"] = bad
        n = dt.slots_per_day()
        assert 0 < n <= dt.MAX_SLOTS, f"DEEP_THINK_SLOTS={bad!r} → {n}"
    os.environ.pop("DEEP_THINK_SLOTS", None)


def t_topics_rotate_over_both_owner_goals():
    os.environ["DEEP_THINK_SLOTS"] = "4"
    topics = {dt.topic_for(s) for s in range(4)}
    assert topics == {dt.TOPIC_SELF, dt.TOPIC_BUSINESS}, topics
    assert dt.topic_for(0) == dt.topic_for(2), "چرخش قطعی نیست"
    os.environ.pop("DEEP_THINK_SLOTS", None)


# ─── حملهٔ ۶: قراردادِ فراخوان (درسِ ۰۷-۲۶: سقفِ ۶۴ بایتِ callback) ──────────
def t_the_card_id_fits_the_64_byte_callback_budget():
    """`rfc:<verb>:<rfc_id>:<token>` — رد شدن از ۶۴ بایت یعنی تلگرام کلِ پیام را
    ۴۰۰ می‌کند و کارت بی‌هیچ ردی گم می‌شود (کارتِ C6 یک شبانه‌روز همین‌طور رفت)."""
    _on(True)
    _reset_slots()
    _fake_router()
    c = Chan()
    dt.run(channel=c)
    assert c.cards, "کارتی ساخته نشد"
    rid = c.cards[0]["rfc_id"]
    worst = len(f"rfc:approve:{rid}:".encode()) + 24     # ۲۴ = فضایِ توکن
    assert worst <= 64, f"callback {worst} بایت با rfc_id={rid!r}"
    _on(False)


def t_the_brain_is_asked_on_the_expensive_tier_with_room_to_answer():
    """اگر tier به primary پین نشود، CORTEX_LOCAL_FIRST جواب را به مغزِ رایگان
    می‌بَرَد و کلِ هدفِ این اندام (استفاده از مغزِ گران) بی‌صدا از بین می‌رود."""
    _on(True)
    _reset_slots()
    m = _fake_router()
    dt.run(channel=Chan())
    call = m._calls[0]
    assert call["tier"] == "primary", f"tier={call['tier']!r} — به مغزِ گران نمی‌رود"
    assert call["max_tokens"] >= 800, f"max_tokens={call['max_tokens']} برای جوابِ واقعی کم است"
    assert call["system"], "بدونِ system prompt، جوابِ کلی و بی‌ارزش می‌آید"
    _on(False)


def t_a_silent_downgrade_to_the_free_brain_produces_no_card():
    """ممیزیِ متخاصمِ ۲۰۲۶-۰۷-۲۷: `tier="primary"` فقط **درخواست** را پین می‌کند. اگر
    Fugu بیفتد (بریکر باز/کلید غایب/تایم‌اوت)، روتر بی‌صدا به مدلِ محلیِ ۱.۵B می‌افتد
    و فقط `fallback_from` می‌گذارد — که کسی نمی‌خواندش. آن‌وقت این اندام یک جلسهٔ
    «عمیق» را با مغزِ رایگان پر می‌کرد و کارتش را با اطمینان تحویل می‌داد."""
    for kw in ({"got_tier": "local", "fallback_from": "primary: paid-call-failed"},
               {"got_tier": "local"},
               {"got_tier": "secondary"}):
        _on(True)
        _reset_slots()
        _fake_router(text="y" * 900, **kw)
        c = Chan()
        r = dt.run(channel=c)
        assert not r.get("delivered"), (kw, r)
        assert not c.cards, f"کارت با مغزِ غیرِ گران ساخته شد: {kw}"
        assert r.get("reason") == "not-the-expensive-brain", (kw, r)
    _on(False)


def t_the_prompt_actually_carries_numbers_not_just_a_question():
    """درسِ governor: ۱۲٬۲۴۲ توکن برای جوابِ ۵۰ کاراکتری. سؤالِ بدونِ داده = حرفِ کلی."""
    p = dt.build_prompt(dt.TOPIC_SELF)
    assert any(ch.isdigit() for ch in p), "promptِ «خودت» هیچ عددی ندارد"
    assert len(p) > 120, f"prompt فقط {len(p)} کاراکتر — context خالی است"


def t_context_never_leaks_a_secret_shaped_string():
    """گاردِ نشتِ secret: هیچ‌کدام از دو context نباید چیزی شبیه کلید/توکن بدهد."""
    import re
    pat = re.compile(r"(sk-|bot\d{6,}:|ghp_|AKIA|-----BEGIN)", re.I)
    for topic in (dt.TOPIC_SELF, dt.TOPIC_BUSINESS):
        p = dt.build_prompt(topic)
        assert not pat.search(p), f"الگویِ شبیهِ secret در promptِ {topic}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_deep_think: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
