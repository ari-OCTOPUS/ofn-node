#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-01..T-24 unit pins for AGI loop closure. Not live send. Not registered until run_all append."""
from __future__ import annotations

import ast
import hashlib
import hmac
import json
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))
sys.path.insert(0, str(_OPS / "cortex"))
sys.path.insert(0, str(_OPS / "budget"))

from loops import doctor_timeout, families, ladder, telegram_organ  # noqa: E402
from telegram_center.self_bot_filter import is_self_bot_update  # noqa: E402


def t_01_twelve_families():
    assert len(families.FAMILIES) == 12


def t_02_twenty_four_discovery():
    assert len(families.DISCOVERY) == 24


def t_03_l6_needs_both_surfaces():
    assert ladder.require_surfaces("/a", "/b") is True
    assert ladder.require_surfaces("UNROUTED", "/b") is False


def t_04_budget_on_every_family_card():
    for fam in families.FAMILIES:
        assert fam["family_id"].startswith("AGI-")
        assert int(fam["sla_s"]) > 0


def t_05_initdata_tamper_rejected():
    from miniapp_gateway import validate_init_data  # noqa: WPS433
    token = "123456:FAKESECRET_k4l5m6n7o8p9q0r1s2t3"
    user = json.dumps({"id": 1}, separators=(",", ":"))
    data = {"auth_date": "1000", "user": user, "query_id": "AA"}
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    good = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    qs = urlencode({**data, "hash": good})
    assert validate_init_data(qs, bot_token=token, owner_id=1, now=1001.0) is not None
    bad = urlencode({**data, "hash": "0" * 64})
    assert validate_init_data(bad, bot_token=token, owner_id=1, now=1001.0) is None


def t_06_hmac_key_is_webappdata_then_token():
    src = (_OPS / "telegram_center" / "miniapp_gateway.py").read_text(encoding="utf-8")
    assert 'hmac.new(b"WebAppData"' in src
    assert "compare_digest" in src


def t_07_outbox_dry_run_default():
    td = Path(tempfile.mkdtemp(prefix="t07-"))
    organ = telegram_organ.TelegramOrgan(td, allowlist={1}, live=False)
    r = organ.enqueue_digest([{"loop_id": "x", "class": "ORPHAN", "title": "t"}],
                             chat_id=1, force=True)
    assert r["sent"] is False
    assert r["status"] == "dry_run"


def t_08_restart_no_resend_update_id():
    td = Path(tempfile.mkdtemp(prefix="t08-"))
    organ = telegram_organ.TelegramOrgan(td, allowlist={1}, live=False)
    u = {"update_id": 7, "message": {"text": "hi", "chat": {"id": 1}, "from": {"id": 1}}}
    assert organ.ingest_update(u)["status"] == "accepted"
    organ2 = telegram_organ.TelegramOrgan(td, allowlist={1}, live=False)
    assert organ2.ingest_update(u)["status"] == "duplicate"


def t_09_business_retry_separate_from_delivery():
    src = (_OPS / "loops" / "telegram_organ.py").read_text(encoding="utf-8")
    assert "delivery_retry" in src and "business_retry" in src


def t_10_owner_visible_is_l6():
    assert ladder.RUNGS[-1] == "owner_visible"


def t_11_can_close_false_without_miniapp():
    lv = {r: True for r in ladder.RUNGS}
    assert ladder.require_surfaces("/status", "UNROUTED") is False


def t_12_self_bot_message_skipped():
    assert is_self_bot_update({"message": {"from": {"id": 1, "is_bot": True}}}) is True
    assert is_self_bot_update({"message": {"from": {"id": 2, "is_bot": False}}}) is False
    assert is_self_bot_update({"callback_query": {"from": {"id": 3, "is_bot": True}}}) is False


def t_13_doctor_timeout_on_copy_not_live_path():
    live = Path(r"F:/backup/OCTOPUS-DOCTOR/90-_meta/state/missions.json")
    raw = json.loads(live.read_text(encoding="utf-8"))
    updated, log = doctor_timeout.expire_open_missions(raw, now=9e12, timeout_s=1)
    assert isinstance(updated, list)
    still = json.loads(live.read_text(encoding="utf-8"))
    assert still[0]["mission_id"] == raw[0]["mission_id"]


def t_14_improve_reads_calibration():
    src = (_OPS / "cortex" / "improve.py").read_text(encoding="utf-8")
    assert "calibration-latest.json" in src


def t_15_no_confidence_assign_0_4():
    src = (_OPS / "doctor" / "self_knowledge.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = [a.id for a in node.targets if isinstance(a, ast.Name)]
            if "confidence" in names and isinstance(node.value, ast.Constant):
                assert node.value.value != 0.4


def t_16_ema_present():
    assert "_accuracy_ema" in (_OPS / "doctor" / "self_knowledge.py").read_text(encoding="utf-8")


def t_17_center_never_calls_getupdates_literal():
    src = (_OPS / "telegram_center" / "center.py").read_text(encoding="utf-8")
    assert "هرگز getUpdates صدا نمی‌زند" in src


def t_18_no_setwebhook_in_center():
    src = (_OPS / "telegram_center" / "center.py").read_text(encoding="utf-8")
    assert "setWebhook" not in src


def t_19_doctor_pulse_tool_exists():
    assert (_OPS / "tools" / "doctor_pulse.py").is_file()


def t_20_approval_store_has_pending_api():
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import approval_store as aps  # noqa: WPS433
    s = aps.summary()
    assert set(s) >= {"pending", "approved", "rejected", "done"}


def t_21_self_bot_filter_imported_by_center():
    src = (_OPS / "telegram_center" / "center.py").read_text(encoding="utf-8")
    assert "self_bot_filter" in src


def t_22_forty_two_loops_one_digest():
    td = Path(tempfile.mkdtemp(prefix="t22-"))
    organ = telegram_organ.TelegramOrgan(td, allowlist={1}, live=False)
    loops = [{"loop_id": f"L{i}", "class": "ORPHAN", "title": str(i)} for i in range(42)]
    d = organ.enqueue_digest(loops, chat_id=1, force=True)
    assert d["n_loops"] == 42 and d["coalesced"] == 39 and d["sent"] is False


def t_23_wave1_lock_readable():
    p = _OPS / "state" / "wave1" / "lock.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    assert "wave1_unlocked" in d
    assert "memory_writes" in d


def t_24_pass3_live_flag_is_explicit():
    grant = Path(r"F:/backup/02-DECISIONS/OWNER-GRANT-UNLOCK-AGI-LOCKS-2026-08-21.md")
    assert grant.is_file()
    body = grant.read_text(encoding="utf-8")
    assert "full_live" in body and "prod_write" in body


if __name__ == "__main__":
    failed = 0
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for n, f in tests:
        try:
            f()
            print(f"  OK  {n}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {n}: {type(e).__name__}: {e}")
    print(f"{len(tests) - failed}/{len(tests)}")
    sys.exit(1 if failed else 0)
