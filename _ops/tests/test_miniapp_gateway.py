#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_gateway â€” Ø¯ÛŒÙˆØ§Ø±Ù 8774 Ù Mini App (PLAN-T4 Â§Û²/Â§Ûµ).

    Ø¯ÛŒÙˆØ§Ø± Ù‚Ø¨Ù„ Ø§Ø² Ø¯Ø§Ø¯Ù‡: initData Ù Ù…Ø¹ØªØ¨Ø± (Ø§Ù„Ú¯ÙˆØ±ÛŒØªÙ…Ù ÙˆØ§Ù‚Ø¹ÛŒÙ HMAC Ø¨Ø§ ØªÙˆÚ©Ù†Ù ØªØ³ØªÛŒ)
    200 Ù…ÛŒâ€ŒÚ¯ÛŒØ±Ø¯Ø› hash Ù Ø¯Ø³ØªÚ©Ø§Ø±ÛŒâ€ŒØ´Ø¯Ù‡ / auth_date Ù Ú©Ù‡Ù†Ù‡ / Ú©Ø§Ø±Ø¨Ø±Ù ØºÛŒØ±Ù…Ø§Ù„Ú© /
    Ù†Ø¨ÙˆØ¯Ù Ù‡Ø¯Ø± = 403 Ù Ø®Ø§Ù„ÛŒØ› Ù‡Ø± Ù…ØªØ¯Ù ØºÛŒØ± GET = 405Ø› STOP-MINIAPP = 503Ø›
    Ùˆ secret Ù‡Ø±Ú¯Ø² Ø¯Ø± Ù‡ÛŒÚ† Ø¨Ø¯Ù†Ù‡â€ŒØ§ÛŒ Ø¸Ø§Ù‡Ø± Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯ (Ø¯ÙØ§Ø¹Ù Ø¯ÙˆÙ„Ø§ÛŒÙ‡Ù” redaction).

    handler Ù…Ø³ØªÙ‚ÛŒÙ… Ø¯Ø±Ø§ÛŒÙˆ Ù…ÛŒâ€ŒØ´ÙˆØ¯ (ØªØ§Ø¨Ø¹Ù Ø®Ø§Ù„ØµÙ handle) â€” Ù‡ÛŒÚ† Ø³Ø±ÙˆØ±/Ø´Ø¨Ú©Ù‡â€ŒØ§ÛŒ.
