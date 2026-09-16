# -*- coding: utf-8 -*-
"""تستِ ترابردِ HTTP stateless ِ سرورِ MCP ِ octopus-vault (2026-08-16، فاز ۵-الف مسیر A).

قراردادِ سنجیده‌شده (spec ِ Streamable HTTP ِ 2025-06-18 در حالتِ stateless، دستی و
فقط stdlib — بدونِ پکیجِ mcp):
  * initialize: negotiation نسخه + serverInfo + هیچ header ِ Mcp-Session-Id ای صادر نشود.
  * tools/list و tools/call رویِ HTTP همانِ stdio.
  * notification → 202 با بدنهٔ خالی.
  * GET/DELETE رویِ /mcp → 405 (session/SSE مستقل نداریم).
  * Host خارج از allowlist محلی → 403 (دفاعِ DNS-rebinding).
  * Accept بدونِ application/json → 406 · JSON خراب/batch → 400 ·
    Mcp-Session-Id ارسالیِ کلاینت → 400 (سرور stateless است).
  * /healthz (liveness) و /readyz (readiness) جدا.

اجرا: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_http_stateless.py
"""
from __future__ import annotations

import http.client
import json
import re
import sys
import threading
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[1] / "octopus_mcp"))
import server  # noqa: E402


_FAILS: list[str] = []
_HTTPD = None
_PORT = None


def _ok(cond: bool, msg: str) -> None:
    if not cond:
        _FAILS.append(msg)


def _req(method: str, path: str, body=None, headers=None, host_hdr=None):
    """یک درخواستِ خام رویِ سوکتِ واقعی؛ خروجی: (status, headers, body_bytes)."""
    conn = http.client.HTTPConnection("127.0.0.1", _PORT, timeout=10)
    hdrs = {"Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    if host_hdr:
        hdrs["Host"] = host_hdr          # هاستِ جعلی برایِ تستِ rebinding
    payload = None
    if body is not None:
        payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    conn.request(method, path, body=payload, headers=hdrs)
    r = conn.getresponse()
    out = (r.status, dict(r.getheaders()), r.read())
    conn.close()
    return out


def _rpc(msg: dict, headers=None):
    st, hd, raw = _req("POST", "/mcp", body=msg, headers=headers)
    return st, hd, (json.loads(raw.decode("utf-8")) if raw else None)


def t_initialize_negotiates_and_has_no_session() -> None:
    st, hd, r = _rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "2025-03-26"}})
    _ok(st == 200, f"initialize باید 200 باشد؛ گرفت {st}")
    _ok(r["result"]["protocolVersion"] == "2025-03-26",
        "نسخهٔ خواسته‌شده و پشتیبانی‌شده باید همان برگردد")
    _ok(r["result"]["serverInfo"]["name"] == "octopus-vault", "serverInfo باید برگردد")
    _ok("Mcp-Session-Id" not in {k.lower() for k in hd},
        "سرورِ stateless نباید Mcp-Session-Id صادر کند")


def t_initialize_unknown_version_falls_back() -> None:
    st, _, r = _rpc({"jsonrpc": "2.0", "id": 2, "method": "initialize",
                     "params": {"protocolVersion": "1999-01-01"}})
    _ok(st == 200 and r["result"]["protocolVersion"] == server.PROTOCOL_VERSION,
        "نسخهٔ ناشناس → پیش‌فرضِ سرور (negotiation صادقانه)")


def t_tools_list_matches_stdio_five_tools() -> None:
    st, _, r = _rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    names = [t["name"] for t in r["result"]["tools"]]
    _ok(st == 200 and sorted(names) == sorted(server.TOOLS.keys()),
        f"همانِ پنج ابزارِ stdio؛ گرفت: {names}")


def t_tools_call_hash_file_over_http() -> None:
    st, _, r = _rpc({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                     "params": {"name": "hash_file",
                                "arguments": {"path": "_ops/octopus_mcp/CONSTITUTION.md"}}})
    _ok(st == 200 and r["result"]["isError"] is False, f"hash_file باید سبز باشد؛ {r}")
    out = json.loads(r["result"]["content"][0]["text"])
    _ok(re.fullmatch(r"[0-9a-f]{64}", out["sha256"]) is not None,
        "sha256 باید ۶۴ hex باشد — همانِ مسیرِ stdio")


def t_tools_call_unknown_tool_is_jsonrpc_error() -> None:
    st, _, r = _rpc({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                     "params": {"name": "no_such_tool", "arguments": {}}})
    _ok(st == 200 and r.get("error", {}).get("code") == -32601,
        f"ابزارِ ناشناس → خطایِ JSON-RPC -32601؛ گرفت: {r}")


