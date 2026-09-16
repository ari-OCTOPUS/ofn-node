#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mcp_malformed_hardening.py — یک پیامِ بدشکل نباید سرورِ MCP را بکشد.

چرا (۲۰۲۶-۰۸-۲۳): هنگامِ ساختِ `server/discover` تستِ malformed یک DoS ِ واقعی
پیدا کرد — `params` ِ غیر-dict ⇒ `AttributeError` ⇒ چون حلقهٔ stdio ِ `main()`
هیچ try نداشت، **کلِ پروسهٔ سرور می‌مرد**. آن یکی همان‌جا فیکس شد، ولی همان
الگو در دو جای دیگر هم بود:

    _handle:      msg.get(...)                      ← msg ِ غیر-dict
    initialize:   (msg.get("params") or {}).get(..) ← params ِ غیر-dict
    tools/call:   msg.get("params") or {}           ← همان

نکتهٔ ظریفِ `or {}`: فقط falsy را می‌گیرد. `""` و `[]` و `0` رد می‌شوند، ولی
`"abc"`، `[1]`، `42` **از آن عبور می‌کنند** و بعد `.get` رویشان منفجر می‌شود.
پس `or {}` امنیتِ کاذب می‌داد.

ناهم‌ترازیِ دو ترابرد که ریشهٔ ماجرا بود: مسیرِ HTTP از قبل
`isinstance(msg, dict)` را چک می‌کرد (→ 400) و مسیرِ stdio — یعنی همان چیزی که
`.mcp.json` واقعاً اجرا می‌کند — نمی‌کرد.

روشِ این فایل: بخشِ کشنده **باید** از راهِ subprocess ِ واقعی سنجیده شود.
فراخوانیِ درون‌پروسه‌ایِ `_handle` هرگز نمی‌تواند ثابت کند «سرور زنده ماند»،
چون چیزی که می‌مرد خودِ پروسه بود (درسِ test-the-pipeline-not-the-unit).
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("mcp-malformed-hardening")
_OPS = harness.SELF_OPS

sys.path.insert(0, str(_OPS / "octopus_mcp"))
import server as mcp  # noqa: E402

SERVER_PATH = _OPS / "octopus_mcp" / "server.py"

# هر خط JSON ِ **معتبر** است — پس از json.loads رد می‌شود و مستقیم به dispatcher می‌رسد.
MALFORMED_LINES = [
    '42',
    '"just a string"',
    '[1, 2, 3]',
    'null',
    'true',
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":"not-a-dict"}',
    '{"jsonrpc":"2.0","id":2,"method":"initialize","params":[1,2]}',
    '{"jsonrpc":"2.0","id":3,"method":"initialize","params":99}',
    '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":"nope"}',
    '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"list_tree","arguments":"nope"}}',
    '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"list_tree","arguments":[1]}}',
    '{"jsonrpc":"2.0","id":7,"method":"server/discover","params":"nope"}',
    '{"jsonrpc":"2.0","id":8,"method":12345}',
    '{"jsonrpc":"2.0","id":9}',
]


def _run_stdio(lines: list[str], timeout: int = 60):
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(SERVER_PATH)],
        input="\n".join(lines) + "\n", capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout)
    out = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
    return proc, out


# ---------------------------------------------------------------- in-process

def t_handle_survives_every_malformed_shape():
    """dispatcher روی هیچ‌کدام استثنا پرتاب نمی‌کند."""
    for raw in MALFORMED_LINES:
        msg = json.loads(raw)
        try:
            mcp._handle(msg)
        except Exception as exc:  # noqa: BLE001
            raise AssertionError(f"{raw} → {type(exc).__name__}: {exc}")


def t_non_dict_message_gets_invalid_request():
    for raw in ('42', '"s"', '[1]', 'null', 'true'):
        r = mcp._handle(json.loads(raw))
        assert r["error"]["code"] == -32600, f"{raw} → {r}"
        assert r["id"] is None


def t_non_string_method_rejected():
    r = mcp._handle({"jsonrpc": "2.0", "id": 8, "method": 12345})
    assert r["error"]["code"] == -32600


def t_params_of_only_accepts_dicts():
    f = mcp._params_of
    assert f({"params": {"a": 1}}) == {"a": 1}
    for bad in ("abc", [1], 42, None, True):
        assert f({"params": bad}) == {}, f"{bad!r} باید به dictِ خالی تبدیل شود"


# ---------------------------------------------------------------- initialize

def t_initialize_survives_non_dict_params():
    """همان چیزی که مالک خواست — و مسیرِ legacy همچنان جواب می‌دهد."""
    for bad in ("not-a-dict", [1, 2], 99, True):
        r = mcp._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                         "params": bad})
        assert "result" in r, f"params={bad!r} → {r}"
        assert r["result"]["protocolVersion"] == mcp.PROTOCOL_VERSION, (
            "با paramsِ بدشکل باید به نسخهٔ خودِ سرور برگردد")


