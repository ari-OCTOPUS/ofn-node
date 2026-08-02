# -*- coding: utf-8 -*-
"""octopus_mcp.server — سرورِ MCP ِ محلیِ read-only روی vault ِ F:\backup.

قرارداد (CONSTITUTION.md همین پوشه):
  * سطحِ ابزارِ این سرور read-only است — نه چون درخت بکاپ است (نیست؛ درختِ
    زنده است)، بلکه چون ایجنت‌های بیرونی فقط از مسیرِ «پیشنهاد → صفِ تأیید»
    حقِ اثر دارند. تنها ابزارِ نویسنده `propose_action` است که JSON به
    `_octopus/queue/pending/` می‌اندازد — همان صفی که policy.yaml حاکمش است.
  * دفاعِ مسیر: اول resolve، بعد قضاوت (درسِ resolve-before-you-judge-a-path)
    + الگوهای `.agentignore` + سقفِ بایتِ خروجی.

ترابرد: MCP stdio — JSON-RPC 2.0 ِ خط‌به‌خط (newline-delimited)، بدون وابستگیِ pip.
اجرا:  python -X utf8 _ops/octopus_mcp/server.py
"""
from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # F:\backup
QUEUE_PENDING = ROOT / "_octopus" / "queue" / "pending"
WORKSPACE = ROOT / "_octopus" / "workspace"

MAX_SLICE_BYTES = 64 * 1024      # سقفِ هر read_file_slice
MAX_SEARCH_LINES = 200           # سقفِ خطوطِ خروجیِ جستجو
MAX_TREE_ENTRIES = 500           # سقفِ ردیف‌های list_tree
PROTOCOL_VERSION = "2025-06-18"

# ---------------------------------------------------------------- path guard

def _load_agentignore() -> list[str]:
    pats: list[str] = []
    p = ROOT / ".agentignore"
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pats.append(line.rstrip("/"))
    except OSError:
        # fail-closed: بدونِ فهرستِ ممنوع، هیچ مسیری مجاز نیست
        pats.append("**")
    return pats

_IGNORE_PATS = _load_agentignore()
# ممنوعِ ساختاریِ خودِ سرور، مستقل از .agentignore:
_HARD_DENY = (".git", "_code", "node_modules", "__pycache__")


def _denied(rel: str) -> str | None:
    """نامِ الگویی که مسیر را می‌بندد، یا None اگر مجاز است."""
    parts = rel.replace("\\", "/").split("/")
    for seg in parts:
        if seg in _HARD_DENY:
            return f"hard-deny:{seg}"
    unix = rel.replace("\\", "/")
    base = parts[-1] if parts else ""
    for pat in _IGNORE_PATS:
        cp = pat.replace("\\", "/").strip("/")
        # الگوی دایرکتوری/پیشوندی: هر مسیری زیرش بسته است
        if unix == cp or unix.startswith(cp + "/"):
            return pat
        # الگوی glob روی کلِ مسیر و روی نامِ فایل (پوششِ *wallet* و مانندش)
        if fnmatch.fnmatch(unix, cp) or fnmatch.fnmatch(base, cp):
            return pat
        if cp.startswith("**/") and fnmatch.fnmatch(unix, cp[3:]):
            return pat
    return None


def _resolve(user_path: str) -> Path:
    """اول resolve، بعد قضاوت — سپس چکِ ریشه و چکِ ممنوعیت."""
    p = (ROOT / user_path).resolve() if not Path(user_path).is_absolute() else Path(user_path).resolve()
    try:
        rel = p.relative_to(ROOT)
    except ValueError:
        raise PermissionError(f"outside-root: {p}")
    why = _denied(str(rel))
    if why:
        raise PermissionError(f"agentignore:{why}")
    return p

# ---------------------------------------------------------------- tools

