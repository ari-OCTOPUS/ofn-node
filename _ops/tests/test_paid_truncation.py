#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_paid_truncation — پاسخِ بریدهٔ مغزِ پولی نباید «موفقیت» شمرده شود.

شاهدِ زنده‌ای که این گارد را لازم کرد (`_ops/state/paid-calls.jsonl`):

    2026-07-29T17:33:08  tier=primary provider=sakana model=fugu ok=True
    tokens_in=606  tokens_out=500  chars_out=3  cost_usd=0.0  ms=14686

`tokens_out=500` **دقیقاً** سقفِ آن‌روزِ `SYNTHESIS_MAX_TOKENS` بود. Fugu مدلِ
استدلالی است و توکن‌های تفکرش از همان بودجه می‌خورند، پس کلِ ۵۰۰ صرفِ استدلال شد و
سه کاراکترِ مرئی («زنج») بیرون آمد. سه لایه هم‌زمان کور بودند:

  ۱) `client` مقدارِ `finish_reason` را از provider می‌خواند، ولی sakana هرگز
     پرش نمی‌کند — در هر ۲۰۶ تماسِ موفق `None` بود. پس گاردی که ۰۷-۲۷ برای دیدنِ
     «length» ساخته شده بود **هرگز شلیک نکرد**؛ میدان لوله‌کشی شده بود و همیشه خالی.
  ۲) `model_router._ask_paid` بی‌قید dict برمی‌گرداند و صداکننده `if out:` می‌کند —
     dict ِ ناخالی همیشه truthy است، پس استابِ ۳-کاراکتری `ok=True` می‌گرفت.
  ۳) `synthesis` صفرِ پیشنهاد را بی‌آلارم ذخیره می‌کرد. حلقه از بیرون سالم به‌نظر
     می‌آمد و `cost_usd=0.0` هم لو نمی‌داد، چون با `subscription: max` هزینه
     ساختاراً صفر است.