def t_initialize_behaviour_unchanged_for_valid_input():
    """گاردِ «ضعیف نشدن»: برای هر ورودیِ معتبر رفتار دقیقاً همان قبل است."""
    ok = mcp._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "2025-06-18"}})["result"]
    assert ok["protocolVersion"] == "2025-06-18"
    assert ok["capabilities"] == {"tools": {}}
    assert ok["serverInfo"] == {"name": mcp.SERVER_NAME, "version": mcp.SERVER_VERSION}

    # نسخهٔ ناشناس ⇒ fallback به نسخهٔ سرور (رفتارِ negotiation قبلی)
    fb = mcp._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "1900-01-01"}})["result"]
    assert fb["protocolVersion"] == mcp.PROTOCOL_VERSION

    # بدونِ params اصلاً (کلاینتِ مینیمال)
    none = mcp._handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})["result"]
    assert none["protocolVersion"] == mcp.PROTOCOL_VERSION


# ---------------------------------------------------------------- tools/call

def t_tools_call_survives_non_dict_params():
    r = mcp._handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                     "params": "nope"})
    assert r is not None and ("error" in r or "result" in r)


def t_tools_call_non_dict_arguments_is_honest_error():
    """آرگومانِ بدشکل باید خطای صادق بدهد، نه سکوت و نه اجرا با dictِ خالی."""
    for bad in ("nope", [1], 42):
        r = mcp._handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                         "params": {"name": "list_tree", "arguments": bad}})
        assert r["result"]["isError"] is True, f"arguments={bad!r} → {r}"


def t_tools_call_still_works_normally():
    """گاردِ رگرسیون: مسیرِ سالمِ ابزار دست‌نخورده."""
    r = mcp._handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                     "params": {"name": "list_tree",
                                "arguments": {"path": ".", "depth": 1}}})
    assert r["result"]["isError"] is False
    payload = json.loads(r["result"]["content"][0]["text"])
    assert "entries" in payload


# ---------------------------------------------------------------- real process

def t_server_process_survives_malformed_flood_over_stdio():
    """قلبِ این فایل: سیلِ پیامِ بدشکل، سپس یک درخواستِ سالم.

    اگر پاسخِ سالمِ پایانی برسد یعنی پروسه زنده مانده. قبل از فیکس، **اولین**
    خط پروسه را می‌کشت و این پاسخ هرگز نمی‌آمد.
    """
    lines = list(MALFORMED_LINES) + [
        json.dumps({"jsonrpc": "2.0", "id": "final", "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"}})]
    proc, out = _run_stdio(lines)
    ids = [r.get("id") for r in out]
    assert "final" in ids, (
        f"سرور از سیلِ بدشکل جان نبرد. rc={proc.returncode} "
        f"ids={ids} stderr={proc.stderr[:300]}")
    final = next(r for r in out if r.get("id") == "final")
    assert final["result"]["protocolVersion"] == "2025-06-18"


def t_malformed_then_discover_then_tools_over_stdio():
    """توالیِ واقعی: آشغال → probe → کارِ واقعی، همه در یک پروسه."""
    lines = [
        '{"jsonrpc":"2.0","id":"junk","method":"initialize","params":"boom"}',
        json.dumps({"jsonrpc": "2.0", "id": "disc", "method": "server/discover"}),
        json.dumps({"jsonrpc": "2.0", "id": "tl", "method": "tools/list"}),
    ]
    proc, out = _run_stdio(lines)
    by_id = {r.get("id"): r for r in out}
    assert set(by_id) >= {"junk", "disc", "tl"}, (
        f"پاسخ‌ها ناقص‌اند: {list(by_id)} stderr={proc.stderr[:300]}")
    assert "result" in by_id["junk"]
    assert by_id["disc"]["result"]["resultType"] == "complete"
    assert {t["name"] for t in by_id["tl"]["result"]["tools"]} == set(mcp.TOOLS)


if __name__ == "__main__":
    failed = harness.run([
        ("_handle survives every malformed shape", t_handle_survives_every_malformed_shape),
        ("non-dict message -> -32600", t_non_dict_message_gets_invalid_request),
        ("non-string method -> -32600", t_non_string_method_rejected),
        ("_params_of only accepts dicts", t_params_of_only_accepts_dicts),
        ("initialize survives non-dict params", t_initialize_survives_non_dict_params),
        ("initialize unchanged for valid input", t_initialize_behaviour_unchanged_for_valid_input),
        ("tools/call survives non-dict params", t_tools_call_survives_non_dict_params),
        ("tools/call bad arguments -> honest error", t_tools_call_non_dict_arguments_is_honest_error),
        ("tools/call still works normally", t_tools_call_still_works_normally),
        ("PROCESS survives malformed flood (stdio)", t_server_process_survives_malformed_flood_over_stdio),
        ("malformed->discover->tools (stdio)", t_malformed_then_discover_then_tools_over_stdio),
    ])
    sys.exit(1 if failed else 0)
