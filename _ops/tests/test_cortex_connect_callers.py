#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cortex_connect_callers.py — مسیرِ کامل caller → wrapper → consumer با transport جعلی.

بازبینیِ ۰۹-۱۱: «چهار ماژول ساخته شده‌اند، اما اتصالِ مصرف‌کننده تکمیل نشده». این فایل
صداکننده‌های **واقعی** را می‌راند، نه wrapper را در خلأ:
  ۱) drive_loops.sync_store_watch  (ssh جعلی) → store_reply.draft_reply → replies.jsonl
     → store_reply.propose_pending (consumer ِ organism epoch) → کارتِ مالک روی کانالِ جعلی
  ۲) lead_pipeline._card_text      → _triage_line → lead_triage.triage → خطِ کارت
  ۳) wiring._digest_text_with_brain → owner_digest.summarize (splice ِ brain_digest_beat)
همه پشتِ فلگ‌های OCTOPUS_CONNECT_* (پیش‌فرض خاموش ⇒ رفتارِ production بایت‌به‌بایت قبلی).
هیچ فلگِ OCTOPUS_WIRE_* لمس نمی‌شود. model_router.ask در سطحِ ماژول جعلی می‌شود (همان
seam ِ brain_link: `ask_fn = _mr.ask`)؛ socket مسدود؛ هیچ ردیفِ paid-calls.
"""
import ast
import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE.parent, _HERE.parent / "budget", _HERE.parent / "cortex", _HERE.parent / "legs"):
    sys.path.insert(0, str(_p))

import harness  # noqa: E402

ENV = harness.setup("cortex-connect-callers")
STATE = Path(ENV["ops"]) / "state"

import opslib          # noqa: E402
import model_router    # noqa: E402 — فقط برای جعلِ ask در سطحِ ماژول
import store_reply     # noqa: E402
import drive_loops     # noqa: E402
import lead_pipeline   # noqa: E402
import wiring          # noqa: E402

_NET = []
_RealSock = socket.socket


class _NoNet(_RealSock):
    def connect(self, *a, **k):
        _NET.append(a)
        raise AssertionError("network blocked")

    connect_ex = connect


socket.socket = _NoNet
# عکسِ فلگ‌های wire در لحظهٔ شروع — این فایل نباید هیچ‌کدام را بسازد/عوض کند (§۴ AGENTS.md)
_WIRE_SNAPSHOT = {k: v for k, v in os.environ.items()
                  if k.startswith("OCTOPUS_WIRE_") or k.startswith("OFN_WIRE_")}

FLAG_STORE, FLAG_LEAD, FLAG_DIGEST = (store_reply.FLAG, "OCTOPUS_CONNECT_LEAD_TRIAGE",
                                     "OCTOPUS_CONNECT_OWNER_DIGEST")
ROUTER_CALLS = []


def _router_fake(text):
    def ask(task, prompt, system="", max_tokens=400, tier=None, **k):
        ROUTER_CALLS.append({"task": task, "max_tokens": max_tokens, "tier": tier})
        return {"ok": True, "text": text, "tier": "secondary", "finish_reason": "stop",
                "model": "fake-router-model"}
    return ask


def _rows(rel):
    p = STATE / rel
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _clear_flags():
    for f in (FLAG_STORE, FLAG_LEAD, FLAG_DIGEST):
        os.environ.pop(f, None)


class _CP:
    def __init__(self, rc, out=""):
        self.returncode, self.stdout, self.stderr = rc, out, ""


def _watch(order_id):
    return json.dumps({"schema": "store-watch.v1", "ts_utc": "2026-09-10T00:00:00Z",
                       "domain": {"dns_ok": True, "page_ok": True},
                       "orders": {"ok": True, "total_fetched": 1, "paid_since_sep1": 0,
                                  "last_order_id": order_id,
                                  "last_created": "2026-09-10T00:00:00Z",
                                  "first_real_order": bool(order_id)}})


def _ssh_fake(watch_json):
    def run(cmd, **k):
        target = cmd[-1] if isinstance(cmd, list) else str(cmd)
        if "store-watch.json" in target:
            return _CP(0, watch_json)
        return _CP(1, "")                     # FIRST-ORDER-MARKER: نبود
    return run


def _sandbox_drive_loops():
    d = Path(tempfile.mkdtemp(prefix="dl-", dir=str(STATE)))
    drive_loops.STATE = d
    drive_loops.DRIVE = d / "drive"
    return d


# ── ۱) فروشگاه: caller واقعی (sync_store_watch) با ssh جعلی ─────────────────────
def t_a_flag_off_sync_store_watch_is_byte_identical_and_writes_no_draft():
    _clear_flags()
    _sandbox_drive_loops()
    real_run, subprocess.run = subprocess.run, _ssh_fake(_watch("FAKE-OFF-1"))
    real_ask, model_router.ask = model_router.ask, _router_fake("should never be used")
    try:
        out = drive_loops.sync_store_watch()
    finally:
        subprocess.run, model_router.ask = real_run, real_ask
    assert out["ok"] is True and "store_reply" not in out, out
    assert not [r for r in _rows("store/replies.jsonl") if "FAKE-OFF-1" in str(r.get("order_id"))]
    assert not ROUTER_CALLS, "با فلگِ خاموش هیچ تماسی با روتر نباید رخ دهد"


def t_b_flag_on_new_order_flows_caller_to_wrapper_to_ledger_and_is_idempotent():
    _clear_flags()
    os.environ[FLAG_STORE] = "1"
    d = _sandbox_drive_loops()
    (d / "store-watch.json").write_text(_watch(None), "utf-8")      # snapshot ِ قبلی: بدونِ سفارش
    real_run, subprocess.run = subprocess.run, _ssh_fake(_watch("FAKE-77"))
    real_ask, model_router.ask = model_router.ask, _router_fake(
        "Thanks — your order is being packed; tracking follows by email.")
    try:
        out1 = drive_loops.sync_store_watch()
        out2 = drive_loops.sync_store_watch()   # همان snapshot دوباره → بدونِ رویداد
    finally:
        subprocess.run, model_router.ask = real_run, real_ask
        _clear_flags()
    assert out1.get("store_reply", {}).get("event") == "order:FAKE-77", out1
    assert out1["store_reply"]["fallback"] is False and out1["store_reply"]["replayed"] is False
    assert out2.get("store_reply") == {"event": None}, out2
    rows = [r for r in _rows("store/replies.jsonl") if r.get("event_id") == "order:FAKE-77"]
    assert len(rows) == 1 and rows[0]["schema"] == store_reply.SCHEMA, rows
    assert rows[0]["task"] == "customer_reply" and rows[0]["sent"] is False
    assert len(ROUTER_CALLS) == 1 and ROUTER_CALLS[0]["task"] == "customer_reply", ROUTER_CALLS
    assert ROUTER_CALLS[0]["tier"] == "secondary" and ROUTER_CALLS[0]["max_tokens"] >= 600
    # مسیرِ رسیدِ brain_link هم واقعاً پر شد
    calls = [c for c in _rows("cortex/connect-calls.jsonl") if c.get("task") == "customer_reply"]
    assert calls and calls[-1]["ok"] is True and "prompt" not in calls[-1]


def t_c_router_failure_inside_the_real_caller_yields_the_fallback_not_silence():
    _clear_flags()
    os.environ[FLAG_STORE] = "1"
    d = _sandbox_drive_loops()
    (d / "store-watch.json").write_text(_watch(None), "utf-8")
    real_run, subprocess.run = subprocess.run, _ssh_fake(_watch("FAKE-78"))

    def _dead(*a, **k):
        raise TimeoutError("fixture: router timeout")
    real_ask, model_router.ask = model_router.ask, _dead
    try:
        out = drive_loops.sync_store_watch()
    finally:
        subprocess.run, model_router.ask = real_run, real_ask
        _clear_flags()
    assert out["ok"] is True, out                       # sync خودش نمی‌میرد
    assert out["store_reply"]["fallback"] is True, out
    row = [r for r in _rows("store/replies.jsonl") if r.get("event_id") == "order:FAKE-78"][-1]
    assert row["reply_text"] == store_reply.FALLBACK and row["reason"].startswith("ask-exception")


# ── consumer ِ organism epoch: propose_pending روی کانالِ جعلی ────────────────────
class FakeChan:
    wired = True

    def __init__(self):
        self.sent = []

    def send_text(self, text, reply_markup=None, chat_id=None, stream=None, topic_id=None):
        self.sent.append({"text": text, "stream": stream, "reply_markup": reply_markup})
        return True


def t_d_pending_drafts_reach_the_owner_exactly_once_and_never_the_customer():
    _clear_flags()
    ch = FakeChan()
    assert store_reply.propose_pending(ch) == {"proposed": 0, "skipped": 0, "enabled": False}
    assert not ch.sent, "فلگ خاموش ⇒ هیچ کارتی"
    os.environ[FLAG_STORE] = "1"
    try:
        pend = store_reply.pending_for_owner()
        assert {p["event_id"] for p in pend} >= {"order:FAKE-77", "order:FAKE-78"}, pend
        r1 = store_reply.propose_pending(ch, limit=10)
        assert r1["proposed"] == len(pend) and r1["skipped"] == 0, (r1, len(pend))
        assert len(ch.sent) == len(pend)
        assert all(s["reply_markup"] is None and s["stream"] == "store" for s in ch.sent)
        assert all("کلاس Z" in s["text"] for s in ch.sent)
        r2 = store_reply.propose_pending(ch, limit=10)
        assert r2["proposed"] == 0 and len(ch.sent) == len(pend), "هر پیش‌نویس فقط یک کارت"
        assert store_reply.pending_for_owner() == []
    finally:
        _clear_flags()
    # لجر: هر رویداد یک ردیفِ draft + یک ردیفِ proposed؛ sent همچنان False
    rows = _rows("store/replies.jsonl")
    for eid in ("order:FAKE-77", "order:FAKE-78"):
        drafts = [r for r in rows if r.get("event_id") == eid and r["schema"] == store_reply.SCHEMA]
        props = [r for r in rows if r.get("event_id") == eid and r["schema"] == store_reply.SCHEMA_PROPOSED]
        assert len(drafts) == 1 and len(props) == 1, (eid, len(drafts), len(props))
        assert drafts[0]["sent"] is False and drafts[0]["delivery"] is None
    # کانالِ ناموفق ⇒ رسیدِ proposed نوشته نمی‌شود ⇒ دفعهٔ بعد دوباره تلاش می‌شود
    row = store_reply.draft_reply({"event_id": "order:FAKE-79", "order_id": "FAKE-79"},
                                  ask_fn=lambda *a, **k: None)

    class Dead(FakeChan):
        def send_text(self, *a, **k):
            return False
    os.environ[FLAG_STORE] = "1"
    try:
        r3 = store_reply.propose_pending(Dead())
        assert r3["proposed"] == 0 and r3["skipped"] == 1, r3
        assert [p["event_id"] for p in store_reply.pending_for_owner()] == ["order:FAKE-79"]
    finally:
        _clear_flags()


def t_e_organism_epoch_calls_propose_pending_behind_the_flag_and_fail_soft():
    """صداکنندهٔ واقعیِ consumer: بلوکِ organism.py باید (الف) propose_pending را صدا بزند،
    (ب) پشتِ enabled() باشد، (ج) داخلِ try باشد که tick را نکشد. (AST، نه grep ِ کامنت.)"""
    src = (harness.SELF_OPS / "organism.py").read_text("utf-8")
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        seg = ast.get_source_segment(src, node) or ""
        if "propose_pending" in seg:
            # فقط درونی‌ترین try (بلوکِ epoch خودش داخلِ try ِ بزرگ‌تر است)
            if any(isinstance(c, ast.Try) and c is not node
                   and "propose_pending" in (ast.get_source_segment(src, c) or "")
                   for c in ast.walk(node)):
                continue
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute) and n.func.attr == "propose_pending"]
            guards = [n for n in ast.walk(node) if isinstance(n, ast.Call)
                      and isinstance(n.func, ast.Attribute) and n.func.attr == "enabled"]
            hits.append((len(calls), len(guards), bool(node.handlers)))
    assert hits == [(1, 1, True)], hits


# ── ۲) لید: caller واقعی (_card_text) ─────────────────────────────────────────────
class _SC:
    def __init__(self, lead, score):
        self.lead, self.score = lead, score

    def card(self):
        return "SCORED-CARD"


def t_f_lead_card_gets_a_brain_priority_line_only_when_the_flag_is_on():
    _clear_flags()
    sc = _SC({"description": "Paint 2 bedrooms in Ryde", "address": "Ryde NSW"}, 75)
    real_ask, model_router.ask = model_router.ask, _router_fake(
        '{"priority": "high", "summary": "2 bedrooms, Ryde", "why": "budget ok"}')
    try:
        off = lead_pipeline._card_text("FAKE-L9", sc, None, {"summary": "r"})
        assert "SCORED-CARD" in off and "اولویت" not in off, off
        os.environ[FLAG_LEAD] = "1"
        on = lead_pipeline._card_text("FAKE-L9", sc, None, {"summary": "r"})
        assert "🔴 اولویت: high (مغز)" in on and "2 bedrooms" in on, on
        again = lead_pipeline._card_text("FAKE-L9", sc, None, {"summary": "r"})
        assert "🔴 اولویت: high" in again
    finally:
        model_router.ask = real_ask
        _clear_flags()
    lead_calls = [c for c in ROUTER_CALLS if c["task"] == "lead_triage"]
    assert len(lead_calls) == 1, ("idempotent روی lead_id — یک تماس", lead_calls)
    rows = [r for r in _rows("leads/triage.jsonl") if r.get("lead_key") == "FAKE-L9"]
    assert len(rows) == 1 and rows[0]["priority"] == "high" and rows[0]["queued_for_owner"]


def t_g_lead_card_survives_a_broken_brain_with_rule_fallback():
    _clear_flags()
    os.environ[FLAG_LEAD] = "1"
    sc = _SC({"description": "x"}, 20)
    real_ask, model_router.ask = model_router.ask, (lambda *a, **k: None)
    try:
        card = lead_pipeline._card_text("FAKE-L10", sc, None, {})
    finally:
        model_router.ask = real_ask
        _clear_flags()
    assert "⚪ اولویت: low (قاعده)" in card, card


# ── ۳) digest: splice ِ brain_digest_beat ────────────────────────────────────────
def t_h_digest_text_is_summarised_only_behind_the_flag_and_never_lost():
    _clear_flags()
    raw = "beat 67336 · store-sync ok · fugu 66/60 · 0 orders"
    fake = lambda task, prompt, system="", max_tokens=400, tier=None, **k: {  # noqa: E731
        "ok": True, "text": "▸ سفارش: ۰\n▸ فوگو 66/60", "tier": "secondary",
        "finish_reason": "stop", "model": "fake"}
    assert wiring._digest_text_with_brain(raw, ask_fn=fake) == raw, "فلگ خاموش ⇒ بایت‌به‌بایت"
    os.environ[FLAG_DIGEST] = "1"
    try:
        out = wiring._digest_text_with_brain(raw, ask_fn=fake)
        assert out.startswith("▸ سفارش") and out != raw, out
        dead = lambda *a, **k: (_ for _ in ()).throw(OSError("net"))  # noqa: E731
        assert wiring._digest_text_with_brain(raw, ask_fn=dead) == raw
        assert wiring._digest_text_with_brain("", ask_fn=fake) == ""
    finally:
        _clear_flags()
    rows = _rows("cortex/digest-summaries.jsonl")
    assert rows and rows[-1]["task"] == "owner_digest"
    assert any(r["ok"] for r in rows) and any(r["fallback"] for r in rows)


def t_i_brain_digest_beat_summarises_after_the_send_gate_not_before():
    """splice باید بعد از _dialogue_gate و داخلِ شاخهٔ ارسال باشد (تماسِ پولی برای
    digest ِ فرستاده‌نشده = سوختن). AST روی خودِ تابع."""
    src = (harness.SELF_OPS / "wiring.py").read_text("utf-8")
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
              and n.name == "brain_digest_beat")
    seg = ast.get_source_segment(src, fn)
    assert seg.count("_digest_text_with_brain(") == 1, seg.count("_digest_text_with_brain(")
    assert seg.index("_dialogue_gate(") < seg.index("_digest_text_with_brain(")
    assert seg.index("_digest_text_with_brain(") < seg.index("_dialogue_mark(")


# ── گاردهای سراسری ────────────────────────────────────────────────────────────────
def t_j_no_network_no_paid_rows_no_wire_flags_touched_no_real_vault_writes():
    assert not _NET, _NET
    assert not (STATE / "paid-calls.jsonl").exists()
    now = {k: v for k, v in os.environ.items()
           if k.startswith("OCTOPUS_WIRE_") or k.startswith("OFN_WIRE_")}
    assert now == _WIRE_SNAPSHOT, "این تست هیچ فلگِ wire ای را نمی‌سازد/عوض نمی‌کند"
    real = str(harness.REAL_VAULT).lower()
    assert real not in str(STATE).lower() and real not in str(drive_loops.STATE).lower()
    for rel in ("store/replies.jsonl", "leads/triage.jsonl", "cortex/digest-summaries.jsonl",
                "cortex/connect-calls.jsonl"):
        for r in _rows(rel):
            assert r.get("task"), (rel, r)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_cortex_connect_callers: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
