#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pending_card_recovery.py — C7 Slice 1: بازسازیِ کارت‌های معلق بعد از restart.

پوشش (لیستِ اجباریِ مأموریت):
  1. pending money card restart → بازسازی از gated_effect
  2. binding mismatch / card swap → توکن reject
  3. old-token replay → reject (binding/exp تازه)
  4. pending RFC restart → بازسازی از rfcs.json
  5. consumed/denied/merged → بازسازی نمی‌شوند
  6. double boot → صفر کارتِ تکراری (dedupِ durable)
  7. STOP/HALT → صفر action (فقط metadata)
$0 آفلاین؛ صفر شبکه/پول/settle؛ sandbox.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("pending-card-recovery")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import pending_card_recovery as pcr  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))
_OWNER = 777
_SECRET = "unit-test-secret-not-real"


def _env():
    os.environ["OCTOPUS_WIRE_PROPOSAL_BUTTONS"] = "1"
    os.environ[pcr.SECRET_ENV] = _SECRET
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)


class _Chan:
    def __init__(self):
        self._pending = {}
        self._pending_rfc = {}
        self.sent = []
        self.wired = True

    def send_text(self, text, **kw):
        self.sent.append(text)
        return True

    def rfc_card(self, rfc_id, summary):
        self._pending_rfc[rfc_id] = {"summary": summary, "token": "tok", "status": "pending"}
        return True


def _chrono(tag, rows):
    """chrono.db با gated_effect fixture. rows = [(effect_id, status, content_hash, action_kind,
    target_ref, expires_at, amount)]."""
    p = _STATE / f"chrono-{tag}.db"
    if p.exists():
        p.unlink()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p))
    con.execute("CREATE TABLE gated_effect(effect_id TEXT PRIMARY KEY, kind TEXT, payload_ref TEXT, "
                "status TEXT, content_hash TEXT, action_kind TEXT, target_ref TEXT, expires_at INTEGER)")
    for (eid, st, ch, ak, tr, exp, amt) in rows:
        con.execute("INSERT INTO gated_effect(effect_id,kind,payload_ref,status,content_hash,"
                    "action_kind,target_ref,expires_at) VALUES(?,?,?,?,?,?,?,?)",
                    (eid, "pay", json.dumps({"amount_aud": amt}), st, ch, ak, tr, exp))
    con.commit(); con.close()
    return p


def _rfcs(tag, rfclist):
    p = _STATE / f"rfcs-{tag}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"ts": 0, "schema": "v1", "rfcs": rfclist}, ensure_ascii=False), "utf-8")
    return p


_FUTURE = pcr._now() + 100000


# ── ۱: pending money card restart ───────────────────────────────────────────────
def t_money_card_rebuilt():
    _env()
    db = _chrono("t1", [("fx-1", "pending", "ch1", "pay", "tgt1", _FUTURE, 12.5)])
    ch = _Chan()
    r = pcr.rebuild_money_cards(channel=ch, chrono_db_path=db, owner=_OWNER, state_dir=_STATE)
    assert r["rebuilt"] == 1, r
    assert "fx-1" in ch._pending and ch._pending["fx-1"]["token"].startswith("mc1."), ch._pending
    ok, why = pcr.verify_money_token(ch._pending["fx-1"]["token"], effect_id="fx-1",
                                     content_hash="ch1", action_kind="pay", target_ref="tgt1",
                                     amount=12.5, owner=_OWNER)
    assert ok, f"توکنِ بازسازی‌شده باید verify شود: {why}"


# ── ۲: binding mismatch / card swap ─────────────────────────────────────────────
def t_binding_mismatch_rejected():
    _env()
    tok = pcr.mint_money_token(effect_id="fx-1", content_hash="ch1", action_kind="pay",
                               target_ref="tgt1", amount=12.5, owner=_OWNER, exp=_FUTURE)
    # همان توکن روی effect/amount/target دیگر → reject
    assert not pcr.verify_money_token(tok, effect_id="fx-2", content_hash="ch1", action_kind="pay",
                                      target_ref="tgt1", amount=12.5, owner=_OWNER)[0]
    assert not pcr.verify_money_token(tok, effect_id="fx-1", content_hash="ch1", action_kind="pay",
                                      target_ref="tgt1", amount=99.9, owner=_OWNER)[0]
    assert not pcr.verify_money_token(tok, effect_id="fx-1", content_hash="EVIL", action_kind="pay",
                                      target_ref="tgt1", amount=12.5, owner=_OWNER)[0]
    # غیرمالک → reject
    assert not pcr.verify_money_token(tok, effect_id="fx-1", content_hash="ch1", action_kind="pay",
                                      target_ref="tgt1", amount=12.5, owner=999)[0]


