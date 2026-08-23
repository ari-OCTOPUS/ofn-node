# -*- coding: utf-8 -*-
"""octopus_mcp.server — سرورِ MCP ِ محلیِ read-only روی vault ِ F:\backup.

قرارداد (CONSTITUTION.md همین پوشه):
  * سطحِ ابزارِ این سرور read-only است — نه چون درخت بکاپ است (نیست؛ درختِ
    زنده است)، بلکه چون ایجنت‌های بیرونی فقط از مسیرِ «پیشنهاد → صفِ تأیید»
    حقِ اثر دارند. تنها ابزارِ نویسنده `propose_action` است که JSON به
    `_octopus/queue/pending/` می‌اندازد — همان صفی که policy.yaml حاکمش است.
  * دفاعِ مسیر: اول resolve، بعد قضاوت (درسِ resolve-before-you-judge-a-path)
    + الگوهای `.agentignore` + سقفِ بایتِ خروجی.

ترابرد (هر دو، بدون وابستگیِ pip — فقط stdlib):
  * stdio (پیش‌فرض): JSON-RPC 2.0 ِ خط‌به‌خط (newline-delimited) — همان که .mcp.json می‌خواند.
  * HTTP stateless: `--http [HOST:]PORT` — ترابردِ Streamable HTTP ِ spec ِ
    2025-06-18 در حالتِ stateless: هر POST مستقل، بدونِ session، بدونِ
    Mcp-Session-Id (ممنوعِ کدِ نو طبقِ مگاپرامپتِ G5)، پاسخِ application/json
    (نه SSE)، GET/DELETE رویِ endpoint = 405.
اجرا:  python -X utf8 _ops/octopus_mcp/server.py [--http [HOST:]PORT]
"""
from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # F:\backup
QUEUE_PENDING = ROOT / "_octopus" / "queue" / "pending"
WORKSPACE = ROOT / "_octopus" / "workspace"

MAX_SLICE_BYTES = 64 * 1024      # سقفِ هر read_file_slice
MAX_SEARCH_LINES = 200           # سقفِ خطوطِ خروجیِ جستجو
MAX_TREE_ENTRIES = 500           # سقفِ ردیف‌های list_tree
PROTOCOL_VERSION = "2025-06-18"
# نسخه‌هایی که negotiation می‌پذیریم (شکلِ پیام‌ها در همهٔ این‌ها یکی است).
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")

# هویتِ سرور — یک منبعِ واحد برای هر دو مسیرِ `initialize` و `server/discover`.
# (قبلاً فقط داخلِ پاسخِ initialize inline بود؛ دو نسخهٔ جدا از هم می‌رانَد.)
SERVER_NAME = "octopus-vault"
SERVER_VERSION = "1.2.0"          # 1.1.0 → 1.2.0: افزودنِ server/discover

# --- server/discover (رویزیونِ 2026-07-28) ---------------------------------
# اسپکِ 2026-07-28 می‌گوید سرورها **MUST** این RPC را داشته باشند، و برای stdio
# نقشِ «backward-compatibility probe» را بازی می‌کند: کلاینتِ dual-era اول این را
# می‌فرستد و «روی هر خطایی که خطای شناخته‌شدهٔ modern نباشد» به `initialize`
# برمی‌گردد.
#
# ⚠ نکتهٔ صداقت — چرا `2026-07-28` در supportedVersions **نیست**:
#   این سرور هیچ‌کدام از الزاماتِ رویزیونِ modern را پیاده نکرده است — نه خواندنِ
#   نسخه از `_meta`، نه MRTR، نه `resultType` روی بقیهٔ نتایج، نه
#   `subscriptions/listen`. طبقِ ماتریسِ سازگاریِ خودِ اسپک، ادعای پشتیبانی
#   باعث می‌شود کلاینت ما را «modern» تشخیص دهد و بعد هر درخواستِ modern شکست
#   بخورد — یعنی همان probe ای که این متد برایش وجود دارد را می‌شکنیم.
#   پس `DiscoverResult` فقط نسخه‌هایی را اعلام می‌کند که **واقعاً** سرو می‌شوند؛
#   کلاینتِ dual-era می‌بیند نسخهٔ modern نیست و درست به `initialize` برمی‌گردد.
#   این از خطای مبهمِ -32601 ِ قبلی **بیشتر** اطلاعات می‌دهد، نه کمتر.
DISCOVER_TTL_MS = 3_600_000       # نتیجهٔ discover ثابت است؛ کش‌کردن بی‌خطر
UNSUPPORTED_PROTOCOL_VERSION = -32022   # spec §error-codes (renumbered از -32004)
_META_PROTOCOL_VERSION = "io.modelcontextprotocol/protocolVersion"
_META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"

