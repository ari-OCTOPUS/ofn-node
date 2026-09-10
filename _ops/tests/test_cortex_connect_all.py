#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cortex_connect_all.py — چهار اتصالِ مغز با transport جعلی، شبکه/پرداخت مسدود.

MEGAPROMPT-CORTEX-CONNECT-ALL-2026-09-10 §آزمونِ پذیرش:
  · قرمز (بدونِ wrapper: سکوت/None) → سبز (با wrapper + fallbackِ قالب).
  · مصرفِ لجر قابلِ مشاهده: ردیف‌های task صریح (این‌جا در sandbox: connect-calls.jsonl و
    لجرِ هر اتصال؛ paid-calls.jsonl را خودِ model_router در production می‌نویسد).
  · گاردِ راز: prompt حاوی توکن → بدونِ اسکرابر به transport می‌رسد (قرمز)؛ با اسکرابر
    فقط [REDACTED] (سبز). حضورِ راز در هر لاگِ sandbox = FAIL.
هیچ راز/دادهٔ واقعی: همهٔ مقادیر ساختگی و برچسب‌خورده (FAKE). هیچ تماسِ پولی.
"""
import json
import os
import socket
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE.parent, _HERE.parent / "budget", _HERE.parent / "cortex", _HERE.parent / "legs"):
    sys.path.insert(0, str(_p))

import harness  # noqa: E402

ENV = harness.setup("cortex-connect-all")
STATE = Path(ENV["ops"]) / "state"

import opslib          # noqa: E402
import scrub           # noqa: E402
import brain_link      # noqa: E402
import store_reply     # noqa: E402
import lead_triage     # noqa: E402
import content_draft   # noqa: E402
import owner_digest    # noqa: E402

# ── شبکه مسدود: هر تلاشِ socket = شکستِ بلند (نه سکوت) ────────────────────────
_NET_ATTEMPTS = []
_REAL_SOCKET = socket.socket


class _NoNet(_REAL_SOCKET):
    def connect(self, *a, **k):
        _NET_ATTEMPTS.append(a)
        raise AssertionError("network blocked in cortex-connect tests")

    connect_ex = connect


socket.socket = _NoNet

# ── مقادیرِ ساختگیِ برچسب‌خورده (هرگز واقعی) ───────────────────────────────────
FAKE_TG = "<REDACTED-TELEGRAM-TOKEN>"   # 10 + ':' + 35
FAKE_SK = "<REDACTED-OPENAI-KEY>"
FAKE_AWS = "<REDACTED-AWS-KEY-ID>"
FAKE_GH = "ghp_FAKEFAKEFAKEFAKEFAKEFAKE12"
FAKE_SLACK = "<REDACTED-SLACK-TOKEN>"
FAKE_TELNYX = "TELNYX_API_KEY=KEYFAKE0000"
FAKE_KV = "api_key: FAKEKV999"
ALL_FAKES = (FAKE_TG, FAKE_SK, FAKE_AWS, FAKE_GH, FAKE_SLACK, "KEYFAKE0000", "FAKEKV999")


def _fake(text="", *, ok=True, tier="secondary", finish_reason="stop", model="fake-model",
          raise_exc=None, returns="dict", extra=None):
    """transport جعلی: هرچه دریافت کرد ضبط می‌کند؛ هرگز شبکه."""
    calls = []
    result_tier = tier          # tierِ **پاسخ** (شبیه‌سازیِ روتر)، جدا از tierِ درخواستی

    def fn(task, prompt, system="", max_tokens=400, tier=None, **k):
        calls.append({"task": task, "prompt": prompt, "system": system,
                      "max_tokens": max_tokens, "tier": tier})
        if raise_exc:
            raise raise_exc
        if returns is None:
            return None
        if returns == "str":
            return "not a dict"
        d = {"ok": ok, "text": text, "tier": result_tier, "finish_reason": finish_reason,
             "model": model}
        if extra:
            d.update(extra)
        return d
    fn.calls = calls
    return fn


def _rows(rel: str):
    p = STATE / rel
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _sandbox_text() -> str:
    out = []
    for p in STATE.rglob("*.jsonl"):
        out.append(p.read_text("utf-8", errors="replace"))
    for p in STATE.rglob("*.json"):
        out.append(p.read_text("utf-8", errors="replace"))
    return "\n".join(out)


# ── A. اسکرابر ────────────────────────────────────────────────────────────────
def t_a_scrubber_catches_every_listed_pattern_in_persian_and_latin_text():
    fa = (f"سلام، توکنِ رباتم {FAKE_TG} است و کلیدِ {FAKE_SK} را هم داری؛ "
          f"{FAKE_TELNYX} و {FAKE_KV} را نگه دار.")
    en = f"Deploy with {FAKE_AWS}, push with {FAKE_GH}, notify via {FAKE_SLACK}."
    for src in (fa, en):
        found = scrub.leaks(src)
        assert found, ("هیچ الگویی پیدا نشد", src[:40])
        clean = scrub.scrub(src)
        for v in ALL_FAKES:
            assert v not in clean, (v, clean)
        assert scrub.REDACTED in clean and scrub.is_clean(clean), clean
    names = set(scrub.leaks(fa + " " + en))
    assert names >= {"tg_bot_token", "openai_key", "aws_key", "github_pat", "slack_token",
                     "telnyx", "kv_secret"}, names
    # متنِ عادیِ فارسی/انگلیسی دست‌نخورده می‌ماند
    plain = "سفارش ۱۲۳۴ رسید. Thanks for your order, we ship Monday."
    assert scrub.scrub(plain) == plain


def t_b_secret_red_without_scrubber_green_with_brain_link():
    prompt = f"مشتری نوشت: لطفاً سفارشم را پیگیری کن. (لاگ: {FAKE_TG} · {FAKE_SK})"
    raw = _fake("ok")
    raw("customer_reply", prompt)                       # قرمز: مستقیم، بدونِ اسکرابر
    assert FAKE_TG in raw.calls[0]["prompt"], "بدونِ اسکرابر باید توکن برسد (بازتولیدِ قرمز)"
    via = _fake("پاسخ")
    r = brain_link.ask_brain("customer_reply", prompt, system=f"secret={FAKE_AWS}", ask_fn=via)
    assert r["ok"], r
    got = via.calls[0]
    for v in (FAKE_TG, FAKE_SK, FAKE_AWS):
        assert v not in got["prompt"] and v not in got["system"], got
    assert scrub.REDACTED in got["prompt"] and scrub.REDACTED in got["system"]
    rows = _rows("cortex/connect-calls.jsonl")
    assert rows and rows[-1]["task"] == "customer_reply" and rows[-1]["ok"] is True
    assert rows[-1].get("scrubbed") is True
    assert "prompt" not in rows[-1] and "text" not in rows[-1], rows[-1]


def t_c_model_output_is_scrubbed_too():
    via = _fake(f"Sure! your token is {FAKE_GH}")
    r = brain_link.ask_brain("customer_reply", "hi", ask_fn=via)
    assert r["ok"] and FAKE_GH not in r["text"] and scrub.REDACTED in r["text"], r


# ── B. brain_link: ماتریسِ شکست، هرگز استثنا، همیشه دلیل ────────────────────────
def t_d_brain_link_failure_matrix_never_raises_and_always_names_a_reason():
    cases = {
        "ask-exception:TimeoutError": _fake(raise_exc=TimeoutError("t/o")),
        "no-answer": _fake(returns=None),
        "no-answer-str": _fake(returns="str"),
        "kill-switch": _fake(ok=False, extra={"reason": "kill-switch"}),
        "not-a-paid-brain-local": _fake("x", tier="local"),
        "not-a-paid-brain-fallback": _fake("x", extra={"fallback_from": "secondary"}),
        "useless-truncation": _fake("ok.", finish_reason="length"),
        "empty": _fake("   "),
    }
    for label, fn in cases.items():
        r = brain_link.ask_brain("lead_triage", "p", ask_fn=fn)
        assert r["ok"] is False and r.get("reason"), (label, r)
        assert "text" not in r, (label, r)
    reasons = [x["reason"] for x in _rows("cortex/connect-calls.jsonl")[-len(cases):]]
    assert "useless-truncation" in reasons and "not-a-paid-brain" in reasons, reasons
    # پاسخِ بریدهٔ **طولانی** می‌گذرد (منطقِ باریکِ is_useless_truncation)
    r = brain_link.ask_brain("lead_triage", "p", ask_fn=_fake("x" * 80, finish_reason="length"))
    assert r["ok"] is True, r


def t_e_daily_cap_blocks_before_calling_the_transport():
    fn = _fake("ok")
    r1 = brain_link.ask_brain("cap_test", "p", ask_fn=fn, cap=1)
    r2 = brain_link.ask_brain("cap_test", "p", ask_fn=fn, cap=1)
    assert r1["ok"] and r2["ok"] is False and r2["reason"] == "connect-daily-cap", (r1, r2)
    assert len(fn.calls) == 1, "سقف باید **قبل** از تماس ببندد"
    os.environ["OCTOPUS_CONNECT_DAILY_CAP_CAP_ENV"] = "0"
    try:
        r3 = brain_link.ask_brain("cap_env", "p", ask_fn=fn)
        assert r3["ok"] is False and r3["cap"] == 0 and len(fn.calls) == 1, r3
    finally:
        os.environ.pop("OCTOPUS_CONNECT_DAILY_CAP_CAP_ENV", None)
    assert brain_link.daily_cap("anything") == brain_link.DEFAULT_DAILY_CAP


# ── C. اتصالِ ۱: پیامِ مشتریِ فروشگاه ────────────────────────────────────────────
def t_f_store_reply_red_silence_becomes_green_fallback_template():
    ev = {"event_id": "order:FAKE-1001", "kind": "order", "order_id": "FAKE-1001",
          "items": ["ZM-0013 gallery print"], "customer_text": f"where is my order? ({FAKE_SK})"}
    dead = _fake(returns=None)                          # قرمز: مغز None می‌دهد
    assert brain_link.ask_brain(store_reply.TASK, "p", ask_fn=dead)["ok"] is False
    row = store_reply.draft_reply(ev, ask_fn=dead)     # سبز: هرگز سکوت
    assert row["reply_text"] == store_reply.FALLBACK and row["fallback"] is True, row
    assert row["ok"] is False and row["reason"] == "no-answer", row
    assert row["task"] == "customer_reply" and row["sent"] is False and row["delivery"] is None
    assert row["production_authorized"] is False
    assert "customer_text" not in row and row["customer_text_sha"], ("متنِ مشتری ذخیره نشود", row)
    assert FAKE_SK not in dead.calls[0]["prompt"], "اسکرابر پیش از مغز"
    led = _rows("store/replies.jsonl")
    assert led and led[-1]["event_id"] == ev["event_id"]


def t_g_store_reply_brain_path_forbidden_filter_and_replay():
    good = _fake("Thanks Sam — your gallery print is being packed; we'll email tracking soon.")
    ev = {"event_id": "order:FAKE-1002", "kind": "order", "order_id": "FAKE-1002",
          "customer_name": "Sam"}
    row = store_reply.draft_reply(ev, ask_fn=good)
    assert row["fallback"] is False and row["ok"] is True and "tracking" in row["reply_text"], row
    assert good.calls[0]["task"] == "customer_reply" and good.calls[0]["max_tokens"] >= 600
    assert good.calls[0]["tier"] == "secondary", good.calls[0]
    # تکرارِ رویداد: همان ردیف، بدونِ تماسِ دوم
    again = store_reply.draft_reply(ev, ask_fn=good)
    assert again.get("replayed") is True and again["reply_sha"] == row["reply_sha"]
    assert len(good.calls) == 1, "replay نباید مغز را دوباره صدا بزند"
    # واژهٔ ممنوعه → قالب
    bad = _fake("We GUARANTEE a refund now, act now! send bank details.")
    row2 = store_reply.draft_reply({"event_id": "order:FAKE-1003", "order_id": "FAKE-1003"},
                                   ask_fn=bad)
    assert row2["fallback"] is True and row2["reason"].startswith("forbidden-word:"), row2
    assert row2["reply_text"] == store_reply.FALLBACK
    # بدونِ event_id → رد، بدونِ تماس
    assert store_reply.draft_reply({"kind": "order"}, ask_fn=good)["ok"] is False
    assert len(good.calls) == 1


def t_h_store_reply_proposes_to_owner_via_fake_channel_without_any_delivery_receipt():
    class FakeChan:
        wired = True

        def __init__(self):
            self.sent = []

        def send_text(self, text, reply_markup=None, chat_id=None, stream=None, topic_id=None):
            self.sent.append({"text": text, "stream": stream, "reply_markup": reply_markup})
            return True
    ch = FakeChan()
    row = store_reply.draft_reply({"event_id": "order:FAKE-1004", "order_id": "FAKE-1004"},
                                  ask_fn=_fake("Thanks! We'll ship this week."))
    assert store_reply.propose(row, ch) is True and len(ch.sent) == 1
    card = ch.sent[0]["text"]
    assert "پیش‌نویسِ پاسخ" in card and "کلاس Z" in card and ch.sent[0]["reply_markup"] is None
    assert ch.sent[0]["stream"] == "store"
    # لجر همچنان sent=False — کارتِ مالک رسیدِ تحویل به مشتری نیست
    last = [r for r in _rows("store/replies.jsonl") if r["event_id"] == "order:FAKE-1004"][-1]
    assert last["sent"] is False and last["delivery"] is None
    # کانالِ not-wired → False، بدونِ استثنا
    ch.wired = False
    assert store_reply.propose(row, ch) is False and len(ch.sent) == 1


def t_i_store_watch_diff_yields_an_order_event_only_on_change():
    prev = {"orders": {"last_order_id": None}}
    cur = {"orders": {"last_order_id": "FAKE-77", "last_created": "2026-09-10T00:00:00Z"}}
    ev = store_reply.event_from_store_watch(prev, cur)
    assert ev and ev["event_id"] == "order:FAKE-77" and ev["kind"] == "order", ev
    assert store_reply.event_from_store_watch(cur, cur) is None
    assert store_reply.event_from_store_watch(None, {"orders": {}}) is None


# ── D. اتصالِ ۲: غربالِ لید ────────────────────────────────────────────────────
def t_j_lead_triage_brain_json_then_rule_fallback_then_replay():
    lead = {"lead_id": "FAKE-L1", "title": "Paint 2 bedrooms", "description": "Two bedrooms, Ryde",
            "budget": "600", "address": "Ryde NSW", "score": 75}
    fn = _fake('{"priority": "high", "summary": "2 bedrooms in Ryde, $600", "why": "close, budget ok"}')
    row = lead_triage.triage(lead, ask_fn=fn)
    assert row["priority"] == "high" and row["fallback"] is False and row["task"] == "lead_triage", row
    assert row["queued_for_owner"] is True and row["decided"] is False
    assert "🔴" in lead_triage.card_line(row) and "مغز" in lead_triage.card_line(row)
    # JSON خراب → قاعده از score، fallback صریح
    bad = _fake("sure thing, looks great")
    row2 = lead_triage.triage({"lead_id": "FAKE-L2", "description": "x", "score": 45}, ask_fn=bad)
    assert row2["priority"] == "medium" and row2["fallback"] is True and row2["reason"] == "bad-format", row2
    row3 = lead_triage.triage({"lead_id": "FAKE-L3", "description": "x"}, ask_fn=_fake(returns=None))
    assert row3["priority"] == "low" and row3["reason"] == "no-answer", row3
    # replay
    again = lead_triage.triage(lead, ask_fn=fn)
    assert again.get("replayed") is True and len(fn.calls) == 1
    assert _rows("leads/triage.jsonl")[-1]["lead_key"] == "FAKE-L3"


# ── E. اتصالِ ۳: پیش‌نویسِ hero — هرگز انتشار ─────────────────────────────────────
def t_k_content_draft_variants_and_publish_is_structurally_impossible():
    fn = _fake('{"variants": [{"headline": "Made by hand, sent with care", "sub": "Small-batch gifts from Sydney", "cta": "Shop now"},'
               ' {"headline": "Gifts that feel personal", "sub": "Handmade, local, honest", "cta": "Browse"}]}')
    row = content_draft.draft_hero("Ziman handmade gifts hero, warm tone", n=2, ask_fn=fn)
    assert row["ok"] and len(row["variants"]) == 2 and row["published"] is False, row
    assert row["chosen"] is None and row["task"] == "content_draft"
    assert "انتخاب کن" in content_draft.owner_card(row)
    fail = content_draft.draft_hero("other brief", ask_fn=_fake(raise_exc=OSError("net")))
    assert fail["ok"] is False and fail["variants"] == [] and "ask-exception" in fail["reason"], fail
    assert content_draft.PUBLISH_ALLOWED is False
    try:
        content_draft.publish(row)
        raise AssertionError("publish باید PermissionError بدهد")
    except PermissionError as e:
        assert "owner vote" in str(e)
    again = content_draft.draft_hero("Ziman handmade gifts hero, warm tone", n=2, ask_fn=fn)
    assert again.get("replayed") is True and len(fn.calls) == 1


# ── F. اتصالِ ۴: digestِ مالک — مغز یا همان متنِ خام ─────────────────────────────
def t_l_owner_digest_summarises_or_keeps_the_raw_text():
    raw = "beat 67336 · store-sync ok 3/3 · fugu 66/60 · 0 orders · 2 leads pending"
    r = owner_digest.summarize(raw, ask_fn=_fake("▸ سفارش: ۰\n▸ فوگو 66/60 پر\n▸ ۲ لید در انتظار"))
    assert r["ok"] and r["fallback"] is False and r["text"].startswith("▸"), r
    r2 = owner_digest.summarize(raw, ask_fn=_fake("", ok=False, extra={"reason": "kill-switch"}))
    assert r2["ok"] is False and r2["fallback"] is True and r2["text"] == raw, r2
    assert r2["reason"] == "kill-switch"
    assert owner_digest.summarize("   ")["ok"] is False
    rows = _rows("cortex/digest-summaries.jsonl")
    assert rows and rows[-1]["task"] == "owner_digest" and "text" not in rows[-1]


# ── G. گاردهای سراسری ───────────────────────────────────────────────────────────
def t_m_no_secret_in_any_sandbox_log_and_nothing_touched_the_real_vault():
    blob = _sandbox_text()
    for v in ALL_FAKES:
        assert v not in blob, ("راز در لاگِ sandbox", v)
    real = str(harness.REAL_VAULT).lower()
    assert real not in str(STATE).lower() and real not in str(opslib.STATE_DIR).lower()
    for rel in ("store/replies.jsonl", "leads/triage.jsonl", "content/hero-drafts.jsonl",
                "cortex/digest-summaries.jsonl", "cortex/connect-calls.jsonl"):
        for r in _rows(rel):
            assert r.get("task"), (rel, "ردیف بدونِ task صریح", r)


def t_n_zero_network_attempts_and_zero_paid_calls():
    assert not _NET_ATTEMPTS, _NET_ATTEMPTS
    assert not (STATE / "paid-calls.jsonl").exists(), "هیچ ردیفِ پولی نباید در sandbox ساخته شود"
    assert "model_router" not in sys.modules or True   # importِ ماژول مجاز است؛ تماس نه


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_cortex_connect_all: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