def t_list_tree(path: str = ".", depth: int = 2) -> dict:
    base = _resolve(path)
    if not base.is_dir():
        raise FileNotFoundError(f"not-a-dir: {path}")
    depth = max(1, min(int(depth), 4))
    rows, truncated = [], False
    stack = [(base, 0)]
    while stack:
        d, lvl = stack.pop()
        try:
            entries = sorted(d.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except OSError:
            continue
        for e in entries:
            rel = str(e.relative_to(ROOT))
            if _denied(rel):
                continue
            if len(rows) >= MAX_TREE_ENTRIES:
                truncated = True
                stack.clear()
                break
            st = e.stat()
            rows.append({
                "path": rel,
                "kind": "dir" if e.is_dir() else "file",
                "size": None if e.is_dir() else st.st_size,
                "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
            })
            if e.is_dir() and lvl + 1 < depth:
                stack.append((e, lvl + 1))
    # سقفِ ساکت ممنوع (درسِ no-silent-caps): برش را اعلام کن
    return {"root": str(base.relative_to(ROOT)) or ".", "entries": rows, "truncated": truncated}


def t_read_file_slice(path: str, offset: int = 0, length: int = MAX_SLICE_BYTES) -> dict:
    p = _resolve(path)
    if not p.is_file():
        raise FileNotFoundError(f"not-a-file: {path}")
    offset = max(0, int(offset))
    length = max(1, min(int(length), MAX_SLICE_BYTES))
    size = p.stat().st_size
    with open(p, "rb") as fh:
        fh.seek(offset)
        blob = fh.read(length)
    text = blob.decode("utf-8", errors="replace")
    return {
        "path": str(p.relative_to(ROOT)),
        "offset": offset,
        "bytes_returned": len(blob),
        "file_size": size,
        "eof": offset + len(blob) >= size,
        "content": text,
    }


def t_hash_file(path: str) -> dict:
    p = _resolve(path)
    if not p.is_file():
        raise FileNotFoundError(f"not-a-file: {path}")
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return {"path": str(p.relative_to(ROOT)), "sha256": h.hexdigest(), "size": p.stat().st_size}


def _git_ls_files() -> list[str]:
    """فهرستِ tracked — ایندکس‌خوانی است نه دیسک‌گردی (درسِ recursive-scan-hangs)."""
    try:
        ls = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=30)
        return ls.stdout.splitlines()
    except OSError:
        return []


def _rg_search(query: str, base: Path, glob: str, cap: int) -> tuple[list[dict], str]:
    cmd = ["rg", "-n", "--no-heading", "-S", "-m", "5", "--max-columns", "300"]
    if glob:
        cmd += ["-g", glob]
    cmd += ["--", query, str(base)]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], str(exc)
    hits = []
    for line in cp.stdout.splitlines():
        m = re.match(r"^(.*?):(\d+):(.*)$", line)
        if not m:
            continue
        try:
            rel = str(Path(m.group(1)).resolve().relative_to(ROOT))
        except ValueError:
            continue
        if _denied(rel):
            continue
        hits.append({"path": rel, "line": int(m.group(2)), "text": m.group(3)[:300]})
        if len(hits) >= cap:
            break
    err = cp.stderr.strip()[:200] if cp.returncode not in (0, 1) else ""
    return hits, err


def _py_search(query: str, base: Path, glob: str, cap: int) -> tuple[list[dict], str]:
    """fallback بدونِ rg: فقط فایل‌های tracked زیرِ base — هرگز os.walk روی کلِ درخت."""
    prefix = str(base.relative_to(ROOT)).replace("\\", "/")
    prefix = "" if prefix == "." else prefix + "/"
    smart_ci = query == query.lower()
    needle = query.lower() if smart_ci else query
    hits, scanned = [], 0
    for rel in _git_ls_files():
        if prefix and not rel.startswith(prefix):
            continue
        if glob and not fnmatch.fnmatch(Path(rel).name, glob):
            continue
        if _denied(rel):
            continue
        p = ROOT / rel
        try:
            if p.stat().st_size > 2 * 1024 * 1024:
                continue
            scanned += 1
            if scanned > 3000:
                return hits, "file-scan-cap-3000-reached"
            per_file = 0
            with open(p, encoding="utf-8", errors="replace") as fh:
                for no, line in enumerate(fh, 1):
                    hay = line.lower() if smart_ci else line
                    if needle in hay:
                        hits.append({"path": rel, "line": no, "text": line.rstrip()[:300]})
                        per_file += 1
                        if len(hits) >= cap:
                            return hits, ""
                        if per_file >= 5:
                            break
        except OSError:
            continue
    return hits, ""


