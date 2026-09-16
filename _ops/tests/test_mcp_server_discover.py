#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mcp_server_discover.py — `server/discover` (spec 2026-07-28) روی ترابردِ stdio.

چرا (۲۰۲۶-۰۸-۲۳): رویزیونِ 2026-07-28 می‌گوید سرورها **MUST** این RPC را داشته
باشند، و برای stdio نقشِ «backward-compatibility probe» را بازی می‌کند —
کلاینتِ dual-era اول `server/discover` می‌فرستد و «روی هر خطایی که خطای
شناخته‌شدهٔ modern نباشد» به `initialize` برمی‌گردد.
مرجع: https://modelcontextprotocol.io/specification/2026-07-28/server/discover

قیدِ سختِ این batch: **additive**. مسیرِ `initialize` نه حذف می‌شود نه ضعیف —
کلاینتِ ثبت‌شده در `.mcp.json` هنوز legacy است.

ناوردیِ صداقت که اینجا قفل می‌شود: `supportedVersions` **نباید** `2026-07-28`
را اعلام کند. این سرور هیچ الزامِ modern را پیاده نکرده (نه `_meta`، نه MRTR،
نه `resultType` روی بقیهٔ نتایج، نه `subscriptions/listen`). طبقِ ماتریسِ
سازگاریِ خودِ اسپک، ادعای دروغ باعث می‌شود کلاینت سرور را modern تشخیص دهد و
بعد هر درخواستِ modern شکست بخورد — یعنی همان probe را می‌شکند.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("mcp-server-discover")
_OPS = harness.SELF_OPS

sys.path.insert(0, str(_OPS / "octopus_mcp"))
import server as mcp  # noqa: E402

SERVER_PATH = _OPS / "octopus_mcp" / "server.py"


def _rpc(method: str, params: dict | None = None, mid=1) -> dict:
    """فراخوانیِ درون‌پروسه‌ای از خودِ dispatcher."""
    msg = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        msg["params"] = params
    return mcp._handle(msg)


# ---------------------------------------------------------------- supported versions

def t_discover_reports_supported_versions():
    r = _rpc("server/discover")
    assert r is not None, "server/discover پاسخ نداد"
    res = r["result"]
    assert res["supportedVersions"] == list(mcp.SUPPORTED_PROTOCOL_VERSIONS)
    assert mcp.PROTOCOL_VERSION in res["supportedVersions"]


def t_discover_does_not_falsely_claim_modern_revision():
    """ناوردیِ صداقت — گرانبهاترین assert این فایل."""
    res = _rpc("server/discover")["result"]
    assert "2026-07-28" not in res["supportedVersions"], (
        "سرور نسخهٔ modern را اعلام کرد در حالی که هیچ الزامِ آن را پیاده "
        "نکرده — این تشخیصِ era در کلاینتِ dual-era را می‌شکند")


def t_discover_result_type_is_complete():
    assert _rpc("server/discover")["result"]["resultType"] == "complete"


# ---------------------------------------------------------------- capabilities

def t_discover_reports_capabilities_matching_initialize():
    """قابلیت‌ها نباید بینِ دو مسیر واگرا شوند."""
    disc = _rpc("server/discover")["result"]["capabilities"]
    init = _rpc("initialize", {"protocolVersion": mcp.PROTOCOL_VERSION})["result"]["capabilities"]
    assert disc == init == {"tools": {}}, f"واگرایی: {disc} != {init}"


def t_declared_tools_actually_exist():
    """`tools` را اعلام می‌کنیم ⇒ tools/list باید واقعاً ابزار بدهد."""
    names = {t["name"] for t in _rpc("tools/list")["result"]["tools"]}
    assert names == set(mcp.TOOLS), f"واگراییِ ابزارها: {names} != {set(mcp.TOOLS)}"
    assert "propose_action" in names


# ---------------------------------------------------------------- identity

def t_discover_carries_server_identity_in_meta():
    res = _rpc("server/discover")["result"]
    info = res["_meta"][mcp._META_SERVER_INFO]
    assert info["name"] == mcp.SERVER_NAME
    assert info["version"] == mcp.SERVER_VERSION


def t_identity_is_single_sourced_with_initialize():
    """هویت در هر دو مسیر یکی است (قبلاً در initialize لفظی inline بود)."""
    disc = _rpc("server/discover")["result"]["_meta"][mcp._META_SERVER_INFO]
    init = _rpc("initialize", {"protocolVersion": mcp.PROTOCOL_VERSION})["result"]["serverInfo"]
    assert disc == init, f"هویتِ واگرا: {disc} != {init}"


def t_discover_is_cacheable():
    res = _rpc("server/discover")["result"]
    assert isinstance(res["ttlMs"], int) and res["ttlMs"] > 0
    assert res["cacheScope"] in ("public", "private")


# ---------------------------------------------------------------- version handling

def t_unsupported_version_returns_32022_with_supported_list():
    r = _rpc("server/discover", {"_meta": {mcp._META_PROTOCOL_VERSION: "1900-01-01"}})
    err = r["error"]
    assert err["code"] == -32022, f"کدِ اسپک -32022 نیست: {err['code']}"
    assert err["data"]["requested"] == "1900-01-01"
    assert err["data"]["supported"] == list(mcp.SUPPORTED_PROTOCOL_VERSIONS), (
        "خطا باید فهرستِ نسخه‌های واقعی را بدهد وگرنه کلاینت راهِ برگشت ندارد")