# --- ترابردِ HTTP stateless (فقط stdlib) -----------------------------------
HTTP_MAX_BODY = 1 * 1024 * 1024          # سقفِ بدنهٔ POST
HTTP_STARTED = time.monotonic()

# fallback ِ جستجوی پایتونی (وقتی rg نیست): سقفِ فایل‌های خوانده‌شده و بودجهٔ
# زمانِ نرم. هر دو روی cap/timeout نتیجهٔ **جزئی** برمی‌گردانند نه خالی — درسِ
# empty-on-cap: صفِ ۳۰۰۰ روی ریپوی ~۶.۴k فایل، match های بعد از ۳۰۰۰ را می‌بلعید.
_PY_SCAN_CAP = 20000
_PY_TIME_BUDGET_S = 8.0
# fallback بدونِ rg کنداست (خواندنِ کاملِ ~۶.۴k فایل). md/py را اول اسکن کن تا
# نتیجهٔ مفیدِ کشف زودتر از فایل‌های حجیمِ state (.json/.jsonl/.log) بیاید.
_PY_PREF_EXT = (".md", ".py", ".txt", ".yaml", ".yml")

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


def _match_terms(hay: str, terms: list[str]) -> bool:
    """AND روی همهٔ واژه‌ها — نه substringِ کلِ رشتهٔ کوئری. «beta alpha» باید
    خطی که «alpha ... beta» دارد را بیابد (مستقل از ترتیب). ریشهٔ باگِ خالی‌برگشتن."""
    return all(t in hay for t in terms)


def _find_rg() -> str | None:
    """rg را پیدا کن: env `OCTOPUS_RG_PATH` → PATH → محل‌های شناختهٔ ویندوز →
    `_ops/bin/rg.exe`. نبود = None (سرور می‌افتد رویِ fallback ِ پایتونی).
    این ماشین rg ِ سیستمی ندارد — پس fallback باید واقعاً کار کند."""
    env = os.environ.get("OCTOPUS_RG_PATH", "").strip()
    if env and Path(env).exists():
        return env
    w = shutil.which("rg")
    if w:
        return w
    for cand in (ROOT / "_ops" / "bin" / "rg.exe",
                 Path(r"C:\Program Files\Git\usr\bin\rg.exe"),
                 Path(r"C:\Program Files\Git\mingw64\bin\rg.exe")):
        if cand.exists():
            return str(cand)
    return None


