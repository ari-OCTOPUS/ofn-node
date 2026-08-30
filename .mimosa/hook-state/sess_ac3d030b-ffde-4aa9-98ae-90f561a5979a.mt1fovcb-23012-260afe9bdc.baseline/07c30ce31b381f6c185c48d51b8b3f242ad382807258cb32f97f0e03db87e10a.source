#!/usr/bin/env python3
"""test_channel_status.py — Task 2 (2026-07-24): writerِ زندهٔ channel-status.json.

رگرسیونِ اصلی: وقتی token+owner هست، وضعیتِ گزارش‌شدهٔ telegram دیگر روی
«stub(no-creds)/not-wired» نمی‌مانَد (فایل تا 2026-07-08 orphan/فریز بود).
ایزوله: tempdir mini-vault (harness)؛ صفر شبکه (http تزریقی)؛ صفر state واقعی.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("channel-status")

from approval_channel import TelegramApprovalChannel  # noqa: E402

SD = Path(ENV["ops"]) / "state"


def _stub_get(url, timeout):
    return {"ok": True, "result": []}


def _stub_post(url, body, timeout_s=10.0):
    return {"ok": True, "result": {}}


def _mk(token="123:testtoken", owner=777):
    return TelegramApprovalChannel(token=token, owner_chat_id=owner,
                                   http_get=_stub_get, http_post=_stub_post,
                                   state_dir=str(SD))


def _read():
    p = SD / "channel-status.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else {}


def t_a_wired_channel_writes_live_true():
    """token+owner → live=True و mode=long-poll — پایانِ عکسِ کهنهٔ not-wired."""
    ch = _mk()
    assert ch.wired
    assert ch._write_channel_status() is True
    d = _read()
    tg = d["channels"]["telegram"]
    assert tg["live"] is True, tg
    assert tg["mode"] == "long-poll(T-8)"
    assert "writer" in tg and "approval_channel" in tg["writer"]
    assert "required_env" not in tg          # وقتی وصل است، «نیاز» رندر نمی‌شود
    assert "testtoken" not in json.dumps(d)  # secret-guard: هیچ مقدارِ token در فایل


def t_b_unwired_reports_honest_stub():
    """بدونِ owner → wired=False → live=False + required_env (صادق، نه دروغِ سبز)."""
    ch = TelegramApprovalChannel(token="123:x", owner_chat_id=None,
                                 http_get=_stub_get, http_post=_stub_post,
                                 state_dir=str(SD))
    assert not ch.wired
    assert ch._write_channel_status() is True
    tg = _read()["channels"]["telegram"]
    assert tg["live"] is False
    assert tg["mode"] == "stub(no-creds)"
    assert "TELEGRAM_BOT_TOKEN" in tg.get("required_env", [])


def t_c_other_channels_preserved():
    """read-modify-write: entryهای snapshotِ دیگر (whatsapp/email) دست‌نخورده می‌مانند."""
    p = SD / "channel-status.json"
    p.write_text(json.dumps({"ts": "old", "channels": {
        "whatsapp": {"channel": "whatsapp", "live": False, "mode": "NotWiredStub"}}},
        ensure_ascii=False), "utf-8")
    ch = _mk()
    assert ch._write_channel_status() is True
    d = _read()
    assert d["channels"]["whatsapp"]["mode"] == "NotWiredStub"
    assert d["channels"]["telegram"]["live"] is True
    assert d["ts"] != "old"


def t_d_poll_once_refreshes_periodically():
    """poll_once مسیرِ کادنسی را می‌زند (بوت‌مستقل): _last_chstat=0 → refresh."""
    (SD / "channel-status.json").unlink(missing_ok=True)
    ch = _mk()
    ch._last_chstat = 0.0
    n = ch.poll_once()
    assert n == 0                             # هیچ update ای — ولی pulse+status نوشته شد
    assert _read()["channels"]["telegram"]["live"] is True


def t_e_corrupt_file_failsoft_rewrite():
    """فایلِ خراب → writer fail-soft بازنویسی می‌کند (هرگز poll را نمی‌کشد)."""
    (SD / "channel-status.json").write_text("{corrupt", "utf-8")
    ch = _mk()
    assert ch._write_channel_status() is True
    assert _read()["channels"]["telegram"]["live"] is True


if __name__ == "__main__":
    import sys as _s
    _s.exit(harness.run([
        ("Task2: token+owner → live=True (پایانِ not-wiredِ دروغ)", t_a_wired_channel_writes_live_true),
        ("Task2: بی‌creds → stub صادق + required_env", t_b_unwired_reports_honest_stub),
        ("Task2: کانال‌های snapshotِ دیگر preserved", t_c_other_channels_preserved),
        ("Task2: poll_once کادنسی refresh می‌کند", t_d_poll_once_refreshes_periodically),
        ("Task2: فایلِ خراب → بازنویسیِ fail-soft", t_e_corrupt_file_failsoft_rewrite),
    ]))
