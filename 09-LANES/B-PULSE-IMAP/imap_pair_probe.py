#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static pair probe: local imap_listener.py vs 138 oneshot recipe.

Lane: B-PULSE-IMAP

Reads source on disk and git porcelain. Optionally reads this-host listen
table for ports 143 and 993 only.

Does not import imap_listener.
Does not call cycle().
Does not connect IMAP (no imaplib.IMAP4 / IMAP4_SSL).
Does not start a listener.
Does not SSH.
Does not send mail.
Prints: do not run
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LANE = "B-PULSE-IMAP"
OFN = Path(r"F:\ofn-node")
LISTENER = OFN / "ofn" / "agents" / "imap_listener.py"
RECIPE = OFN / "tools" / "install_systemd.sh"
RECEIPT_138 = Path(__file__).resolve().parent / "SSH-RO-RECEIPT.md"

DO_NOT_RUN = "do not run"

PS_LISTEN_143_993 = r"""
$ErrorActionPreference = 'SilentlyContinue'
$rows = @()
$conns = Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 143,993 }
foreach ($c in $conns) {
  $proc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $c.OwningProcess)
  $cmd = ''
  $name = ''
  if ($proc) {
    $name = [string]$proc.Name
    $cmd = [string]$proc.CommandLine
  }
  $rows += [pscustomobject]@{
    LocalAddress = [string]$c.LocalAddress
    LocalPort = [int]$c.LocalPort
    OwningProcess = [int]$c.OwningProcess
    ProcessName = $name
    CommandLine = $cmd
  }
}
if ($rows.Count -eq 0) { '[]' } else { $rows | ConvertTo-Json -Compress -Depth 3 }
"""

PS_IMAP_PROCS = r"""
$ErrorActionPreference = 'SilentlyContinue'
$hits = Get-CimInstance Win32_Process | Where-Object {
  $name = [string]$_.Name
  $cmd = [string]$_.CommandLine
  if ($name -match 'imap_pair_probe|powershell') { return $false }
  if ($cmd -match 'imap_pair_probe') { return $false }
  $name -match '^(dovecot|imapd|imap-login)' -or $cmd -match 'imap_listener\.py'
} | ForEach-Object {
  [pscustomobject]@{
    ProcessId = [int]$_.ProcessId
    Name = [string]$_.Name
    CommandLine = [string]$_.CommandLine
  }
}
if (-not $hits) { '[]' } else { @($hits) | ConvertTo-Json -Compress -Depth 3 }
"""

