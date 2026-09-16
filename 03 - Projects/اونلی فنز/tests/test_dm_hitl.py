#!/usr/bin/env python3
"""test_dm_hitl.py — تست‌های safety net #1: DM HITL queue.

تضمین می‌کند:
  - AI فقط draft می‌زند؛ هیچ متدِ send/transmit/auto-send وجود ندارد.
  - آری قبل از ارسال باید approve کند.
  - DM حاوی banned-copy (paypal/هویت/شهر) flag می‌شود و approve نمی‌شود.
  - payload نهایی برای copy-paste دستی است، نه ارسال خودکار.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
_LANGAR = _HERE.parent / "langar"
for p in (_BRAIN, _LANGAR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from dm_pipeline import DmPipeline, _BANNED_DM  # noqa: E402
import dm_admin  # noqa: E402


def _pipe(tmp_path):
    return DmPipeline(store_path=tmp_path / "dm.json")


# ── structural: no outward methods ───────────────────────────────────────

def test_no_outward_methods(tmp_path):
    p = _pipe(tmp_path)
    for m in ("send", "deliver", "transmit", "post", "publish", "dm_send",
              "telegram_send", "auto_send"):
        assert not hasattr(p, m), f"HITL violated: {m} exists"


def test_admin_digest_reports_no_auto_send(tmp_path):
    p = _pipe(tmp_path)
    d = p.admin_digest()
    assert d["auto_send"] is False


# ── draft → review → approve flow ────────────────────────────────────────

def test_draft_creates_pending_review(tmp_path):
    p = _pipe(tmp_path)
    r = p.draft("of", "welcome", "Hey! Thanks for subscribing. Heres a welcome offer.")
    assert r["ok"] is True
    assert r["status"] == "pending_review"
    assert r["flagged"] is False


def test_approve_produces_manual_payload_not_auto_send(tmp_path):
    p = _pipe(tmp_path)
    rid = p.draft("of", "welcome", "Welcome aboard!")["id"]
    r = p.approve(rid)
    assert r["ok"] is True
    assert r["status"] == "ready_for_manual_send"
    assert r["auto_sent"] is False
    assert "payload" in r
    assert r["payload"]["body"] == "Welcome aboard!"


def test_reject_works(tmp_path):
    p = _pipe(tmp_path)
    rid = p.draft("of", "general", "hello")["id"]
    r = p.reject(rid, "not needed")
    assert r["ok"] is True
    assert r["status"] == "rejected"


def test_mark_sent_requires_ready_first(tmp_path):
    """نمی‌توان mark_sent زد قبل از approve (fail-closed)."""
    p = _pipe(tmp_path)
    rid = p.draft("of", "general", "hello")["id"]
    # هنوز pending_review
    r = p.mark_sent(rid)
    assert r["ok"] is False
    # حالا approve کن بعد mark_sent
    p.approve(rid)
    r2 = p.mark_sent(rid)
    assert r2["ok"] is True
    assert r2["status"] == "sent"


# ── containment guard ────────────────────────────────────────────────────

def test_draft_with_paypal_flagged(tmp_path):
    """DM حاوی paypal (rule #3) باید flag شود."""
    p = _pipe(tmp_path)
    r = p.draft("of", "ppv_offer", "pay me via paypal for custom content")
    assert r["flagged"] is True


def test_approve_flagged_dm_blocked(tmp_path):
    """DM flagged نباید approve شود (fail-closed)."""
    p = _pipe(tmp_path)
    rid = p.draft("of", "general", "send money via cashapp")["id"]
    r = p.approve(rid)
    assert r["ok"] is False
    assert "flagged" in r["error"] or "containment" in r["error"]


def test_draft_with_identity_flagged(tmp_path):
    """DM نباید نامِ پارتنر/شهر را نشت دهد."""
    p = _pipe(tmp_path)
    cases = ["my name is saba", "I live in sydney", "persian girl here",
             "find me on onlyfans directly"]
    for body in cases:
        rid = p.draft("of", "general", body)["id"]
        item = p._find(rid)
        assert item["flagged"] is True, f"missed containment: {body}"


def test_banned_list_covers_payment_redirections():
    """rule #3: همهٔ مسیرهای پرداختِ خارج از پلتفرم باید banned باشند."""
    for term in ["paypal", "cashapp", "venmo", "crypto", "bitcoin", "usdt", "zelle"]:
        assert term in _BANNED_DM, f"missing payment redirect: {term}"


# ── dm_admin dispatch ────────────────────────────────────────────────────

def test_dm_admin_status_dispatch(tmp_path):
    p = _pipe(tmp_path)
    msg = dm_admin.handle_dm("/dm_status", "", pipe=p)
    assert "DM HITL" in msg
    assert "auto-send: خاموش" in msg


def test_dm_admin_ok_dispatch(tmp_path):
    p = _pipe(tmp_path)
    rid = p.draft("of", "welcome", "Hi there!")["id"]
    msg = dm_admin.handle_dm("/dm_ok", rid, pipe=p)
    assert "آمادهٔ ارسال" in msg
    assert "دستی" in msg   # تأکید بر manual


def test_dm_admin_no_arg_errors_cleanly(tmp_path):
    p = _pipe(tmp_path)
    msg = dm_admin.handle_dm("/dm_ok", "", pipe=p)
    assert "❌" in msg


def test_dm_admin_unknown_returns_help(tmp_path):
    p = _pipe(tmp_path)
    msg = dm_admin.handle_dm("/dm_unknown", "", pipe=p)
    assert "DM HITL" in msg or "دستورهای" in msg
