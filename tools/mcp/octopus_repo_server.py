#!/usr/bin/env python3
"""octopus_repo_server — سرور MCP فقط‌خواندنیِ ریپو (نقشهٔ سند تلاقی، گام ۴).

جای خالیِ پک Cursor (.cursor/mcp.json ← tools/mcp/octopus_repo_server.py).
JSON-RPC 2.0 روی stdio با حداقلِ MCP: initialize / tools/list / tools/call.
دروازهٔ سیگنال: ایجنت به‌جای اسکرپینگ، از اینجا تلمتریِ تاییدشده می‌خواند.
فقط‌خواندنی: --read-only الزامی؛ هر ابزار فقط خواندن/محاسبه است، صفر نوشتن.

اجرا: python3 tools/mcp/octopus_repo_server.py --read-only
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
REPO = HOME / "ofn"
READ_ONLY = "--read-only" in sys.argv

TOOLS = [
    {"name": "get_reconcile",
     "description": "Run the 6-invariant cross-store reconciliation (read-only) and return its JSON verdict.",
     "inputSchema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_lead_stats",
     "description": "Painting leads grouped by status + booked revenue total (read-only sqlite query).",
     "inputSchema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_wal_stats",
     "description": "Outbound WAL effects grouped by state (the send truth store).",
     "inputSchema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_git_log",
     "description": "Last N commits of release/p0 on the board.",
     "inputSchema": {"type": "object",
                     "properties": {"n": {"type": "integer", "default": 10}},
                     "required": []}},
    {"name": "get_memory_chain_verify",
     "description": "Verify the agent memory hash-chain integrity.",
     "inputSchema": {"type": "object", "properties": {}, "required": []}},
]


def _sqlite(db: Path, sql: str):
    import sqlite3
    c = sqlite3.connect(db)
    try:
        return [list(r) for r in c.execute(sql)]
    finally:
        c.close()


def tool_call(name: str, args: dict) -> dict:
    if not READ_ONLY:
        return {"error": "server must run with --read-only"}
    if name == "get_reconcile":
        r = subprocess.run([sys.executable, str(REPO / "tools/reconcile.py")],
                           capture_output=True, text=True, timeout=30)
        return {"rc": r.returncode,
                "report": json.loads(r.stdout) if r.stdout.strip() else None}
    if name == "get_lead_stats":
        db = HOME / ".local/share/ofn/painting.sqlite"
        by_status = _sqlite(db, "SELECT status, COUNT(*) FROM painting_leads "
                                 "GROUP BY status")
        booked = _sqlite(db, "SELECT COALESCE(SUM(booked_amount_cents),0) "
                             "FROM painting_leads")[0][0] / 100.0
        return {"by_status": dict(by_status), "booked_aud": booked}
    if name == "get_wal_stats":
        db = REPO / "ofn/agi2027_runtime/outbound-effects.sqlite3"
        rows = _sqlite(db, "SELECT state, COUNT(*) FROM outbound_effects "
                           "GROUP BY state")
        return {"by_state": dict(rows)}
    if name == "get_git_log":
        n = int(args.get("n", 10))
        r = subprocess.run(["git", "-C", str(REPO), "log", "--oneline",
                            f"-n{n}"], capture_output=True, text=True,
                           timeout=15)
        return {"log": r.stdout.strip().splitlines()}
    if name == "get_memory_chain_verify":
        sys.path.insert(0, str(REPO / "ofn/agents"))
        sys.path.insert(0, str(REPO / "ofn/budget"))
        import memory_chain
        return memory_chain.chain_verify()
    return {"error": f"unknown tool: {name}"}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method", "")
        rid = req.get("id")
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05",
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "octopus-repo",
                                     "version": "0.1.0",
                                     "readOnly": READ_ONLY}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = req.get("params") or {}
            out = tool_call(str(params.get("name")), params.get("arguments") or {})
            result = {"content": [{"type": "text",
                                   "text": json.dumps(out, ensure_ascii=False)}]}
        elif method == "ping":
            result = {}
        else:
            resp = {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32601, "message": "method not found"}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue
        resp = {"jsonrpc": "2.0", "id": rid, "result": result}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
