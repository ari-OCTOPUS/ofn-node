# -*- coding: utf-8 -*-
"""test_g5_infra_selfheal -- infrastructure self-healing tests (EQUIP G5, wave D).

Vertical slice tests for:
  1. Service inventory discovery and dependency graph
  2. MCP HTTP health/readiness/liveness three-tier split
  3. Constitution invariants (5 tools, read-only + propose)
  4. Service call (RPC over HTTP)
  5. DNS-rebinding guard
  6. Configuration schema validation
  7. Full health check integration

Executes on a single ephemeral server started once and stopped once
(Windows ThreadingHTTPServer.shutdown() is fragile if called repeatedly).

Graceful shutdown is already validated by test_octopus_mcp_http_stateless.py
(G5-A, 13/13) which does start/stop once.

Zero new dependencies -- only stdlib.

Execute:
    PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g5_infra_selfheal.py
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT = _HERE.parents[2]  # F:\backup
_OPS = _HERE.parents[1]
_MCP_DIR = _OPS / "octopus_mcp"

sys.path.insert(0, str(_VAULT))
sys.path.insert(0, str(_MCP_DIR))

import server  # noqa: E402
from _ops.infra.service_inventory import (  # noqa: E402
    SERVICE_CATALOG,
    ServiceInventory,
    get_service_inventory,
)
from _ops.infra.mcp_http_health import (  # noqa: E402
    check_constitution,
    check_endpoint,
    check_service_call,
    run_full_health_check,
    HealthCheckResult,
    MCPHealthReport,
)

_FAILS: list[str] = []
_HTTPD = None
_PORT = None


def _ok(cond: bool, msg: str) -> None:
    if not cond:
        _FAILS.append(msg)


def _start_ephemeral_server():
    global _HTTPD, _PORT
    _HTTPD = server.make_http_server("127.0.0.1", 0)
    _PORT = _HTTPD.server_address[1]
    th = threading.Thread(target=_HTTPD.serve_forever, daemon=True)
    th.start()
    time.sleep(0.15)


def _stop_ephemeral_server():
    global _HTTPD
    if _HTTPD:
        _HTTPD.shutdown()
        _HTTPD.server_close()


# ---------------------------------------------------------------------------
# 1. Service inventory
# ---------------------------------------------------------------------------

def t_service_catalog_has_all_known_services():
    """CATALOG must include organism, cortex, live, center, gateway, mcp_server."""
    ids = {s["id"] for s in SERVICE_CATALOG}
    expected = {"organism", "cortex", "live", "center", "gateway", "mcp_server"}
    _ok(ids == expected, f"catalog ids mismatch: got {ids}, expected {expected}")


def t_service_catalog_has_dependency_order():
    """Catalog must have at least 5 entries with implied dependency ordering."""
    _ok(len(SERVICE_CATALOG) >= 5,
        f"catalog must have >=5 entries; got {len(SERVICE_CATALOG)}")
    ids = [s["id"] for s in SERVICE_CATALOG]
    _ok(ids[0] == "organism", f"first service should be organism; got {ids[0]}")
    _ok(ids[-1] == "mcp_server",
        f"last service should be mcp_server; got {ids[-1]}")


def t_service_inventory_is_typed():
    """get_service_inventory must return a ServiceInventory with typed fields."""
    inv = get_service_inventory()
    _ok(isinstance(inv, ServiceInventory), "must return ServiceInventory instance")
    _ok(len(inv.services) == len(SERVICE_CATALOG),
        f"service count {len(inv.services)} != catalog count {len(SERVICE_CATALOG)}")
    _ok(inv.scanned_at != "", "scanned_at must be populated")
    _ok(inv.python_version != "", "python_version must be populated")
    _ok(inv.platform != "", "platform must be populated")


def t_service_inventory_dependency_graph():
    """Dependency graph must produce correct edges."""
    inv = get_service_inventory()
    edges = inv.dependency_graph()
    _ok(len(edges) == len(SERVICE_CATALOG) - 1,
        f"edges count {len(edges)} != expected {len(SERVICE_CATALOG) - 1}")
    if edges:
        _ok(edges[0] == ("organism", "cortex"),
            f"first edge should be (organism, cortex); got {edges[0]}")


def t_service_inventory_to_dict_roundtrip():
    """to_dict must produce serializable JSON."""
    inv = get_service_inventory()
    d = inv.to_dict()
    try:
        json_str = json.dumps(d, ensure_ascii=False)
        _ok(len(json_str) > 100, "serialized JSON should be substantial")
        d2 = json.loads(json_str)
        _ok(len(d2["services"]) == len(inv.services),
            "roundtrip service count must match")
    except (json.JSONDecodeError, TypeError) as exc:
        _ok(False, f"JSON roundtrip failed: {exc}")


def t_service_inventory_summary():
    """summary() must produce a readable string."""
    inv = get_service_inventory()
    s = inv.summary()
    _ok("OCTOPUS Service Inventory" in s, "summary must contain header")
    _ok("Services:" in s, "summary must contain running count")
    for svc in inv.services:
        _ok(svc.id in s, f"summary must mention service {svc.id}")


# ---------------------------------------------------------------------------
# 2. Health / Readiness / Liveness three-tier split
# ---------------------------------------------------------------------------

def t_healthz_returns_liveness():
    """GET /healthz must return alive status with uptime."""
    r = check_endpoint("127.0.0.1", _PORT, "/healthz")
    _ok(r.ok, f"/healthz must return 2xx; got {r.status_code}")
    _ok(r.response.get("status") == "alive",
        f"healthz must report 'alive'; got {r.response.get('status')}")
    _ok("uptime_s" in r.response, "healthz must include uptime_s")
    _ok(r.response["uptime_s"] >= 0, "uptime must be non-negative")


def t_readyz_returns_readiness():
    """GET /readyz must return readiness with engine and agentignore state."""
    r = check_endpoint("127.0.0.1", _PORT, "/readyz")
    _ok(r.ok, f"/readyz must return 2xx; got {r.status_code}")
    _ok("ready" in r.response, "readyz must include 'ready' field")
    _ok(r.response.get("engine") in ("rg", "py-tracked-only"),
        f"engine must be rg or py-tracked-only; got {r.response.get('engine')}")
    _ok("agentignore_fail_closed" in r.response,
        "readyz must include agentignore_fail_closed")
    _ok("uptime_s" in r.response, "readyz must include uptime_s")
    _ok("degraded" in r.response, "readyz must include degraded list")


def t_healthz_and_readyz_are_different_endpoints():
    """/healthz and /readyz must return different shaped payloads."""
    h = check_endpoint("127.0.0.1", _PORT, "/healthz")
    r = check_endpoint("127.0.0.1", _PORT, "/readyz")
    _ok(h.response.get("status") == "alive", "healthz has alive status")
    _ok("engine" in r.response, "readyz has engine (healthz does not)")
    _ok("ready" in r.response, "readyz has ready (healthz does not)")


# ---------------------------------------------------------------------------
# 3. Constitution invariants
# ---------------------------------------------------------------------------

def t_constitution_five_tools():
    """CONSTITUTION: exactly 5 tools, matching the canonical set."""
    cc = check_constitution()
    _ok(cc["tool_count"] == 5, f"must have 5 tools; got {cc['tool_count']}")
    _ok(cc["tools_match"], f"tools must match canonical set; got {cc['tools']}")


def t_constitution_all_read_only_except_propose():
    """All tools except propose_action must be read-only (no write operations)."""
    cc = check_constitution()
    _ok(cc["all_read_only"],
        "all non-propose tools must be read-only; inspection found write operations")


def t_constitution_has_propose_action():
    """propose_action must exist as the only write tool."""
    cc = check_constitution()
    _ok(cc["has_propose_action"], "propose_action must be present")
    _ok(cc["ok"], f"constitution check failed: {cc}")


# ---------------------------------------------------------------------------
# 4. Service call (RPC over HTTP)
# ---------------------------------------------------------------------------

def t_service_call_list_tree():
    """POST /mcp with tools/call:list_tree must work over HTTP."""
    r = check_service_call("127.0.0.1", _PORT)
    _ok(r.ok, f"tools/call must succeed; got {r.status_code}: {r.error}")
    if r.ok:
        data = r.response
        _ok("result" in data, "response must have 'result'")
        _ok("content" in data.get("result", {}),
            "result must have 'content'")


# ---------------------------------------------------------------------------
# 5. DNS-rebinding guard
# ---------------------------------------------------------------------------

def t_dns_rebinding_foreign_host_rejected():
    """Foreign Host header must return 403."""
    r = check_endpoint("127.0.0.1", _PORT, "/healthz")
    _ok(r.ok, f"localhost must be allowed; got {r.status_code}")
    import http.client as hc
    conn = hc.HTTPConnection("127.0.0.1", _PORT, timeout=5)
    conn.request("GET", "/healthz", headers={"Host": "evil.example.com"})
    resp = conn.getresponse()
    resp.read()
    conn.close()
    _ok(resp.status == 403,
        f"foreign Host must return 403; got {resp.status}")


# ---------------------------------------------------------------------------
# 6. Configuration schema validation
# ---------------------------------------------------------------------------

def t_config_policy_schema():
    """policy.yaml must have the expected top-level keys."""
    policy_path = _VAULT / "_octopus" / "config" / "policy.yaml"
    if not policy_path.exists():
        _ok(False, f"policy.yaml not found at {policy_path}")
        return
    text = policy_path.read_text(encoding="utf-8", errors="replace")
    _ok("propose-only" in text, "policy must contain 'propose-only' mode")
    _ok("requires_approval" in text, "policy must have requires_approval section")
    _ok("forbidden_now" in text, "policy must have forbidden_now section")


def t_mcp_json_config_exists():
    """.mcp.json must exist and reference the MCP server."""
    mcp_path = _VAULT / ".mcp.json"
    if not mcp_path.exists():
        _ok(False, f".mcp.json not found at {mcp_path}")
        return
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    _ok("mcpServers" in data, ".mcp.json must have mcpServers")
    _ok("octopus-vault" in data["mcpServers"],
        ".mcp.json must reference octopus-vault")
    svr = data["mcpServers"]["octopus-vault"]
    args_list = svr.get("args", [])
    _ok(any("server.py" in str(a) for a in args_list),
        "octopus-vault must launch server.py")


def t_activation_flags_count():
    """Activation flags must exist and be countable."""
    ops_dir = _VAULT / "_ops"
    flags = list(ops_dir.glob("ACTIVATION-*.flag"))
    _ok(len(flags) > 0, f"expected activation flags; found {len(flags)}")


# ---------------------------------------------------------------------------
# 7. Full health check integration
# ---------------------------------------------------------------------------

def t_full_health_check_report():
    """run_full_health_check must produce a complete report."""
    report = run_full_health_check("127.0.0.1", _PORT, start_server=False)
    _ok(report.liveness is not None, "report must have liveness")
    _ok(report.readiness is not None, "report must have readiness")
    _ok(report.service_call is not None, "report must have service_call")
    _ok(report.constitution_check is not None, "report must have constitution_check")
    _ok(report.overall in ("PASS", "FAIL"), "report must have PASS or FAIL overall")
    _ok(report.liveness.ok, "liveness must be ok in fresh server")
    _ok(report.readiness.ok, "readiness must be ok in fresh server")
    _ok(report.constitution_check.get("ok"), "constitution must be ok")


def t_full_health_report_to_dict():
    """Health report must serialize to JSON."""
    report = MCPHealthReport(
        liveness=HealthCheckResult("/healthz", 200, {"status": "alive", "uptime_s": 1.0}, 5.0, True),
        readiness=HealthCheckResult("/readyz", 200, {"ready": True, "engine": "rg"}, 3.0, True),
        service_call=HealthCheckResult("POST /mcp", 200, {"result": {}}, 10.0, True),
        constitution_check={"ok": True, "tool_count": 5},
        overall="PASS",
    )
    d = report.to_dict()
    try:
        json_str = json.dumps(d, ensure_ascii=False)
        _ok(len(json_str) > 50, "JSON report must be substantial")
    except (json.JSONDecodeError, TypeError) as exc:
        _ok(False, f"JSON serialization failed: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    global _HTTPD, _PORT
    _start_ephemeral_server()
    try:
        tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
        for t in tests:
            try:
                t()
            except Exception as exc:  # noqa: BLE001
                _FAILS.append(f"{t.__name__} raised {type(exc).__name__}: {exc}")
    finally:
        _stop_ephemeral_server()
    if _FAILS:
        print(f"FAIL test_g5_infra_selfheal: {len(_FAILS)} problem(s)")
        for f in _FAILS:
            print("  X", f)
        return 1
    count = len([k for k in globals() if k.startswith("t_")])
    print(f"OK test_g5_infra_selfheal: {count}/{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