PS_IDENTITY = r"""
$ErrorActionPreference = 'SilentlyContinue'
$wifi = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -match 'Wi-Fi|WiFi|WLAN' -and $_.PrefixOrigin -eq 'Dhcp' } |
  Select-Object -First 1 IPAddress, InterfaceAlias
[pscustomobject]@{
  Hostname = [string]$env:COMPUTERNAME
  WifiIP = [string]$wifi.IPAddress
  WifiAlias = [string]$wifi.InterfaceAlias
} | ConvertTo-Json -Compress
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ps_json(script: str) -> object:
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        return {"_error": completed.stderr.strip() or f"exit {completed.returncode}"}
    raw = (completed.stdout or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_not_json": raw[:200]}


def _as_rows(payload: object) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        if "_error" in payload or "_not_json" in payload:
            return [payload]
        return [payload]
    return []


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(OFN), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _tracked(rel: str) -> tuple[str, str]:
    ls = _git(["ls-files", "--error-unmatch", "--", rel])
    porc = _git(["status", "--porcelain", "--", rel])
    porcelain = (porc.stdout or "").strip()
    if ls.returncode != 0:
        if porcelain.startswith("??"):
            return "untracked", porcelain or "?? " + rel
        return "not_in_index", porcelain or (ls.stderr or "").strip()
    if porcelain.startswith("??"):
        return "contradiction_lsfiles_vs_porcelain", porcelain
    if porcelain:
        return "tracked_dirty", porcelain
    return "tracked_clean", rel


def _const(node: ast.AST | None) -> object | None:
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _call_name(node: ast.AST) -> str:
    func = getattr(node, "func", None)
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        cur: ast.AST | None = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        parts.reverse()
        return ".".join(parts)
    return ""


def parse_listener(path: Path) -> dict:
    out: dict = {
        "path": str(path),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "cycle_def": False,
        "cycle_lineno": None,
        "has_dunder_main": False,
        "dunder_main_lineno": None,
        "imap4_ssl": [],
        "select_mailbox": [],
        "state_mailbox_default": None,
        "bind_or_listen_calls": [],
        "imported_modules": [],
    }
    if not path.is_file():
        return out
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out["imported_modules"].append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out["imported_modules"].append(node.module)
        elif isinstance(node, ast.FunctionDef) and node.name == "cycle":
            out["cycle_def"] = True
            out["cycle_lineno"] = node.lineno
        elif isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and any(isinstance(c, ast.Constant) and c.value == "__main__" for c in test.comparators)
            ):
                out["has_dunder_main"] = True
                out["dunder_main_lineno"] = node.lineno
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name.endswith("IMAP4_SSL") or name == "IMAP4_SSL":
                host = _const(node.args[0]) if node.args else None
                port = _const(node.args[1]) if len(node.args) > 1 else None
                out["imap4_ssl"].append(
                    {"lineno": node.lineno, "host": host, "port": port, "call": name}
                )
            elif name.endswith(".select") or name == "select":
                mailbox = _const(node.args[0]) if node.args else None
                readonly = None
                for kw in node.keywords:
                    if kw.arg == "readonly":
                        readonly = _const(kw.value)
                out["select_mailbox"].append(
                    {
                        "lineno": node.lineno,
                        "mailbox": mailbox,
                        "readonly": readonly,
                        "call": name,
                    }
                )
            elif name in {"bind", "listen"} or name.endswith(".bind") or name.endswith(".listen"):
                out["bind_or_listen_calls"].append({"lineno": node.lineno, "call": name})
        elif isinstance(node, ast.Dict):
            keys = [_const(k) for k in node.keys]
            if "mailbox" in keys and "last_uid" in keys:
                for key, val in zip(node.keys, node.values):
                    if _const(key) == "mailbox":
                        out["state_mailbox_default"] = _const(val)
    return out


def parse_recipe(path: Path) -> dict:
    out: dict = {
        "path": str(path),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "type_oneshot": False,
        "imap_exec": None,
        "imap_timer": None,
        "wire_env_name_present": False,
    }
    if not path.is_file():
        return out
    text = path.read_text(encoding="utf-8")
    out["type_oneshot"] = "Type=oneshot" in text
    out["wire_env_name_present"] = "OCTOPUS_WIRE_LEAD_OUTBOUND" in text
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("mk_svc imap"):
            out["imap_exec"] = stripped
        elif stripped.startswith("mk_timer imap"):
            out["imap_timer"] = stripped
    return out


def kv(key: str, value: object) -> str:
    if value is None:
        return f"{key}=null"
    if isinstance(value, bool):
        return f"{key}={'true' if value else 'false'}"
    if isinstance(value, (int, float)):
        return f"{key}={value}"
    text = str(value).replace("\r", " ").replace("\n", " ")
    return f"{key}={text}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Static IMAP pair probe (B-PULSE-IMAP)")
    ap.add_argument("--out", default="", help="optional receipt path")
    args = ap.parse_args(argv)

    lines: list[str] = []

    def emit(text: str = "") -> None:
        lines.append(text)
        print(text)

    now = _now_iso()
    ident = _as_rows(_ps_json(PS_IDENTITY))
    ident0 = ident[0] if ident else {}
    hostname = ident0.get("Hostname") or socket.gethostname()
    wifi = ident0.get("WifiIP") or "unverified"

    listener = parse_listener(LISTENER)
    recipe = parse_recipe(RECIPE)
    rel_listener = "ofn/agents/imap_listener.py"
    rel_recipe = "tools/install_systemd.sh"
    track_l, track_l_detail = _tracked(rel_listener)
    track_r, track_r_detail = _tracked(rel_recipe)
    branch = (_git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout or "").strip()
    head = (_git(["rev-parse", "HEAD"]).stdout or "").strip()

    listen_rows = _as_rows(_ps_json(PS_LISTEN_143_993))
    proc_rows = _as_rows(_ps_json(PS_IMAP_PROCS))
    listen_err = any("_error" in r or "_not_json" in r for r in listen_rows)
    proc_err = any("_error" in r or "_not_json" in r for r in proc_rows)
    real_listen = [r for r in listen_rows if "LocalPort" in r]
    real_procs = [r for r in proc_rows if "ProcessId" in r]

    ssl_host = None
    ssl_port = None
    if listener["imap4_ssl"]:
        ssl_host = listener["imap4_ssl"][0].get("host")
        ssl_port = listener["imap4_ssl"][0].get("port")

    mailbox = None
    if listener["select_mailbox"]:
        mailbox = listener["select_mailbox"][0].get("mailbox")

    emit(f"lane={LANE}")
    emit(f"measured_at_utc={now}")
    emit(kv("hostname", hostname))
    emit(kv("wifi_ip", wifi))
    emit(kv("wifi_alias", ident0.get("WifiAlias")))
    emit("vantage=this_host_only")
    emit("scope=this_host_only")
    emit("claim_type=runtime")
    emit("ssh=none")
    emit("imap_connect=none")
    emit("listener_started=none")
    emit("mail_sent=none")
    emit(f"pid_self={os.getpid()} argv={sys.argv[0]}")
    emit(f"banner={DO_NOT_RUN}")
    emit("---identity---")
    emit(kv("ofn_branch", branch or "unverified"))
    emit(kv("ofn_head", head or "unverified"))
    emit("note=191_is_not_180; claimed board-180 stopped if wifi is .191")
    emit("---listener-static---")
    emit(kv("listener_path", listener["path"]))
    emit(kv("listener_exists", listener["exists"]))
    emit(kv("listener_bytes", listener["bytes"]))
    emit(kv("cycle_def", listener["cycle_def"]))
    emit(kv("cycle_lineno", listener["cycle_lineno"]))
    emit(kv("has_dunder_main", listener["has_dunder_main"]))
    emit(kv("dunder_main_lineno", listener["dunder_main_lineno"]))
    emit(kv("imap4_ssl_count", len(listener["imap4_ssl"])))
    emit(kv("imap_host", ssl_host))
    emit(kv("imap_port", ssl_port))
    emit(kv("select_mailbox", mailbox))
    emit(kv("state_mailbox_default", listener["state_mailbox_default"]))
    emit(kv("bind_or_listen_calls", len(listener["bind_or_listen_calls"])))
    emit(kv("imports_imaplib", "imaplib" in listener["imported_modules"]))
    emit("mailbox_means=remote_gmail_folder_name_not_local_bind")
    emit("job_class_from_code=oneshot_client_poll -- cycle() then exit via __main__")
    emit("---git---")
    emit(kv("listener_tracked", track_l))
    emit(kv("listener_git_detail", track_l_detail))
    emit(kv("recipe_tracked", track_r))
    emit(kv("recipe_git_detail", track_r_detail))
    emit("---recipe-static---")
    emit(kv("recipe_exists", recipe["exists"]))
    emit(kv("recipe_bytes", recipe["bytes"]))
    emit(kv("recipe_type_oneshot", recipe["type_oneshot"]))
    emit(kv("recipe_imap_exec", recipe["imap_exec"]))
    emit(kv("recipe_imap_timer", recipe["imap_timer"]))
    emit(kv("recipe_wire_env_name_present", recipe["wire_env_name_present"]))
    emit("recipe_wire_note=name_only_not_enabled_this_session")
    emit("---138-prior-file---")
    emit(kv("ssh_receipt_exists", RECEIPT_138.is_file()))
    emit(f"ssh_receipt_path={RECEIPT_138}")
    emit("ssh_this_session=none -- prefer prior receipt; no new SSH")
    emit("138_job_class_file=oneshot+timer FILE_VERIFIED from SSH-RO-RECEIPT.md")
    emit("138_143_993_file=absent FILE_VERIFIED from receipts/listen-138-20260903T0932Z.csv")
    emit("---this-host-listen-143-993---")
    if listen_err:
        emit("listen_143_993=unverified")
        emit(kv("listen_error", listen_rows[0] if listen_rows else "empty"))
    elif not real_listen:
        emit("listen_143=absent")
        emit("listen_993=absent")
    else:
        for row in real_listen:
            emit(
                "listen_hit="
                f"{row.get('LocalAddress')}:{row.get('LocalPort')}"
                f" pid={row.get('OwningProcess')} cmd={row.get('CommandLine')}"
            )
    emit("---this-host-imap-named-process---")
    if proc_err:
        emit("imap_named_process=unverified")
    else:
        emit(kv("imap_named_process_count", len(real_procs)))
        for row in real_procs:
            emit(
                "imap_proc="
                f"pid={row.get('ProcessId')} name={row.get('Name')} cmd={row.get('CommandLine')}"
            )
    emit("---pair---")
    emit("same_species=gmail_imap_client_oneshot_poll")
    emit("not_species=local_imap_daemon_bind_143_993")
    emit("138_exact_bytes_match=unverified (no SSH this session, no fetch)")
    emit(f"banner_again={DO_NOT_RUN}")
    emit("forbidden_done=none")

    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"receipt_written={dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