def _rg_search(query: str, base: Path, glob: str, cap: int, rg_path: str) -> tuple[list[dict], str]:
    """کوئریِ چندواژه‌ای: rg فقط خطوطِ «کاندید» (شاملِ هر واژه) را می‌یابد؛ فیلترِ
    AND رویِ واژه‌ها اینجا می‌نشیند — همانِ قراردادِ _match_terms، مستقل از ترتیب.
    ریشهٔ باگ (2026-08-16، rg روی PATH آمد): الگوی خام به rg می‌رفت ⇒ عبارتِ
    پیوسته ⇒ «search rg» خطِ `_rg_search` را نمی‌یافت و «   » خطوطِ تورفتگی را
    hit می‌کرد. کوئریِ بدونِ واژه ⇒ empty-query، مثلِ fallback پایتونی."""
    terms = [t for t in query.split() if t]
    if not terms:
        return [], "empty-query"
    smart_ci = query == query.lower()
    if len(terms) == 1:
        pattern = terms[0]                              # تک‌واژه: regex-capableِ همیشگی
        and_filter = False
    else:
        pattern = "|".join(re.escape(t) for t in terms)  # کاندید‌ساز: هر واژه
        and_filter = True
    cmd = [rg_path, "-n", "--no-heading", "-S",
           "-m", "25" if and_filter else "5", "--max-columns", "300"]
    if glob:
        cmd += ["-g", glob]
    cmd += ["--", pattern, str(base)]
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
        text = m.group(3)
        if and_filter:
            # خطِ کاندید باید هر دو/همهٔ واژه‌ها را داشته باشد (-m 25 چون فیلتر
            # می‌کَند؛ ۵تای اولِ کاندید شاید همه‌شان one-term-only باشند)
            hay = text.lower() if smart_ci else text
            if not all(t in hay for t in terms):
                continue
        hits.append({"path": rel, "line": int(m.group(2)), "text": text[:300]})
        if len(hits) >= cap:
            break
    err = cp.stderr.strip()[:200] if cp.returncode not in (0, 1) else ""
    return hits, err