def t_modern_version_request_is_refused_not_faked():
    """درخواستِ 2026-07-28 باید صادقانه رد شود، نه اینکه legacy سرو شود."""
    r = _rpc("server/discover", {"_meta": {mcp._META_PROTOCOL_VERSION: "2026-07-28"}})
    assert "error" in r and r["error"]["code"] == -32022


def t_supported_version_request_is_accepted():
    r = _rpc("server/discover", {"_meta": {mcp._META_PROTOCOL_VERSION: mcp.PROTOCOL_VERSION}})
    assert "result" in r, f"نسخهٔ پشتیبانی‌شده رد شد: {r}"


def t_malformed_params_do_not_crash():
    """params/‏_meta ِ بدشکل نباید سرور را بکشد — probe باید جواب بگیرد."""
    for params in ({}, {"_meta": None}, {"_meta": {}}, {"_meta": "not-a-dict"},
                   {"_meta": {mcp._META_PROTOCOL_VERSION: None}}):
        try:
            r = _rpc("server/discover", params)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(f"params={params!r} سرور را کشت: {type(exc).__name__}")
        assert r is not None and ("result" in r or "error" in r), f"params={params!r}"


# ---------------------------------------------------------------- additive guarantee

def t_initialize_still_works_untouched():
    """قیدِ سختِ batch: مسیرِ legacy دست‌نخورده."""
    r = _rpc("initialize", {"protocolVersion": "2025-06-18"})
    res = r["result"]
    assert res["protocolVersion"] == "2025-06-18"
    assert res["capabilities"] == {"tools": {}}
    assert res["serverInfo"]["name"] == "octopus-vault"


def t_initialize_negotiation_still_falls_back():
    """رفتارِ negotiation قبلی حفظ شده: نسخهٔ ناشناس ⇒ نسخهٔ خودِ سرور."""
    res = _rpc("initialize", {"protocolVersion": "1900-01-01"})["result"]
    assert res["protocolVersion"] == mcp.PROTOCOL_VERSION, (
        "initialize نباید رفتارش عوض شود — این batch additive است")


def t_initialized_notification_still_silent():
    assert _rpc("notifications/initialized", mid=None) is None


def t_unknown_method_still_32601():
    """discover نباید مسیرِ خطای متدِ ناشناس را عوض کند (probe به آن تکیه دارد)."""
    assert _rpc("no/such/method")["error"]["code"] == -32601


# ---------------------------------------------------------------- stdio transport

def t_discover_works_over_real_stdio():
    """probe واقعی روی همان ترابردی که `.mcp.json` راه می‌اندازد.

    درون‌پروسه‌ای کافی نیست: مسیرِ ثبت‌شده stdio است و باید JSON خط‌به‌خطِ
    معتبر بدهد (درسِ test-the-pipeline-not-the-unit).
    """
    req = json.dumps({"jsonrpc": "2.0", "id": "d1", "method": "server/discover"})
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(SERVER_PATH)],
        input=req + "\n", capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, f"stdio هیچ خروجی نداد. stderr={proc.stderr[:300]}"
    resp = json.loads(lines[0])
    assert resp["id"] == "d1"
    assert resp["result"]["supportedVersions"] == list(mcp.SUPPORTED_PROTOCOL_VERSIONS)
    assert "2026-07-28" not in resp["result"]["supportedVersions"]


def t_stdio_discover_then_initialize_sequence():
    """توالیِ واقعیِ کلاینتِ dual-era: probe، سپس fallback به initialize."""
    reqs = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "server/discover"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"}}),
    ]) + "\n"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(SERVER_PATH)],
        input=reqs, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60)
    lines = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
    assert len(lines) == 2, f"انتظار ۲ پاسخ، {len(lines)} آمد: {proc.stderr[:300]}"
    assert lines[0]["result"]["resultType"] == "complete"
    assert lines[1]["result"]["protocolVersion"] == "2025-06-18"


if __name__ == "__main__":
    failed = harness.run([
        ("discover reports supported versions", t_discover_reports_supported_versions),
        ("discover does NOT falsely claim modern", t_discover_does_not_falsely_claim_modern_revision),
        ("resultType is complete", t_discover_result_type_is_complete),
        ("capabilities match initialize", t_discover_reports_capabilities_matching_initialize),
        ("declared tools actually exist", t_declared_tools_actually_exist),
        ("identity carried in _meta", t_discover_carries_server_identity_in_meta),
        ("identity single-sourced", t_identity_is_single_sourced_with_initialize),
        ("discover is cacheable", t_discover_is_cacheable),
        ("unsupported version -> -32022 + list", t_unsupported_version_returns_32022_with_supported_list),
        ("modern version refused not faked", t_modern_version_request_is_refused_not_faked),
        ("supported version accepted", t_supported_version_request_is_accepted),
        ("malformed params do not crash", t_malformed_params_do_not_crash),
        ("initialize still works untouched", t_initialize_still_works_untouched),
        ("initialize negotiation unchanged", t_initialize_negotiation_still_falls_back),
        ("initialized notification silent", t_initialized_notification_still_silent),
        ("unknown method still -32601", t_unknown_method_still_32601),
        ("discover over real stdio", t_discover_works_over_real_stdio),
        ("stdio discover->initialize sequence", t_stdio_discover_then_initialize_sequence),
    ])
    sys.exit(1 if failed else 0)