"""
import hashlib
import hmac
import json
import os
import sys
import tempfile
import urllib.parse
from pathlib import Path

import harness

ENV = harness.setup("miniapp-gateway")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import miniapp_gateway as mg  # noqa: E402

NOW = 1_785_400_000.0
# ØªÙˆÚ©Ù†Ù **ØªØ³ØªÛŒ/Ø¬Ø¹Ù„ÛŒ** â€” Ø¹Ù…Ø¯Ø§Ù‹ Ù‡Ù…â€ŒØ´Ú©Ù„Ù ØªÙˆÚ©Ù†Ù ÙˆØ§Ù‚Ø¹ÛŒ ØªØ§ Ø§Ù„Ú¯ÙˆÛŒ redaction Ø¨Ú¯ÛŒØ±Ø¯Ø´.
TOKEN = "123456789:AA" + "x" * 32
OWNER = "777"

os.environ["TG_CENTER_BOT_TOKEN"] = TOKEN
os.environ["TELEGRAM_OWNER_CHAT_ID"] = OWNER


def _init_data(user_id=777, auth_date=NOW - 10, token=TOKEN, tamper=False,
               extra=None):
    data = {"auth_date": str(int(auth_date)),
            "query_id": "AAE-test",
            "user": json.dumps({"id": user_id, "first_name": "ari"},
                               ensure_ascii=False)}
    if extra:
        data.update(extra)
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode("utf-8"),
                      hashlib.sha256).digest()
    h = hmac.new(secret, dcs.encode("utf-8"), hashlib.sha256).hexdigest()
    if tamper:
        h = ("0" if h[0] != "0" else "1") + h[1:]
    data["hash"] = h
    return urllib.parse.urlencode(data)


def _fetch(body=b'{"money":{"month_aud":1}}', ctype="application/json"):
    calls = []

    def fn(path):
        calls.append(path)
        return 200, body, ctype

    fn._calls = calls
    return fn


def _stop_file() -> Path:
    import opslib
    return Path(opslib.OPS) / mg.STOP_NAME


# â”€â”€ Ø¯ÛŒÙˆØ§Ø±Ù Â§Û² â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def t_valid_initdata_gets_200_and_the_upstream_body():
    fn = _fetch()
    st, body, _ = mg.handle("GET", "/api/miniapp",
                            {"X-Tg-Init-Data": _init_data()},
                            fetch_fn=fn, now=NOW)
    assert st == 200, st
    assert b"month_aud" in body, body
    assert fn._calls == ["/api/miniapp"]


def t_extra_fields_still_validate_sorting_is_correct():
    st, _, _ = mg.handle("GET", "/api/miniapp",
                         {"X-Tg-Init-Data": _init_data(
                             extra={"chat_type": "sender", "start_param": "z"})},
                         fetch_fn=_fetch(), now=NOW)
    assert st == 200, st


def t_a_tampered_hash_is_403_with_an_empty_body():
    fn = _fetch()
    st, body, _ = mg.handle("GET", "/api/miniapp",
                            {"X-Tg-Init-Data": _init_data(tamper=True)},
                            fetch_fn=fn, now=NOW)
    assert st == 403 and body == b"", (st, body)
    assert not fn._calls, "Ø¯Ø±Ø®ÙˆØ§Ø³ØªÙ Ø±Ø¯Ø´Ø¯Ù‡ Ø¨Ù‡ Ø¨Ø§Ù„Ø§Ø¯Ø³ØªÛŒ Ø±Ø³ÛŒØ¯"


def t_a_stale_auth_date_is_replay_and_403():
    st, body, _ = mg.handle("GET", "/api/miniapp",
                            {"X-Tg-Init-Data": _init_data(auth_date=NOW - 400)},
                            fetch_fn=_fetch(), now=NOW)
    assert st == 403 and body == b"", (st, body)


def t_a_non_owner_user_is_403_even_with_a_valid_hash():
    st, body, _ = mg.handle("GET", "/api/miniapp",
                            {"X-Tg-Init-Data": _init_data(user_id=888)},
                            fetch_fn=_fetch(), now=NOW)
    assert st == 403 and body == b"", (st, body)


def t_a_missing_or_empty_header_is_403():
    for headers in ({}, {"X-Tg-Init-Data": ""}):
        st, body, _ = mg.handle("GET", "/api/miniapp", headers,
                                fetch_fn=_fetch(), now=NOW)
        assert st == 403 and body == b"", (headers, st)


def t_a_wrong_token_key_direction_would_fail():
    """Ú©Ù„ÛŒØ¯Ù HMAC = HMAC(key=b"WebAppData", msg=token) â€” Ø¬Ù‡ØªÙ Ø¨Ø±Ø¹Ú©Ø³ Ø±Ø¯ Ø´ÙˆØ¯."""
    wrong_secret = hmac.new(TOKEN.encode(), b"WebAppData",
                            hashlib.sha256).digest()
    data = {"auth_date": str(int(NOW - 5)), "user": json.dumps({"id": 777})}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    data["hash"] = hmac.new(wrong_secret, dcs.encode(),
                            hashlib.sha256).hexdigest()
    st, _, _ = mg.handle("GET", "/api/miniapp",
                         {"X-Tg-Init-Data": urllib.parse.urlencode(data)},
                         fetch_fn=_fetch(), now=NOW)
    assert st == 403, st


# VQ-GATEWAY-DRIFT-BLIND-001 (برشِ ۳، آیتمِ ۵): organism/center/cortex/live
# همه snapshot_boot را صدا می‌زنند تا flag_drift.probe_all رانشِ فلگِ آن پروسه
# را ببیند؛ gateway تنها limb ِ بدونش بود. main() سرور را بلاک می‌کند (serve_
# forever)، پس اینجا فقط سازه سنجیده می‌شود -- همان الگویِ compare_digest پایین.
def t_main_snapshots_boot_flags_like_every_other_limb():
    src = Path(mg.__file__).read_text("utf-8")
    i = src.find("def main(")
    assert i >= 0
    seg = src[i:i + 2000]
    assert "flag_drift" in seg and "snapshot_boot" in seg, \
        "main() باید flag_drift.snapshot_boot('miniapp-gateway') را صدا بزند"


def t_compare_digest_is_used_no_timing_leak():
    src = Path(mg.__file__).read_text("utf-8")
    assert "compare_digest" in src, "Ù…Ù‚Ø§ÛŒØ³Ù‡Ù” hash Ø¨Ø¯ÙˆÙ†Ù Ø¶Ø¯Ù-timing"


# â”€â”€ Ø³Ø·Ø­Ù ÙÙ‚Ø·â€ŒØ®ÙˆØ§Ù†Ø¯Ù†ÛŒ Ùˆ Ù…Ø³ÛŒØ±Ù‡Ø§ÛŒ Ø¨Ø³ØªÙ‡ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def t_every_non_get_method_is_405():
    for m in ("POST", "PUT", "DELETE", "PATCH"):
        st, _, _ = mg.handle(m, "/api/miniapp",
                             {"X-Tg-Init-Data": _init_data()},
                             fetch_fn=_fetch(), now=NOW)
        assert st == 405, (m, st)


def t_unknown_paths_are_404():
    for p in ("/", "/ops", "/api/live", "/api/action", "/x"):
        st, _, _ = mg.handle("GET", p, {"X-Tg-Init-Data": _init_data()},
                             fetch_fn=_fetch(), now=NOW)
        assert st == 404, (p, st)
def t_actions_post_requires_owner_auth_and_blocks_without_it():
    body = json.dumps({"action": "lead.create", "payload": {"handle": "@x"}}).encode("utf-8")
    st, payload, _ = mg.handle("POST", "/api/actions", {"_body": body}, fetch_fn=_fetch(), now=NOW)
    assert st == 403, (st, payload)
    assert b"owner_auth_required" in payload
def t_owner_can_create_local_lead_but_onlyfans_automation_is_blocked():
    with tempfile.TemporaryDirectory() as d:
        old = {k: os.environ.get(k) for k in ("OCTOPUS_OPS_RUNTIME_DIR", "OCTOPUS_OPS_DB_PATH", "OCTOPUS_OPS_AUDIT_PATH", "OCTOPUS_OPS_IDEMPOTENCY_PATH")}
        try:
            os.environ["OCTOPUS_OPS_RUNTIME_DIR"] = d
            os.environ["OCTOPUS_OPS_DB_PATH"] = str(Path(d) / "ops.sqlite3")
            os.environ["OCTOPUS_OPS_AUDIT_PATH"] = str(Path(d) / "audit.jsonl")
            os.environ["OCTOPUS_OPS_IDEMPOTENCY_PATH"] = str(Path(d) / "idem.sqlite3")
            headers = {"X-Tg-Init-Data": _init_data(), "_body": json.dumps({"action":"lead.create","payload":{"handle":"@demo","platform":"onlyfans","stage":"new"}}).encode("utf-8")}
            st, payload, _ = mg.handle("POST", "/api/actions", headers, fetch_fn=_fetch(), now=NOW)
            res = json.loads(payload)
            assert st == 200 and res["ok"] and res["lead_id"].startswith("lead_"), (st, res)
            headers["_body"] = json.dumps({"action":"onlyfans.auto_dm","payload":{"handle":"@demo"}}).encode("utf-8")
            st2, payload2, _ = mg.handle("POST", "/api/actions", headers, fetch_fn=_fetch(), now=NOW)
            res2 = json.loads(payload2)
            assert st2 == 200 and res2["status"] == "BLOCKED" and res2["reason"] == "external_platform_automation_forbidden", res2
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


# Slice 3, item 6: real browsers send header field names lowercase over the
# wire, and _Handler._run downgrades headers to a plain (case-sensitive) dict
# on POST only. A dict built with the exact request-line casing is what
# _Handler._run actually hands to handle() for /api/actions -- simulate that
# here instead of the idealized "X-Tg-Init-Data" dict every other test uses.
def t_post_auth_works_with_lowercase_header_like_a_real_browser_sends():
    with tempfile.TemporaryDirectory() as d:
        old = {k: os.environ.get(k) for k in
               ("OCTOPUS_OPS_RUNTIME_DIR", "OCTOPUS_OPS_DB_PATH",
                "OCTOPUS_OPS_AUDIT_PATH", "OCTOPUS_OPS_IDEMPOTENCY_PATH")}
        try:
            os.environ["OCTOPUS_OPS_RUNTIME_DIR"] = d
            os.environ["OCTOPUS_OPS_DB_PATH"] = str(Path(d) / "ops.sqlite3")
            os.environ["OCTOPUS_OPS_AUDIT_PATH"] = str(Path(d) / "audit.jsonl")
            os.environ["OCTOPUS_OPS_IDEMPOTENCY_PATH"] = str(Path(d) / "idem.sqlite3")
            body = json.dumps({"action": "lead.create", "payload": {"handle": "@x"}}).encode("utf-8")
            headers = {"x-tg-init-data": _init_data(), "_body": body}
            st, payload, _ = mg.handle("POST", "/api/actions", headers, fetch_fn=_fetch(), now=NOW)
            res = json.loads(payload)
            # Tightened past "not 403": a swallowed exception (e.g. a blocked
            # live-state write) also degrades to a non-403 status, so this
            # must confirm the action actually ran, not just that auth passed.
            assert st == 200 and res.get("ok") and str(res.get("lead_id", "")).startswith("lead_"), \
                (st, res)
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


# VQ-OPEN-READ-API-001 (برشِ ۳، آیتمِ ۱): این ۱۱ مسیر قبلاً بی‌قیدوشرط باز
# بودند مگر یک فلگِ اضافه صریحاً روشن می‌شد. حالا برعکس: بسته مگر صریحاً باز شود.
def t_read_api_paths_require_owner_auth_by_default():
    os.environ.pop(mg.READ_GATE_FLAG, None)   # پیش‌فرض — env دست‌نخورده
    assert mg.read_gate_enabled() is True, "پیش‌فرض باید بسته باشد"
    st, body, _ = mg.handle("GET", "/api/approvals", {}, fetch_fn=_fetch(), now=NOW)
    assert st == 403, (st, body)


def t_read_api_paths_can_be_explicitly_reopened():
    os.environ[mg.READ_GATE_FLAG] = "0"
    try:
        assert mg.read_gate_enabled() is False
    finally:
        os.environ.pop(mg.READ_GATE_FLAG, None)


def t_get_header_is_case_insensitive_both_directions():
    assert mg._get_header({"X-Tg-Init-Data": "v1"}, "X-Tg-Init-Data") == "v1"
    assert mg._get_header({"x-tg-init-data": "v2"}, "X-Tg-Init-Data") == "v2"
    assert mg._get_header({"X-TG-INIT-DATA": "v3"}, "X-Tg-Init-Data") == "v3"
    assert mg._get_header({}, "X-Tg-Init-Data") == ""


def t_the_page_serves_without_initdata_and_injects_the_header_snippet():
    # /miniapp must serve the committed read-only cockpit shell, not the old
    # upstream legacy placeholder dashboard. No initData is required for the
    # shell; data/action APIs stay gated/read-only separately.
    fn = _fetch(body=b"<html><body>legacy-shell</body></html>", ctype="text/html")
    st, body, ctype = mg.handle("GET", "/miniapp", {}, fetch_fn=fn, now=NOW)
    assert st == 200, (st, body[:80])
    assert b"Octopus Cockpit" in body, body[:160]
    for tab in (b"Outbound", b"Approvals", b"Legs", b"Value", b"UI Registry", b"Truth"):
        assert tab in body, tab
    assert b"legacy-shell" not in body, "legacy placeholder was served instead of cockpit"
    assert b"X-Tg-Init-Data" in body, "initData injection snippet missing"
    assert body.index(b"X-Tg-Init-Data") < body.index(b"</body>")
    assert fn._calls == [], "static cockpit shell must not proxy to legacy 8773"


# â”€â”€ Ú©Ù„ÛŒØ¯Ù Ú©Ø´ØªØ§Ø± + ÙÙ„Ú¯ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def t_stop_miniapp_kills_every_request_with_503():
    sf = _stop_file()
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text("test", "utf-8")
    try:
        for m, p in (("GET", "/miniapp"), ("GET", "/api/miniapp"), ("POST", "/x")):
            st, body, _ = mg.handle(m, p, {"X-Tg-Init-Data": _init_data()},
                                    fetch_fn=_fetch(), now=NOW)
            assert st == 503 and body == b"", (m, p, st)
    finally:
        sf.unlink()


# VQ-PORT-COLLISION-001 (برشِ ۳، آیتمِ ۲): قبلاً وقتی bind شکست می‌خورد main()
# فقط print می‌کرد و ۰ برمی‌گرداند -- بی‌صدا، حتی وقتی شنوندهٔ اشغال‌کننده خودِ
# gateway نبود (تونلِ عمومی بی‌خبر به سرویسِ اشتباه می‌رسید). حالا باید alert کند.
def t_bind_failure_alerts_instead_of_silent_exit():
    import importlib
    import socket as _socket
    _prev_port_env = os.environ.get("OCTOPUS_MINIAPP_PORT")
    blocker = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))   # OS-assigned free port, isolated from prod 8774
    blocker.listen(1)
    real_port = blocker.getsockname()[1]
    try:
        os.environ["OCTOPUS_MINIAPP_PORT"] = str(real_port)
        importlib.reload(mg)
        os.environ[mg.FLAG] = "1"
        sf = _stop_file()
        if sf.exists():
            sf.unlink()
        try:
            rc = mg.main()
        finally:
            blocker.close()
            os.environ.pop(mg.FLAG, None)
        assert rc == 0, rc
        import opslib
        assert opslib.ALERTS_MD.exists(), "bind-failure باید alert بنویسد"
        assert f"{real_port}" in opslib.ALERTS_MD.read_text(encoding="utf-8")
    finally:
        if _prev_port_env is None:
            os.environ.pop("OCTOPUS_MINIAPP_PORT", None)
        else:
            os.environ["OCTOPUS_MINIAPP_PORT"] = _prev_port_env
        importlib.reload(mg)


def t_the_flag_is_default_off():
    os.environ.pop(mg.FLAG, None)
    assert not mg.enabled()
    os.environ[mg.FLAG] = "1"
    assert mg.enabled()
    os.environ.pop(mg.FLAG, None)


# â”€â”€ Ø¶Ø¯Ù†Ø´Øª: secret Ù‡Ø±Ú¯Ø² Ø¯Ø± Ù‡ÛŒÚ† Ø¨Ø¯Ù†Ù‡â€ŒØ§ÛŒ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def t_the_bot_token_never_appears_in_any_response_body():
    leaky = _fetch(body=json.dumps({"note": f"token={TOKEN}"}).encode())
    st, body, _ = mg.handle("GET", "/api/miniapp",
                            {"X-Tg-Init-Data": _init_data()},
                            fetch_fn=leaky, now=NOW)
    assert st == 200
    assert TOKEN.encode() not in body, "ØªÙˆÚ©Ù† Ø§Ø² Ù¾Ø§Ø³Ù redaction Ø±Ø¯ Ø´Ø¯!"
    # ØµÙØ­Ù‡Ù” Ø´ÙÙ„ Ù‡Ù… (Ø­ØªÛŒ Ø§Ú¯Ø± Ø¨Ø§Ù„Ø§Ø¯Ø³ØªÛŒ Ø¢Ù„ÙˆØ¯Ù‡ Ø¨Ø§Ø´Ø¯) ØªÙˆÚ©Ù† Ø±Ø§ echo Ù†Ù…ÛŒâ€ŒÚ©Ù†Ø¯
    st2, body2, _ = mg.handle("GET", "/miniapp", {},
                              fetch_fn=_fetch(b"<body>x</body>"), now=NOW)
    assert TOKEN.encode() not in body2


def t_the_module_never_writes_the_token_to_disk_or_logs():
    src = Path(mg.__file__).read_text("utf-8")
    assert "TG_CENTER_BOT_TOKEN" in src
    # Â«urlopenÂ» Ù proxy Ù…Ø¬Ø§Ø² Ø§Ø³ØªØ› Ù†ÙˆØ´ØªÙ†Ù ÙØ§ÛŒÙ„/Ù„Ø§Ú¯ Ù†Ù‡.
    for bad in ("write_text", "write_bytes", "with open", "logging"):
        assert bad not in src, f"Ù…Ø³ÛŒØ±Ù Ù†ÙˆØ´ØªÙ†Ù Ø¯ÛŒØ³Ú© Ø¯Ø± gateway: {bad}"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.SELF_OPS).lower()
    assert not str(_stop_file()).lower().startswith(live), _stop_file()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'âœ…' if not failed else 'âŒ'} test_miniapp_gateway: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