def t_notification_gets_202_empty() -> None:
    st, _, raw = _req("POST", "/mcp",
                      body={"jsonrpc": "2.0", "method": "notifications/initialized"})
    _ok(st == 202 and raw == b"", f"notification → 202 + بدنهٔ خالی؛ گرفت {st} {raw!r}")


def t_get_and_delete_mcp_are_405() -> None:
    st1, _, _ = _req("GET", "/mcp")
    st2, _, _ = _req("DELETE", "/mcp")
    _ok(st1 == 405, f"GET /mcp → 405 در سرورِ stateless؛ گرفت {st1}")
    _ok(st2 == 405, f"DELETE /mcp → 405 (session برای بستن نیست)؛ گرفت {st2}")


def t_healthz_readyz_split() -> None:
    st, _, raw = _req("GET", "/healthz")
    _ok(st == 200 and json.loads(raw)["status"] == "alive", "/healthz = liveness زنده")
    st, _, raw = _req("GET", "/readyz")
    body = json.loads(raw)
    _ok(st == 200 and body["engine"] in ("rg", "py-tracked-only"),
        f"/readyz = readiness با engine؛ گرفت: {body}")
    _ok("agentignore_fail_closed" in body, "readiness باید وضعیتِ fail-closed را بگوید")


def t_foreign_host_is_403() -> None:
    st, _, _ = _req("GET", "/healthz", host_hdr="evil.example")
    _ok(st == 403, f"Host خارجی → 403 (DNS-rebinding)؛ گرفت {st}")
    st, _, _ = _req("POST", "/mcp", body={"jsonrpc": "2.0", "id": 9, "method": "tools/list"},
                    host_hdr="evil.example:1234")
    _ok(st == 403, "Host خارجی رویِ POST هم → 403")


def t_accept_without_json_is_406() -> None:
    st, _, _ = _req("POST", "/mcp", body={"jsonrpc": "2.0", "id": 10, "method": "tools/list"},
                    headers={"Accept": "text/plain"})
    _ok(st == 406, f"Accept بدونِ application/json → 406؛ گرفت {st}")


def t_bad_json_and_batch_are_400() -> None:
    st, _, _ = _req("POST", "/mcp", body=b"{not-json")
    _ok(st == 400, f"JSON خراب → 400؛ گرفت {st}")
    st, _, _ = _req("POST", "/mcp",
                    body=[{"jsonrpc": "2.0", "id": 11, "method": "tools/list"}])
    _ok(st == 400, f"batch (حذف‌شده در 2025-06-18) → 400؛ گرفت {st}")


def t_client_session_header_rejected_400() -> None:
    st, _, _ = _req("POST", "/mcp", body={"jsonrpc": "2.0", "id": 12, "method": "tools/list"},
                    headers={"Mcp-Session-Id": "forged-123"})
    _ok(st == 400, f"کلاینتِ session-id می‌فرستد به سرورِ stateless → 400؛ گرفت {st}")


def t_search_hybrid_single_word_over_http() -> None:
    st, _, r = _rpc({"jsonrpc": "2.0", "id": 13, "method": "tools/call",
                     "params": {"name": "search_hybrid",
                                "arguments": {"query": "CONSTITUTION",
                                              "path": "_ops/octopus_mcp", "glob": "*.md",
                                              "max_results": 5}}})
    _ok(st == 200, f"search رویِ HTTP → 200؛ گرفت {st}")
    out = json.loads(r["result"]["content"][0]["text"])
    _ok(len(out["content"]) >= 1, "کوئریِ تک‌واژه‌ایِ قطعی باید hit داشته باشد")
    _ok(out["engine"] in ("rg", "py-tracked-only"), "فیلدِ engine صادقانه")


def main() -> int:
    global _HTTPD, _PORT
    _HTTPD = server.make_http_server("127.0.0.1", 0)
    _PORT = _HTTPD.server_address[1]
    th = threading.Thread(target=_HTTPD.serve_forever, daemon=True)
    th.start()
    try:
        tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
        for t in tests:
            try:
                t()
            except Exception as exc:  # noqa: BLE001
                _FAILS.append(f"{t.__name__} raised {type(exc).__name__}: {exc}")
    finally:
        _HTTPD.shutdown()
        _HTTPD.server_close()
    if _FAILS:
        print(f"FAIL test_octopus_mcp_http_stateless: {len(_FAILS)} problem(s)")
        for f in _FAILS:
            print("  ❌", f)
        return 1
    print(f"OK test_octopus_mcp_http_stateless: "
          f"{len([k for k in globals() if k.startswith('t_')])}/"
          f"{len([k for k in globals() if k.startswith('t_')])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