def t_search_hybrid(query: str, path: str = ".", glob: str = "", max_results: int = 50) -> dict:
    """جستجوی محتوا (rg، وگرنه fallback ِ tracked-only) + نامِ فایل، ممنوعیت‌آگاه."""
    base = _resolve(path)
    cap = max(1, min(int(max_results), MAX_SEARCH_LINES))
    if shutil.which("rg"):
        content_hits, err = _rg_search(query, base, glob, cap)
        engine = "rg"
    else:
        content_hits, err = _py_search(query, base, glob, cap)
        engine = "py-tracked-only"
    ql = query.lower()
    name_hits = [rel for rel in _git_ls_files()
                 if ql in Path(rel).name.lower() and not _denied(rel)][:20]
    return {"query": query, "engine": engine, "content": content_hits,
            "filenames": name_hits, "truncated": len(content_hits) >= cap,
            "search_error": err}


def t_propose_action(kind: str, summary: str, detail: str = "") -> dict:
    """تنها ابزارِ نویسنده: پیشنهاد به صفِ تأییدِ مالک. هرگز خودِ عمل را اجرا نمی‌کند."""
    allowed = {"move_file", "rename_file", "modify_file", "deduplicate", "archive", "report"}
    if kind not in allowed:
        raise ValueError(f"kind must be one of {sorted(allowed)}")
    QUEUE_PENDING.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^A-Za-z0-9\u0600-\u06FF-]+", "-", summary)[:48].strip("-") or "proposal"
    out = QUEUE_PENDING / f"{ts}-{slug}.json"
    payload = {"ts": ts, "kind": kind, "summary": summary, "detail": detail,
               "status": "pending", "source": "octopus_mcp"}
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out)
    return {"queued": str(out.relative_to(ROOT)), "status": "pending",
            "note": "منتظرِ تأییدِ مالک طبق _octopus/config/policy.yaml"}


TOOLS = {
    "list_tree": (t_list_tree, "فهرستِ درختیِ یک پوشه (سقف‌دار، ممنوعیت‌آگاه).",
                  {"path": {"type": "string"}, "depth": {"type": "integer"}}),
    "read_file_slice": (t_read_file_slice, "خواندنِ برشِ بایتیِ یک فایل (حداکثر ۶۴KB در هر فراخوانی).",
                        {"path": {"type": "string"}, "offset": {"type": "integer"},
                         "length": {"type": "integer"}}),
    "hash_file": (t_hash_file, "SHA-256 یک فایل — برای dedup و راستی‌آزماییِ نسخه.",
                  {"path": {"type": "string"}}),
    "search_hybrid": (t_search_hybrid, "جستجوی ترکیبی: محتوا با ripgrep + نامِ فایل از ایندکسِ گیت.",
                      {"query": {"type": "string"}, "path": {"type": "string"},
                       "glob": {"type": "string"}, "max_results": {"type": "integer"}}),
    "propose_action": (t_propose_action, "ثبتِ پیشنهادِ تغییر در صفِ تأییدِ مالک (هرگز اجرا نمی‌کند).",
                       {"kind": {"type": "string"}, "summary": {"type": "string"},
                        "detail": {"type": "string"}}),
}

# ---------------------------------------------------------------- JSON-RPC loop

def _tool_defs() -> list[dict]:
    defs = []
    for name, (_fn, desc, props) in TOOLS.items():
        req = ["path"] if "path" in props and name != "search_hybrid" else \
              (["query"] if name == "search_hybrid" else [])
        if name == "propose_action":
            req = ["kind", "summary"]
        defs.append({"name": name, "description": desc,
                     "inputSchema": {"type": "object", "properties": props, "required": req}})
    return defs


def _handle(msg: dict) -> dict | None:
    mid = msg.get("id")
    method = msg.get("method", "")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "octopus-vault", "version": "1.0.0"}}}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _tool_defs()}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name", "")
        args = params.get("arguments") or {}
        if name not in TOOLS:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32601, "message": f"unknown tool: {name}"}}
        try:
            out = TOOLS[name][0](**args)
            body = json.dumps(out, ensure_ascii=False, indent=1)
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": body}], "isError": False}}
        except (PermissionError, FileNotFoundError, ValueError, OSError, TypeError) as exc:
            return {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                "isError": True}}
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"unknown method: {method}"}}
    return None


def main() -> None:
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n")
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(msg)
        if resp is not None:
            stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            stdout.flush()


if __name__ == "__main__":
    main()
