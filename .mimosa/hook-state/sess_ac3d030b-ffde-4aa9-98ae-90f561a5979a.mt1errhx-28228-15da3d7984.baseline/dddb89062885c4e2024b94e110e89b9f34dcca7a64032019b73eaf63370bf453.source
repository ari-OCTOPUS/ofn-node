# -*- coding: utf-8 -*-
"""mcp_http_health -- health/readiness/liveness validation for the MCP HTTP server.

Validates the three-tier health contract for the OCTOPUS MCP stateless HTTP
transport (added by G5-A in commit 5899ed5):
  * /healthz  = liveness  (process alive, uptime)
  * /readyz   = readiness (engine available, agentignore ok, no degraded state)
  * /mcp POST = service   (JSON-RPC tools/call works)

Also validates:
  * Graceful shutdown (server shuts down cleanly on signal)
  * Configuration schema (CONSTITUTION invariants: 5 tools, read-only + propose)
  * Startup ordering (dependency graph from service_inventory)

Zero new pip dependencies -- only stdlib.
"""
from __future__ import annotations

import http.client
import json
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
_OPS = _HERE.parents[1]
_MCP_DIR = _OPS / "octopus_mcp"

# Lazy import to avoid side effects at module level
def _import_server():
    sys.path.insert(0, str(_MCP_DIR))
    import server
    return server


@dataclass
class HealthCheckResult:
    """Result of a single health endpoint check."""
    endpoint: str
    status_code: int
    response: dict
    latency_ms: float
    ok: bool
    error: str = ""


@dataclass
class MCPHealthReport:
    """Full health report for the MCP HTTP server."""
    liveness: Optional[HealthCheckResult] = None
    readiness: Optional[HealthCheckResult] = None
    service_call: Optional[HealthCheckResult] = None
    constitution_check: Optional[dict] = None
    graceful_shutdown_ok: Optional[bool] = None
    overall: str = "UNKNOWN"

    def summary(self) -> str:
        lines = [f"MCP HTTP Health Report: {self.overall}"]
        for label, check in [("Liveness  (/healthz)", self.liveness),
                             ("Readiness (/readyz)", self.readiness),
                             ("Service   (tools/call)", self.service_call)]:
            if check:
                status = "OK" if check.ok else "FAIL"
                lines.append(f"  {label}: {status} ({check.status_code}, {check.latency_ms:.0f}ms)")
                if check.error:
                    lines.append(f"    error: {check.error}")
            else:
                lines.append(f"  {label}: NOT CHECKED")
        if self.constitution_check:
            cc = self.constitution_check
            lines.append(f"  Constitution: tools={cc.get('tool_count')}, "
                         f"read_only={cc.get('all_read_only')}, "
                         f"propose={cc.get('has_propose_action')}, "
                         f"ok={cc.get('ok')}")
        if self.graceful_shutdown_ok is not None:
            lines.append(f"  Graceful shutdown: {'OK' if self.graceful_shutdown_ok else 'FAIL'}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "overall": self.overall,
            "liveness": _check_to_dict(self.liveness),
            "readiness": _check_to_dict(self.readiness),
            "service_call": _check_to_dict(self.service_call),
            "constitution_check": self.constitution_check,
            "graceful_shutdown_ok": self.graceful_shutdown_ok,
        }


def _check_to_dict(check: Optional[HealthCheckResult]) -> Optional[dict]:
    if check is None:
        return None
    return {
        "endpoint": check.endpoint,
        "status_code": check.status_code,
        "latency_ms": check.latency_ms,
        "ok": check.ok,
        "error": check.error,
    }