اثباتِ زندهٔ فیکس (همان مسیر، بعد از بالا بردنِ سقف): `tokens_out=826
chars_out=872` → سه پیشنهادِ سالم.
"""
import sys

import harness

ENV = harness.setup("paid-truncation")   # env قبل از import — ترتیب مهم است

# harness مسیرهای _ops/budget و _ops/debate را می‌گذارد ولی cortex را نه.
from pathlib import Path                # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cortex"))

import client as C           # noqa: E402
import model_router as MR    # noqa: E402
import synthesis as S        # noqa: E402


# ── لایهٔ ۱: استنتاجِ محلیِ بریدگی ──────────────────────────────────────────
def t_provider_verdict_always_wins():
    """رأیِ صریحِ provider هرگز بازنویسی نمی‌شود — حتی روی سقف."""
    assert C._infer_finish("stop", 500, 500) == "stop"
    assert C._infer_finish("content_filter", 900, 500) == "content_filter"


def t_a_silent_provider_at_the_ceiling_means_length():
    """قلبِ فیکس: sakana میدان را خالی می‌گذارد، پس از شمارِ توکن استنتاج می‌شود."""
    assert C._infer_finish(None, 500, 500) == "length"
    assert C._infer_finish(None, 512, 500) == "length", "عبور از سقف هم بریدگی است"


def t_a_healthy_short_answer_is_not_truncation():
    """تلهٔ کاذب: پاسخِ کوتاهِ سالم نباید بریده شمرده شود.

    ردیفِ واقعیِ بی‌گناه: `tokens_out=18` با سقفِ ۷۰۰ و `chars_out=4` — جوابِ
    درستِ کوتاه به یک سؤالِ کوچک. اگر این را رد کنیم، مسیرِ پولی را روی
    پاسخ‌های سالم می‌شکنیم."""
    assert C._infer_finish(None, 18, 700) is None
    assert C._infer_finish(None, 499, 500) is None


def t_unknown_or_broken_counts_never_invent_truncation():
    assert C._infer_finish(None, 0, 0) is None
    assert C._infer_finish(None, "x", None) is None
    assert C._infer_finish(None, None, 500) is None


def t_the_client_reproduces_the_live_row_as_length():
    """بازتولیدِ بایت‌به‌بایتِ شکلِ ردیفِ زنده، بدونِ شبکه."""
    def _t(_payload):
        return {"choices": [{"message": {"content": "زنج"}}],   # finish_reason غایب
                "usage": {"prompt_tokens": 606, "completion_tokens": 500}}
    out = C.MultiProviderClient(role="orchestr", transport=_t) \
        .complete("سیستم", "پرامپت", max_tokens=500)
    assert out["text"] == "زنج"
    assert out["tokens_out"] == 500
    assert out["finish_reason"] == "length", \
        "همان کوریِ ۲۰۶/۲۰۶ برگشت — بریدگی از درِ مغز صدا درنمی‌آورد"


def t_the_same_reply_under_a_bigger_ceiling_is_not_truncated():
    """اثباتِ اینکه سنجه **سقف** است نه طولِ متن."""
    def _t(_payload):
        return {"choices": [{"message": {"content": "زنج"}}],
                "usage": {"prompt_tokens": 606, "completion_tokens": 500}}
    out = C.MultiProviderClient(role="orchestr", transport=_t) \
        .complete("س", "پ", max_tokens=2000)
    assert out["finish_reason"] is None


# ── لایهٔ ۲: روتر — استابِ بی‌مصرف = شکست ───────────────────────────────────
def t_a_truncated_stub_is_refused():
    assert MR.is_useless_truncation("زنج", "length") is True
    assert MR.is_useless_truncation("", "length") is True


def t_a_long_truncated_answer_still_passes():
    """ناقص ولی مفید — قضاوتش کارِ صاحبِ فراخوان است، نه روتر."""
    assert MR.is_useless_truncation("ی" * 500, "length") is False


def t_a_short_but_complete_answer_still_passes():
    """مهم‌ترین تلهٔ کاذب: «بله» جوابِ معتبری است."""
    assert MR.is_useless_truncation("بله", None) is False
    assert MR.is_useless_truncation("بله", "stop") is False


def t_the_threshold_is_a_knob():
    import os
    os.environ["PAID_MIN_USEFUL_CHARS"] = "5"
    try:
        # «زنج» (۳ کاراکتر) زیرِ ۵ است → بازهم رد
        assert MR.is_useless_truncation("زنج", "length") is True
        # ۱۰ کاراکتر بالای آستانهٔ ۵ است → حالا عبور می‌کند
        assert MR.is_useless_truncation("ا" * 10, "length") is False
    finally:
        os.environ.pop("PAID_MIN_USEFUL_CHARS", None)


def t_ask_paid_actually_consults_the_predicate():
    """گاردِ ساختاری، ولی روی **صداکننده** نه روی وجودِ رشته: اگر روزی کسی
    شرط را از `_ask_paid` بردارد، همین‌جا قرمز می‌شود."""
    import inspect
    src = inspect.getsource(MR._ask_paid)
    assert "is_useless_truncation" in src, \
        "_ask_paid دیگر predicate را صدا نمی‌زند — استابِ بریده باز ok=True می‌گیرد"
    assert "return None" in src


# ── لایهٔ ۳: سنتز — سقفِ کافی و صفرِ باصدا ──────────────────────────────────
def t_the_synthesis_ceiling_leaves_room_for_reasoning():
    """سقفِ ۵۰۰ برای مدلِ استدلالی کافی نبود — شاهدِ زنده: ۸۲۶ توکن لازم داشت."""
    assert S.MAX_TOKENS >= 1000, (
        f"سقفِ سنتز {S.MAX_TOKENS} است؛ مدلِ استدلالی در شاهدِ زنده ۸۲۶ توکن "
        "مصرف کرد و با سقفِ ۵۰۰ فقط ۳ کاراکتر بیرون داد")


def t_zero_proposals_from_a_successful_call_raises_an_alert():
    """لایه‌ای که سکوت می‌کرد. شاهد باید **هم** ذخیره شود **هم** صدا بدهد."""
    alerts = []
    _orig = S.opslib.alert
    S.opslib.alert = lambda items: alerts.append(items)
    try:
        r = S.synthesize(ask=lambda *a, **k: {
            "ok": True, "text": "زنج", "tier": "primary", "model": "fugu",
            "finish_reason": "length", "cost_usd": 0.0})
    finally:
        S.opslib.alert = _orig
    assert r["ok"] is True and r["digest"]["proposals"] == []
    assert len(alerts) == 1, f"صفرِ پیشنهاد بی‌صدا ماند ({len(alerts)} آلارم)"
    body = alerts[0][0]
    assert "length" in body and "max_tokens" in body, \
        f"آلارم علتِ عملی را نام نمی‌برد: {body!r}"
    assert r["digest"]["raw_text"] == "زنج", "شاهد پاک شد — آلارم جای ذخیره را گرفت"


def t_healthy_proposals_do_not_raise_a_false_alarm():
    alerts = []
    _orig = S.opslib.alert
    S.opslib.alert = lambda items: alerts.append(items)
    try:
        r = S.synthesize(ask=lambda *a, **k: {
            "ok": True, "tier": "primary", "model": "fugu", "cost_usd": 0.0,
            "finish_reason": None,
            "text": ("- عنوانِ یک | چرای یک | قدمِ اولِ عملیِ یک\n"
                     "- عنوانِ دو | چرای دو | قدمِ اولِ عملیِ دو")})
    finally:
        S.opslib.alert = _orig
    assert len(r["digest"]["proposals"]) >= 2
    assert alerts == [], f"آلارمِ کاذب روی نتیجهٔ سالم: {alerts}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_paid_truncation: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
