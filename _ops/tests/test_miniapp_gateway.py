#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_gateway — دیوارِ 8774 ِ Mini App (PLAN-T4 §۲/§۵).

    دیوار قبل از داده: initData ِ معتبر (الگوریتمِ واقعیِ HMAC با توکنِ تستی)
    200 می‌گیرد؛ hash ِ دستکاری‌شده / auth_date ِ کهنه / کاربرِ غیرمالک /
    نبودِ هدر = 403 ِ خالی؛ هر متدِ غیر GET = 405؛ STOP-MINIAPP = 503؛
    و secret هرگز در هیچ بدنه‌ای ظاهر نمی‌شود (دفاعِ دولایهٔ redaction).

    handler مستقیم درایو می‌شود (تابعِ خالصِ handle) — هیچ سرور/شبکه‌ای.
"""
import hashlib
import hmac
import json
import os
import sys
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
# توکنِ **تستی/جعلی** — عمداً هم‌شکلِ توکنِ واقعی تا الگوی redaction بگیردش.
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


# ── دیوارِ §۲ ───────────────────────────────────────────────────────────────
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
    assert not fn._calls, "درخواستِ ردشده به بالادستی رسید"


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
    """کلیدِ HMAC = HMAC(key=b"WebAppData", msg=token) — جهتِ برعکس رد شود."""
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


def t_compare_digest_is_used_no_timing_leak():
    src = Path(mg.__file__).read_text("utf-8")
    assert "compare_digest" in src, "مقایسهٔ hash بدونِ ضدِ-timing"


# ── سطحِ فقط‌خواندنی و مسیرهای بسته ─────────────────────────────────────────
def t_every_non_get_method_is_405():
    for m in ("POST", "PUT", "DELETE", "PATCH"):
        st, _, _ = mg.handle(m, "/api/miniapp",
                             {"X-Tg-Init-Data": _init_data()},
                             fetch_fn=_fetch(), now=NOW)
        assert st == 405, (m, st)


def t_unknown_paths_are_404():
    for p in ("/", "/ops", "/api/live", "/api/ops", "/api/action", "/x"):
        st, _, _ = mg.handle("GET", p, {"X-Tg-Init-Data": _init_data()},
                             fetch_fn=_fetch(), now=NOW)
        assert st == 404, (p, st)


def t_the_page_serves_without_initdata_and_injects_the_header_snippet():
    fn = _fetch(body=b"<html><body>shell</body></html>", ctype="text/html")
    st, body, ctype = mg.handle("GET", "/miniapp", {}, fetch_fn=fn, now=NOW)
    assert st == 200 and b"shell" in body, (st, body[:80])
    assert b"X-Tg-Init-Data" in body, "اسنیپتِ initData تزریق نشد"
    assert body.index(b"X-Tg-Init-Data") < body.index(b"</body>")


# ── کلیدِ کشتار + فلگ ───────────────────────────────────────────────────────
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


def t_the_flag_is_default_off():
    os.environ.pop(mg.FLAG, None)
    assert not mg.enabled()
    os.environ[mg.FLAG] = "1"
    assert mg.enabled()
    os.environ.pop(mg.FLAG, None)


# ── ضدنشت: secret هرگز در هیچ بدنه‌ای ───────────────────────────────────────
def t_the_bot_token_never_appears_in_any_response_body():
    leaky = _fetch(body=json.dumps({"note": f"token={TOKEN}"}).encode())
    st, body, _ = mg.handle("GET", "/api/miniapp",
                            {"X-Tg-Init-Data": _init_data()},
                            fetch_fn=leaky, now=NOW)
    assert st == 200
    assert TOKEN.encode() not in body, "توکن از پاسِ redaction رد شد!"
    # صفحهٔ شِل هم (حتی اگر بالادستی آلوده باشد) توکن را echo نمی‌کند
    st2, body2, _ = mg.handle("GET", "/miniapp", {},
                              fetch_fn=_fetch(b"<body>x</body>"), now=NOW)
    assert TOKEN.encode() not in body2


def t_the_module_never_writes_the_token_to_disk_or_logs():
    src = Path(mg.__file__).read_text("utf-8")
    assert "TG_CENTER_BOT_TOKEN" in src
    # «urlopen» ِ proxy مجاز است؛ نوشتنِ فایل/لاگ نه.
    for bad in ("write_text", "write_bytes", "with open", "logging"):
        assert bad not in src, f"مسیرِ نوشتنِ دیسک در gateway: {bad}"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops").lower()
    assert not str(_stop_file()).lower().startswith(live), _stop_file()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_miniapp_gateway: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