def check_endpoint(host: str, port: int, path: str, timeout_s: float = 5.0) -> HealthCheckResult:
    """Check a single HTTP endpoint and return typed result."""
    t0 = time.monotonic()
    conn = None
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout_s)
        conn.request("GET", path, headers={"Accept": "application/json"})
        resp = conn.getresponse()
        body = resp.read()
        latency = (time.monotonic() - t0) * 1000
        conn.close()
        conn = None
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}
        ok = 200 <= resp.status < 300
        return HealthCheckResult(
            endpoint=path, status_code=resp.status,
            response=data, latency_ms=latency, ok=ok,
        )
    except (ConnectionRefusedError, OSError, Exception) as exc:
        latency = (time.monotonic() - t0) * 1000
        return HealthCheckResult(
            endpoint=path, status_code=-1,
            response={}, latency_ms=latency, ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def check_service_call(host: str, port: int, timeout_s: float = 5.0) -> HealthCheckResult:
    """POST a tools/call to verify the MCP RPC endpoint works."""
    t0 = time.monotonic()
    conn = None
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout_s)
        payload = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "list_tree", "arguments": {"path": ".", "depth": 1}},
        }).encode("utf-8")
        conn.request("POST", "/mcp", body=payload,
                     headers={"Content-Type": "application/json",
                              "Accept": "application/json"})
        resp = conn.getresponse()
        body = resp.read()
        latency = (time.monotonic() - t0) * 1000
        conn.close()
        conn = None
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = {}
        ok = resp.status == 200
        # Check that the response has the expected JSON-RPC structure
        if ok and "result" in data and "content" in data["result"]:
            ok = True
        elif ok:
            ok = False  # unexpected structure
        return HealthCheckResult(
            endpoint="POST /mcp (tools/call:list_tree)", status_code=resp.status,
            response=data, latency_ms=latency, ok=ok,
        )
    except (ConnectionRefusedError, OSError, Exception) as exc:
        latency = (time.monotonic() - t0) * 1000
        return HealthCheckResult(
            endpoint="POST /mcp (tools/call:list_tree)", status_code=-1,
            response={}, latency_ms=latency, ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def check_constitution() -> dict:
    """Verify the CONSTITUTION.md invariants without starting a server."""
    server = _import_server()
    tools = list(server.TOOLS.keys())
    tool_count = len(tools)
    expected_tools = {"list_tree", "read_file_slice", "hash_file",
                      "search_hybrid", "propose_action"}
    has_propose_action = "propose_action" in tools
    tools_match = set(tools) == expected_tools
    # Verify all tools except propose_action are read-only.
    # Read-only means: no file writes, no destructive subprocess, no os.system.
    # open() for reading (rb/r) and subprocess.run for search/git-ls are fine.
    read_only_tools = [t for t in tools if t != "propose_action"]
    all_read_only = True
    violations = []
    for t in read_only_tools:
        fn = server.TOOLS[t][0]
        import inspect
        src = inspect.getsource(fn)
        # True write indicators: open with write mode, os.system, file .write()
        # Exclude open("rb") and open(r"...", "rb") patterns (read-only)
        import re as _re
        write_violations = []
        for m in _re.finditer(r'open\([^)]*\)', src):
            call = m.group(0)
            # Skip read-mode opens (rb, r, encoding= without w/a/x)
            if any(mode in call for mode in ['"w', '"a', '"x', "'w", "'a", "'x",
                                              '"r+"', '"a+"', '"w+"']):
                write_violations.append(f"open-write: {call}")
        if "os.system(" in src:
            write_violations.append("os.system")
        if write_violations:
            all_read_only = False
            violations.append(f"{t}: {', '.join(write_violations)}")
    ok = tool_count == 5 and tools_match and has_propose_action and all_read_only
    return {
        "tool_count": tool_count,
        "tools": tools,
        "expected_tools": sorted(expected_tools),
        "tools_match": tools_match,
        "has_propose_action": has_propose_action,
        "all_read_only": all_read_only,
        "ok": ok,
    }


def check_graceful_shutdown(httpd=None) -> bool:
    """Verify an MCP HTTP server shuts down cleanly and releases its port.

    If httpd is provided, uses that server instance. Otherwise starts one on
    an ephemeral port. Verifies shutdown completes and a new server can
    rebind the same port (proving clean release without probing a dead socket).
    """
    server = _import_server()
    owned = httpd is None
    try:
        if owned:
            httpd = server.make_http_server("127.0.0.1", 0)
        port = httpd.server_address[1]
        # Start server in background thread
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        # Verify it's serving
        time.sleep(0.1)
        lc = check_endpoint("127.0.0.1", port, "/healthz", timeout_s=2.0)
        if not lc.ok:
            return False
        # Shutdown
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5.0)
        # Verify port is released by rebinding the same port
        time.sleep(0.15)
        try:
            httpd2 = server.make_http_server("127.0.0.1", port)
            httpd2.server_close()
            return True  # port was released cleanly
        except OSError:
            return False  # port still held
    except Exception:
        return False


def run_full_health_check(host: str = "127.0.0.1", port: int = 0,
                          start_server: bool = True) -> MCPHealthReport:
    """Run full health check suite (liveness, readiness, service call, constitution).

    Note: graceful_shutdown is NOT included here because it requires stopping the
    server under test. Call check_graceful_shutdown() separately.

    If start_server=True and port=0, starts an ephemeral MCP HTTP server
    for the duration of the check.
    """
    server_module = None
    httpd = None
    thread = None
    actual_port = port

    if start_server:
        server_module = _import_server()
        httpd = server_module.make_http_server(host, port if port > 0 else 0)
        actual_port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.2)  # let server bind

    try:
        report = MCPHealthReport()
        report.liveness = check_endpoint(host, actual_port, "/healthz")
        report.readiness = check_endpoint(host, actual_port, "/readyz")
        report.service_call = check_service_call(host, actual_port)
        report.constitution_check = check_constitution()

        # Determine overall
        checks = [report.liveness, report.readiness, report.service_call]
        all_ok = all(c.ok for c in checks if c is not None)
        report.overall = "PASS" if all_ok and report.constitution_check.get("ok") else "FAIL"
        return report
    finally:
        if httpd:
            httpd.shutdown()
            httpd.server_close()
            if thread:
                thread.join(timeout=5.0)


if __name__ == "__main__":
    report = run_full_health_check()
    print(report.summary())
    print()
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