# ── ۳: old-token replay (expired) ───────────────────────────────────────────────
def t_old_token_replay_rejected():
    _env()
    old = pcr.mint_money_token(effect_id="fx-1", content_hash="ch1", action_kind="pay",
                               target_ref="tgt1", amount=12.5, owner=_OWNER, exp=pcr._now() - 10)
    assert pcr.verify_money_token(old, effect_id="fx-1", content_hash="ch1", action_kind="pay",
                                  target_ref="tgt1", amount=12.5, owner=_OWNER)[1] == "expired"


# ── ۴: pending RFC restart ──────────────────────────────────────────────────────
def t_rfc_card_rebuilt():
    _env()
    rf = _rfcs("t4", [{"rfc_id": "RFC-1", "status": "submitted", "bottleneck": "slow tick"}])
    ch = _Chan()
    r = pcr.rebuild_rfc_cards(channel=ch, rfcs_path=rf, state_dir=_STATE)
    assert r["rebuilt"] == 1 and "RFC-1" in ch._pending_rfc, (r, ch._pending_rfc)


# ── ۵: consumed/denied/merged not rebuilt ───────────────────────────────────────
def t_decided_rfc_not_rebuilt():
    _env()
    rf = _rfcs("t5", [{"rfc_id": "RFC-M", "status": "human-merge"},
                      {"rfc_id": "RFC-D", "status": "human-deny"},
                      {"rfc_id": "RFC-S", "status": "submitted"}])
    pcr.persist_rfc_verdict(state_dir=_STATE, rfc_id="RFC-S", verdict="denied")  # قبلاً رأی خورده
    ch = _Chan()
    r = pcr.rebuild_rfc_cards(channel=ch, rfcs_path=rf, state_dir=_STATE)
    assert r["rebuilt"] == 0, f"decided/consumed نباید بازسازی شوند: {ch._pending_rfc}"


# ── ۶: double boot → no duplicate ───────────────────────────────────────────────
def t_double_boot_no_dup():
    _env()
    db = _chrono("t6", [("fx-6", "releasable", "ch6", "pay", "t6", _FUTURE, 5.0)])
    ch1 = _Chan()
    assert pcr.rebuild_money_cards(channel=ch1, chrono_db_path=db, owner=_OWNER, state_dir=_STATE)["rebuilt"] == 1
    ch2 = _Chan()   # «restart دوم» — همان state_dir
    r2 = pcr.rebuild_money_cards(channel=ch2, chrono_db_path=db, owner=_OWNER, state_dir=_STATE)
    assert r2["rebuilt"] == 0, f"بوتِ دوم نباید کارتِ تکراری بسازد: {r2}"


# ── ۷: STOP/HALT → no action (only metadata) ────────────────────────────────────
def t_halt_metadata_only_no_action():
    _env()
    db = _chrono("t7", [("fx-7", "pending", "ch7", "pay", "t7", _FUTURE, 8.0)])
    ch = _Chan()
    r = pcr.rebuild_money_cards(channel=ch, chrono_db_path=db, owner=_OWNER, state_dir=_STATE, halted=True)
    assert r["rebuilt"] == 1 and r["halted"] is True
    assert "fx-7" in ch._pending, "metadata باید بازسازی شود"
    assert ch.sent == [], "زیرِ HALT هیچ کارتی ارسال/action نشود (فقط metadata)"


# ── extra: terminal/in-flight never re-presented ────────────────────────────────
def t_terminal_and_inflight_skipped():
    _env()
    db = _chrono("t8", [("s", "settled", "c", "pay", "t", _FUTURE, 1),
                        ("x", "EXECUTING", "c", "pay", "t", _FUTURE, 1),
                        ("r", "RECONCILE_REQUIRED", "c", "pay", "t", _FUTURE, 1),
                        ("f", "FAILED_SAFE", "c", "pay", "t", _FUTURE, 1)])
    ch = _Chan()
    r = pcr.rebuild_money_cards(channel=ch, chrono_db_path=db, owner=_OWNER, state_dir=_STATE)
    assert r["rebuilt"] == 0 and ch._pending == {}, "terminal/EXECUTING/RECONCILE هرگز re-present نشوند"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱] pending money card restart", t_money_card_rebuilt),
        ("[۲] binding mismatch/swap reject", t_binding_mismatch_rejected),
        ("[۳] old-token replay reject", t_old_token_replay_rejected),
        ("[۴] pending RFC restart", t_rfc_card_rebuilt),
        ("[۵] consumed/denied/merged not rebuilt", t_decided_rfc_not_rebuilt),
        ("[۶] double boot no duplicate", t_double_boot_no_dup),
        ("[۷] STOP/HALT no action (metadata only)", t_halt_metadata_only_no_action),
        ("[extra] terminal/in-flight never re-presented", t_terminal_and_inflight_skipped),
    ])
    sys.exit(1 if failed else 0)
