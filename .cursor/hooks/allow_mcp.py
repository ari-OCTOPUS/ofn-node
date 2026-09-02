import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, allow, deny, append_ledger

# Deny-by-default allowlist. An unrecognised server name is a deny, matching the
# repository's deny-by-default network posture.
ALLOWED = {
    "octopus-repo",        # local read-only repo/telemetry server
    "sequential-thinking",
    "context7",
    "huggingface",
}
READ_ONLY_PREFIXES = ("list", "get", "read", "search", "query", "describe", "stat", "find")

d = read_input()
server = d.get("mcp_server_name") or ""
tool = (d.get("tool_name") or "").lower()

if server not in ALLOWED:
    append_ledger({"kind": "mcp_denied_unknown_server", "server": server, "tool": tool})
    deny(f"MCP server '{server}' is not on the allowlist.",
         "Unrecognised MCP servers are denied by default. Add it to .cursor/hooks/allow_mcp.py after owner review.")

if server == "octopus-repo" and not tool.startswith(READ_ONLY_PREFIXES):
    append_ledger({"kind": "mcp_denied_write_tool", "server": server, "tool": tool})
    deny(f"MCP tool '{tool}' on octopus-repo is not read-only.",
         "Only read-only tools are permitted on the repository server.")

append_ledger({"kind": "mcp_allowed", "server": server, "tool": tool})
allow()