def _py_search(query: str, base: Path, glob: str, cap: int) -> tuple[list[dict], str]:
    """fallback بدونِ rg: فقط فایل‌های tracked زیرِ base — هرگز os.walk روی کلِ درخت.
    term-based (AND روی همهٔ واژه‌ها) نه substringِ کلِ رشته — «lead pipeline PROJECT»
    باید فایلی که هر سه واژه را دارد بیابد. روی cap/بودجهٔ زمان نتیجهٔ **جزئی**
    برمی‌گرداند نه خالی (درسِ empty-on-cap)."""
    prefix = str(base.relative_to(ROOT)).replace("\\", "/")
    prefix = "" if prefix == "." else prefix + "/"
    smart_ci = query == query.lower()
    terms = [t for t in (query.lower() if smart_ci else query).split() if t]
    if not terms:
        return [], "empty-query"
    hits, scanned, t0 = [], 0, time.monotonic()
    ordered = sorted(_git_ls_files(),
                     key=lambda r: 0 if r.lower().endswith(_PY_PREF_EXT) else 1)
    for rel in ordered:
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
            if scanned > _PY_SCAN_CAP:
                return hits, f"file-scan-cap-{_PY_SCAN_CAP}-reached (partial — مسیر/گلاب را باریک کن)"
            if scanned % 100 == 0 and time.monotonic() - t0 > _PY_TIME_BUDGET_S:
                return hits, "time-budget-reached (partial — مسیر/گلاب را باریک کن)"
            with open(p, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            low = text.lower() if smart_ci else text
            # early-out: کلِ فایل باید همهٔ واژه‌ها را داشته باشد (سریع؛ اکثرِ فایل‌ها
            # همین‌جا skip می‌شوند — این تفاوتِ هنگ با کارکرد است روی ~۶.۴k فایل).
            if not _match_terms(low, terms):
                continue
            per_file, first_any = 0, None
            for no, line in enumerate(text.splitlines(), 1):
                hay = line.lower() if smart_ci else line
                if _match_terms(hay, terms):
                    hits.append({"path": rel, "line": no, "text": line.rstrip()[:300]})
                    per_file += 1
                    if len(hits) >= cap:
                        return hits, ""
                    if per_file >= 5:
                        break
                elif first_any is None and any(t in hay for t in terms):
                    first_any = (no, line)
            # واژه‌ها در فایل هستند ولی روی یک خط نه — فایل را با اولین خطِ مرتبط رو کن
            if per_file == 0 and first_any is not None:
                hits.append({"path": rel, "line": first_any[0],
                             "text": first_any[1].rstrip()[:300]})
                if len(hits) >= cap:
                    return hits, ""
        except OSError:
            continue
    return hits, ""


def t_search_hybrid(query: str, path: str = ".", glob: str = "", max_results: int = 50) -> dict:
    """جستجوی محتوا (rg، وگرنه fallback ِ tracked-only) + نامِ فایل، ممنوعیت‌آگاه."""
    base = _resolve(path)
    cap = max(1, min(int(max_results), MAX_SEARCH_LINES))
    rg = _find_rg()
    if rg:
        content_hits, err = _rg_search(query, base, glob, cap, rg)
        engine = "rg"
    else:
        content_hits, err = _py_search(query, base, glob, cap)
        engine = "py-tracked-only"
    terms = [t for t in query.lower().split() if t]
    name_hits = [rel for rel in _git_ls_files()
                 if terms and _match_terms(Path(rel).name.lower(), terms)
                 and not _denied(rel)][:20]
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

# ---------------------------------------------------------------- readiness

def _ready_state() -> dict:
    """جداکردنِ health از readiness (الزامِ G5): alive بودن را /healthz می‌گوید؛
    «می‌توانم درست خدمت بدهم؟» را همین تابع — با دو عاملِ مؤثر بر کیفیتِ خدمت."""
    fail_closed = _IGNORE_PATS == ["**"]   # .agentignore غایب ⇒ همه‌چیز بسته
    engine = "rg" if _find_rg() else "py-tracked-only"
    reasons = []
    if fail_closed:
        reasons.append("agentignore-missing-fail-closed")
    if not ROOT.is_dir():
        reasons.append("root-missing")
    return {"ready": ROOT.is_dir(), "engine": engine,
            "agentignore_fail_closed": fail_closed,
            "degraded": reasons, "uptime_s": round(time.monotonic() - HTTP_STARTED, 1)}


# ---------------------------------------------------------------- HTTP stateless

class _StatelessHTTPHandler(BaseHTTPRequestHandler):
    """Streamable HTTP ِ stateless (spec 2025-06-18) — دستی، فقط stdlib.

    قواعدِ این ترابرد:
      * هیچ session ای وجود ندارد: header ِ Mcp-Session-Id نه صادر می‌شود نه
        پذیرفته می‌شود (کدِ نو نباید session بازی کند — مگاپرامپتِ G5).
      * POST /mcp → یک JSON-RPC در بدنه (batch در 2025-06-18 حذف شده ⇒ 400)؛
        پاسخِ عدد‌دار = 200 + application/json، notification = 202 + بدنهٔ خالی.
      * GET /mcp = 405 (سرورِ stateless استریمِ مستقلِ SSE نمی‌دهد)؛
        DELETE /mcp = 405 (session ای برای بستن نیست).
      * /healthz (liveness) و /readyz (readiness) جدا هستند.
      * دفاعِ DNS-rebinding: Host باید در allowlistِ محلی باشد وگرنه 403.
    """
    protocol_version = "HTTP/1.1"
    server_version = "octopus-mcp-stateless/1.1"
    # bind host به‌صورتِ per-server تزریق می‌شود ( پیش‌فرضِ کلاس در make_http_server)
    allow_hosts = {"localhost", "127.0.0.1", "[::1]"}

    def log_message(self, fmt, *args):  # خروجیِ stdio را در حالتِ stdio خراب نکند
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # -- گاردهای مشترک
    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").strip()
        # پورت را جدا کن (IPv6 با براکت): "127.0.0.1:8809" → "127.0.0.1"
        if host.startswith("["):
            host = host.split("]", 1)[0] + "]"
        else:
            host = host.rsplit(":", 1)[0] if ":" in host else host
        return host.lower() in self.allow_hosts

    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        if code >= 400:
            # ردِ زودهنگام بدنه را نخوانده — بستنِ اتصال تا بایت‌های باقیماندهٔ
            # بدنه، درخواستِ بعدیِ keep-alive نشود (وگرنه «Bad request version»).
            self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    # -- endpoint های ساده
    def do_GET(self) -> None:
        if not self._host_ok():
            return self._send_json(403, {"error": "host-not-allowed"})
        if self.path == "/healthz":          # liveness: پروسه‌ی زنده است؟
            return self._send_json(200, {"status": "alive",
                                         "uptime_s": round(time.monotonic() - HTTP_STARTED, 1)})
        if self.path == "/readyz":           # readiness: می‌توانم درست خدمت بدهم؟
            st = _ready_state()
            return self._send_json(200, st)
        if self.path.rstrip("/") == "/mcp":
            # stateless: استریمِ مستقلِ SSE نداریم — فقط POST
            self.send_response(405)
            self.send_header("Allow", "POST, OPTIONS")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_json(404, {"error": "not-found"})

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_DELETE(self) -> None:
        if not self._host_ok():
            return self._send_json(403, {"error": "host-not-allowed"})
        if self.path.rstrip("/") == "/mcp":
            self.send_response(405)         # session ای برای بستن نیست
            self.send_header("Allow", "POST, OPTIONS")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_json(404, {"error": "not-found"})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Allow", "POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    # -- مسیرِ اصلی
    def do_POST(self) -> None:
        if not self._host_ok():
            return self._send_json(403, {"error": "host-not-allowed"})
        if self.path.rstrip("/") != "/mcp":
            return self._send_json(404, {"error": "not-found"})
        if self.headers.get("Mcp-Session-Id"):
            # ما session صادر نکرده‌ایم؛ پذیرفتنِ شناسهٔ ناشناس = ادعای state ای که نیست
            return self._send_json(400, {"error": "stateless-server-no-sessions"})
        accept = (self.headers.get("Accept") or "").lower()
        if accept and "application/json" not in accept and "*/*" not in accept:
            return self._send_json(406, {"error": "accept-must-include-application/json"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > HTTP_MAX_BODY:
            return self._send_json(413, {"error": "body-size-1MB-max"})
        raw = self.rfile.read(n) if n else b""
        try:
            msg = json.loads(raw.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._send_json(400, {"error": "invalid-json"})
        if isinstance(msg, list):
            return self._send_json(400, {"error": "batch-removed-in-2025-06-18"})
        if not isinstance(msg, dict):
            return self._send_json(400, {"error": "message-must-be-object"})
        resp = _handle(msg)
        if resp is None:                    # notification — چیزی برای گفتن نیست
            return self._send(202, b"")
        self._send_json(200, resp)


def make_http_server(host: str, port: int) -> ThreadingHTTPServer:
    """ساختِ سرور (port=0 ⇒ ephemeral) — جدا از run-loop تا تست بتواند port را بردارد."""
    handler = type("BoundHandler", (_StatelessHTTPHandler,),
                   {"allow_hosts": {h.lower() for h in
                                    ({host} if host not in ("0.0.0.0", "::") else set()) |
                                    {"localhost", "127.0.0.1", "[::1]"}}})
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True
    return httpd


def serve_http(host: str, port: int) -> None:
    httpd = make_http_server(host, port)
    bound = httpd.server_address[1]
    sys.stderr.write(f"octopus-mcp stateless HTTP on http://{host}:{bound}/mcp "
                     f"(no sessions, no SSE stream)\n")
    sys.stderr.flush()
    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()




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


def _discover_result() -> dict:
    """`DiscoverResult` طبقِ spec 2026-07-28 §server/discover.

    فقط نسخه‌هایی که این سرور واقعاً سرو می‌کند اعلام می‌شوند — دلیلش در
    کامنتِ SUPPORTED_PROTOCOL_VERSIONS بالا.
    """
    return {
        "resultType": "complete",
        "supportedVersions": list(SUPPORTED_PROTOCOL_VERSIONS),
        "capabilities": {"tools": {}},
        "instructions": (
            "Read-only vault tools over the local tree. The only writer is "
            "propose_action, which queues a proposal for owner approval and "
            "never performs the action itself. This server speaks the listed "
            "legacy protocol versions and still answers the initialize "
            "handshake; it does not implement the 2026-07-28 modern revision."
        ),
        "ttlMs": DISCOVER_TTL_MS,
        "cacheScope": "public",
        "_meta": {_META_SERVER_INFO: {"name": SERVER_NAME,
                                      "version": SERVER_VERSION}},
    }


def _unsupported_version_error(mid, requested: str) -> dict:
    """`UnsupportedProtocolVersionError` — کد و شکلِ `data` طبقِ اسپک."""
    return {"jsonrpc": "2.0", "id": mid, "error": {
        "code": UNSUPPORTED_PROTOCOL_VERSION,
        "message": "Unsupported protocol version",
        "data": {"supported": list(SUPPORTED_PROTOCOL_VERSIONS),
                 "requested": requested}}}


def _handle(msg: dict) -> dict | None:
    mid = msg.get("id")
    method = msg.get("method", "")
    if method == "server/discover":
        # additive — مسیرِ `initialize` پایین دست‌نخورده می‌ماند (کلاینتِ
        # ثبت‌شدهٔ .mcp.json هنوز legacy است و با آن کار می‌کند).
        # isinstance صریح، نه `or {}`: اگر `params` یا `_meta` از نوعِ dict
        # نباشند (مثلاً رشته)، `.get` روی‌شان AttributeError می‌دهد — و چون
        # حلقهٔ stdio ِ `main()` دورِ `_handle` هیچ try ندارد، یک probe ِ بدشکل
        # کلِ پروسهٔ سرور را می‌کشت. تستِ malformed همین را گرفت.
        _params = msg.get("params")
        _meta = _params.get("_meta") if isinstance(_params, dict) else None
        want = _meta.get(_META_PROTOCOL_VERSION) if isinstance(_meta, dict) else None
        if want is not None and want not in SUPPORTED_PROTOCOL_VERSIONS:
            # نسخهٔ صریحاً درخواست‌شده را سرو نمی‌کنیم ⇒ خطای اسپک‌محور که
            # فهرستِ نسخه‌های واقعی را هم می‌دهد (کلاینت یا نسخهٔ مشترک را
            # انتخاب می‌کند یا صادقانه به مالکش خطا نشان می‌دهد).
            return _unsupported_version_error(mid, str(want))
        return {"jsonrpc": "2.0", "id": mid, "result": _discover_result()}
    if method == "initialize":
        # negotiation (spec §versioning): نسخهٔ خواسته‌شده اگر می‌دانیم همان
        # برگردد؛ وگرنه نسخهٔ خودمان — کلاینت یا می‌پذیرد یا قطع می‌کند.
        want = (msg.get("params") or {}).get("protocolVersion")
        ver = want if want in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": ver,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}}}
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


def _parse_http_arg(argv: list[str]) -> tuple[str, int] | None:
    """`--http` / `--http 127.0.0.1:8809` / `--http 8809` → (host, port)؛
    بدونِ --http = None (همان stdio ِ همیشگی). bind پیش‌فرض 127.0.0.1."""
    if "--http" not in argv:
        return None
    i = argv.index("--http")
    val = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else ""
    if not val:
        return "127.0.0.1", 8809
    if val.isdigit():
        return "127.0.0.1", int(val)
    host, _, port = val.rpartition(":")
    if not host or not port.isdigit():
        raise SystemExit("usage: --http [HOST:]PORT   (e.g. --http 127.0.0.1:8809)")
    return host, int(port)


def main() -> None:
    http = _parse_http_arg(sys.argv[1:])
    if http is not None:
        serve_http(*http)
        return
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
