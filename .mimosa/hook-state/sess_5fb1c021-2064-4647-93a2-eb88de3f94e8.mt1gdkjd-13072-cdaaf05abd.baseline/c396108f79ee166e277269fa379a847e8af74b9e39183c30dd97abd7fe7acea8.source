#!/usr/bin/env python3
r"""metadata_scan.py — نقشه‌برداریِ فقط‌خواندنیِ metadata از ریشهٔ پروژه (فاز ۲ اختاپوس).

نقش: یک walkِ استات روی درختِ فایل و فقط metadata می‌گیرد — path نسبی، type، size،
mtime، extension. **هیچ‌گاه محتوای فایل خوانده نمی‌شود** (مخصوصاً `.env` و سایر
secretها — فقط وجودشان به‌عنوان ردیفِ metadata ثبت می‌شود، هرگز bait/محتوا).

خروجی‌ها:
  - `F:\backup\_octopus\manifests\latest_manifest.json`   (آخرین اسکن)
  - `F:\backup\_octopus\manifests\history\manifest_<ts>.json` (آرشیو تاریخ‌دار)
  - `F:\backup\_octopus\state\metadata_scan.json`          (stateِ progress/idle)
  - `F:\backup\_octopus\reports\daily\metadata_scan_<ts>.md` (گزارش انسان‌خوانا)
  - append به `_octopus\logs\audit.log`                     (content-free)

قوانین ایمنی (سخت):
  1. فقط `os.scandir`/`stat` — هیچ `open()` روی محتوای فایل.
  2. excludeها: پوشه‌های سنگین/غیرلازم (.git, __pycache__, node_modules, venv, ...).
  3. hash سنگین فقط پشتِ `OCTOPUS_METADATA_HASH=1` و با سقفِ `max_hash_files`.
  4. `_octopus` خودش scan می‌شود ولی فقط metadata (مثل بقیه)؛ محتوا هرگز echo نمی‌شود.
  5. fail-soft: هر خطای یک فایل → skip + شمارش در errors، هرگز crashِ کلِ scan.
  6. قابلِ قطع: `max_files` سقفِ سخت (ثابتِ ماژول `MAP_SCAN_MAX_FILES`) + `max_seconds`.

صداقتِ نقشه (C9 — طرحِ یکپارچه‌سازیِ ۲۰۲۶-۰۸-۰۳):
  - `.claude` در `EXCLUDE_DIRS` است. اندازه‌گیری‌شده: از ۵۰٬۰۰۰ رکوردِ اسکنِ قبلی،
    ۴۹٬۹۳۹ تا زیرِ `.claude/worktrees/` بودند — نُه رونوشتِ کهنهٔ vault از برنچ‌های
    جلسه‌ای. یعنی این اسکنر **هرگز حتی یک نوتِ واقعیِ vault را ثبت نکرده**.
    (`.gitignore` از قبل `.claude/` را اعلام می‌کند ولی این اسکنر `.gitignore` نمی‌خواند.)
  - سقف در **ثابتِ ماژول** است نه در محلِ فراخوانی؛ هیچ call siteی حق ندارد
    `max_files` خودش را پاس بدهد وگرنه شکلِ نقشه را بی‌صدا بازتعریف می‌کند.
  - `truncated` درجه‌یک است (`files_seen >= max_files` یا سقفِ زمانی) و اسکنِ
    به‌سقف‌خورده باید `UNKNOWN` رندر شود — `count_display()` — حتی اگر عدد تولید کرده.

$0 · stdlib-only · import-time خالص. مصرف‌کننده: center.py (callback map:start).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

# ریشهٔ پروژه و خروجی‌ها — idiomِ telegram_center (parent.parent.parent = F:\backup).
_OPS = Path(__file__).resolve().parent.parent              # _ops
_ROOT = _OPS.parent                                         # F:\backup
_OCTOPUS = _ROOT / "_octopus"
_MANIFEST_DIR = _OCTOPUS / "manifests"
_HISTORY_DIR = _MANIFEST_DIR / "history"
_REPORTS_DIR = _OCTOPUS / "reports" / "daily"
_STATE_PATH = _OCTOPUS / "state" / "metadata_scan.json"
_AUDIT_PATH = _OCTOPUS / "logs" / "audit.log"

# ⚠️ C9: سقفِ فایل **فقط این‌جا** اعلام می‌شود. تا ۲۰۲۶-۰۸-۰۳ این عدد در
# `center.py::_handle_map_callback` به‌صورت `scan_metadata(max_files=50_000)`
# hardcode بود در حالی که ثابتِ ماژول ۲۰۰٬۰۰۰ بود — پس بالابردنِ ثابتِ ماژول
# هیچ اثری نداشت. حالا یک نام، یک مقدار؛ هر call siteی که `max_files` خودش را
# پاس بدهد تستِ `test_metadata_scan_honesty` را قرمز می‌کند.
MAP_SCAN_MAX_FILES = 50_000
DEFAULT_MAX_FILES = MAP_SCAN_MAX_FILES   # نامِ قدیمی، همان یک مقدار (هرگز دو سقف)
DEFAULT_MAX_SECONDS = 300          # ۵ دقیقه — سقفِ نرم برای scan کامل
MAX_HASH_FILES = 5_000             # hash فقط برای این تعدادِ نخست (پشت فلگ)
HASH_FLAG = "OCTOPUS_METADATA_HASH"

# پوشه‌هایی که نادیده گرفته می‌شوند (دقیقاً با نام، حساس به case روی ویندوز نه).
# `.claude`: نُه worktreeِ کهنه زیرِ `.claude/worktrees/` — ۴۹٬۹۳۹ از ۵۰٬۰۰۰ رکوردِ
# اسکنِ قبلی. رونوشتِ vault اند، نه خودِ vault؛ شمردنشان کارتِ نقشه را ۸ برابر می‌کرد.
EXCLUDE_DIRS = {
    ".git", ".claude", "__pycache__", ".pytest_cache", "node_modules",
    "venv", ".venv", "env", ".env", ".tox", ".mypy_cache", ".ruff_cache",
    "dist", "build", ".idea", ".vscode", ".cache",
}

# محتوای این فایل‌ها هرگز خوانده/echo نمی‌شود (حتی metadata حساس نیست، ولی این‌ها
# bait هستند — در گزارش فقط شمارش می‌آیند، نه نامِ کاملِ path). فعلاً هیچ pathی
# redact نمی‌شود چون pathهای پروژه از پیش public هستند؛ flag برای آینده.
_SECRET_PATTERNS = (".env",)        # فقط پسوند؛ فقط شمارش در گزارش


def _now_ts() -> str:
    """timestamp ISO برای نامِ فایل و state (با offset محلی)."""
    return time.strftime("%Y%m%dT%H%M%S", time.localtime())


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


# ─── state (اتمیک، fail-soft) ───────────────────────────────────────────────────
def _write_state(state: dict) -> bool:
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STATE_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, _STATE_PATH)
        return True
    except (OSError, TypeError, ValueError):
        return False


def load_state() -> dict:
    """state فعلیِ اسکن (idle/running/done/error + شمارش‌ها). fail-soft → {}."""
    try:
        if not _STATE_PATH.exists():
            return _default_state()
        d = json.loads(_STATE_PATH.read_text("utf-8"))
        return d if isinstance(d, dict) else _default_state()
    except (OSError, ValueError):
        return _default_state()


def _default_state() -> dict:
    return {
        "schema_version": 1,
        "status": "idle",
        "started_at": None,
        "finished_at": None,
        "files_seen": 0,
        "dirs_seen": 0,
        "bytes_total": 0,
        "last_error": None,
        "latest_manifest": None,
    }


def _audit(event: str, detail: str = "") -> None:
    """append به audit.log اختاپوس (JSON یک‌خطی، content-free)."""
    try:
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": _now_iso(), "event": event, "result": detail}
        with open(_AUDIT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ─── هستهٔ اسکن ──────────────────────────────────────────────────────────────────
def scan_metadata(root: "Path | None" = None, *,
                  max_files: int = MAP_SCAN_MAX_FILES,
                  max_seconds: float = DEFAULT_MAX_SECONDS,
                  hash_files: "bool | None" = None) -> dict:
    """یک walkِ فقط‌خواندنی. خروجی = manifest dict.

    `hash_files`: None → از env (OCTOPUS_METADATA_HASH)؛ True/False override.
    اگر True، برای نخستین `MAX_HASH_FILES` فایل، sha256(initial 64KB) گرفته می‌شود
    (sampler، نه کلِ فایل) تا dedupe سبک ممکن شود؛ بقیه بدون hash.

    fail-soft: خطای هر فایل/پوشه → skip + شمارش در errors؛ کلِ scan هرگز crash نمی‌کند.

    ⚠️ `max_files` را **پاس نده**؛ سقف ثابتِ ماژول (`MAP_SCAN_MAX_FILES`) است.
    پارامتر فقط برای تست/فیکسچر باقی مانده. (C9)

    `truncated` درجه‌یک است: `files_seen >= max_files` یا برخورد به سقفِ زمانی.
    مرزِ دقیق عمداً محافظه‌کارانه است — درختی با دقیقاً `max_files` فایل هم
    `truncated=True` می‌گیرد، چون از داخلِ walk نمی‌شود «تمام شد» را از
    «درست سرِ سقف بریده شد» تفکیک کرد؛ و ادعای «کامل» بدترین دروغ است.

    `by_top_dir`: شکستِ شمارشِ فایل به‌ازای هر پوشهٔ سطحِ‌یک (فایل‌های خودِ ریشه
    زیرِ کلیدِ `"."`). مجموعِ مقادیر همیشه `= files_seen`."""
    root = Path(root) if root is not None else _ROOT
    if hash_files is None:
        hash_files = os.environ.get(HASH_FLAG, "0") == "1"

    started = time.time()
    state = _default_state()
    state["status"] = "running"
    state["started_at"] = _now_iso()
    _write_state(state)

    result = {
        "schema_version": 1,
        "root": str(root),
        "scanned_at": _now_iso(),
        "files": [],
        "dirs": [],
        "top_extensions": {},        # {".py": (count, bytes)}
        "by_top_dir": {},            # {"03 - Projects": 812, ".": 14}
        "truncated": False,
        "truncated_reason": None,    # None | "max_files" | "max_seconds"
        "max_files": int(max_files),
        "max_seconds": float(max_seconds),
        "excluded_dirs": sorted(EXCLUDE_DIRS),
        "error_count": 0,
    }
    files_seen = dirs_seen = bytes_total = 0
    hash_budget = MAX_HASH_FILES if hash_files else 0
    errors = 0
    hit_time_cap = False

    try:
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            # فیلترِ excludeها روی‌جا (os.walk با mutate کردن dirnames بهینه است)
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

            rel_dir = os.path.relpath(dirpath, root)
            try:
                st_dir = os.stat(dirpath)
                dirs_seen += 1
                result["dirs"].append({
                    "path": "." if rel_dir == "." else rel_dir.replace("\\", "/"),
                    "mtime": int(st_dir.st_mtime),
                })
            except OSError:
                errors += 1

            # قطعِ زمانی
            if time.time() - started > max_seconds:
                hit_time_cap = True
                break

            for fn in filenames:
                if files_seen >= max_files:
                    break
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, root).replace("\\", "/")
                try:
                    st = os.lstat(full) if os.path.islink(full) else os.stat(full)
                except OSError:
                    errors += 1
                    continue
                ext = os.path.splitext(fn)[1].lower()
                size = int(st.st_size)
                entry = {
                    "path": rel,
                    "type": "link" if os.path.islink(full) else "file",
                    "size": size,
                    "mtime": int(st.st_mtime),
                    "ext": ext,
                }
                # hash sampler فقط پشت فلگ و با بودجه (هرگز روی .env)
                if hash_budget > 0 and not fn.endswith(_SECRET_PATTERNS) and size > 0:
                    h = _sample_hash(full)
                    if h:
                        entry["sha256_64k"] = h
                        hash_budget -= 1
                result["files"].append(entry)
                files_seen += 1
                bytes_total += size
                ext_stat = result["top_extensions"].setdefault(ext, [0, 0])
                ext_stat[0] += 1
                ext_stat[1] += size
                # شکستِ per-top-level-directory (فایلِ خودِ ریشه → کلیدِ ".")
                top = rel.split("/", 1)[0] if "/" in rel else "."
                result["by_top_dir"][top] = result["by_top_dir"].get(top, 0) + 1

            if files_seen >= max_files:
                break

    except OSError as e:
        errors += 1
        state["last_error"] = str(e)[:200]

    # ─── قطع‌شدگی، درجه‌یک ───────────────────────────────────────────────────
    # یک محاسبهٔ صریح در یک جا — نه یک فلگی که در سه شاخه ست می‌شود.
    hit_file_cap = files_seen >= max_files
    result["truncated"] = bool(hit_file_cap or hit_time_cap)
    result["truncated_reason"] = ("max_files" if hit_file_cap
                                  else "max_seconds" if hit_time_cap else None)
    result["by_top_dir"] = dict(sorted(result["by_top_dir"].items(),
                                       key=lambda kv: (-kv[1], kv[0])))

    # خلاصه
    elapsed = round(time.time() - started, 2)
    result["summary"] = {
        "files": files_seen,
        "dirs": dirs_seen,
        "bytes_total": bytes_total,
        "bytes_human": _human_bytes(bytes_total),
        "errors": errors,
        "elapsed_s": elapsed,
        "hash_sampled": (MAX_HASH_FILES - hash_budget) if hash_files else 0,
        "scanned_at": _now_iso(),
        "truncated": result["truncated"],
        "truncated_reason": result["truncated_reason"],
    }
    # مرتب‌سازیِ top extensions (با tuple (count, bytes) که JSON قابلیت serialize دارد)
    result["top_extensions"] = {
        k: list(v) for k, v in sorted(
            result["top_extensions"].items(),
            key=lambda kv: kv[1][1], reverse=True)[:15]
    }

    state.update({
        "status": "done",
        "finished_at": _now_iso(),
        "files_seen": files_seen,
        "dirs_seen": dirs_seen,
        "bytes_total": bytes_total,
        "last_error": None if errors == 0 else f"{errors} errors during scan",
        "latest_manifest": None,   # write_manifest پر می‌کند
    })
    _write_state(state)
    return result


def _sample_hash(path: str, chunk: int = 65536) -> "str | None":
    """sha256 روی نخستین ۶۴KB فایل (sampler برای dedupe سبک). هرگز کلِ فایلِ بزرگ.

    fail-soft: هر خطای خواندن → None (این فایل بدون hash می‌ماند، کل scan ادامه می‌یابد).
    توجه: این تابع محتوای فایل را می‌خواند — ولی فقط برای hash، نه برای echo/log.
    به‌هیچ‌عنوان برای فایل‌های _SECRET_PATTERNS صدا زده نمی‌شود (گیت در scan_metadata)."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:           # noqa: SIM115 — sample کوتاه، با تایید path
            h.update(f.read(chunk))
        return h.hexdigest()
    except OSError:
        return None


def _human_bytes(n: int) -> str:
    """8723 → '8.5 KiB'. برای گزارشِ انسان‌خوانا."""
    n = int(n or 0)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


# ─── persist ────────────────────────────────────────────────────────────────────
def write_manifest(result: dict) -> dict:
    """نوشتنِ latest + history + گزارش markdown + audit. خروجی = مسیرها.

    اتمیک (tmp + os.replace). fail-soft: هر شکست → dict با pathهای None."""
    ts = _now_ts()
    paths = {"latest": None, "history": None, "report": None, "state": None}
    try:
        _MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
        _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        latest = _MANIFEST_DIR / "latest_manifest.json"
        tmp = latest.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, latest)
        paths["latest"] = str(latest)

        hist = _HISTORY_DIR / f"manifest_{ts}.json"
        hist.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
        paths["history"] = str(hist)
    except OSError:
        pass

    # گزارشِ انسان‌خوانا
    try:
        report_md = _summarize_to_md(result)
        rp = _REPORTS_DIR / f"metadata_scan_{ts}.md"
        rp.write_text(report_md, "utf-8")
        paths["report"] = str(rp)
    except OSError:
        pass

    # به‌روزرسانیِ state با مسیرِ latest
    st = load_state()
    st["latest_manifest"] = paths["latest"]
    st["status"] = "done"
    _write_state(st)
    paths["state"] = str(_STATE_PATH)

    s = result.get("summary", {}) if isinstance(result, dict) else {}
    _audit("metadata_scan",
           f"files={s.get('files', 0)} dirs={s.get('dirs', 0)} "
           f"bytes={s.get('bytes_human', '?')} truncated={result.get('truncated')}")
    return paths


UNKNOWN = "UNKNOWN"


def is_truncated(result: "dict | None") -> bool:
    """آیا این اسکن به سقف خورده؟ ورودیِ خراب/غایب ⇒ True (محافظه‌کارانه).

    یک خواننده (کارت، گزارش، toast) نباید خودش `files_seen >= max_files` را
    دوباره حساب کند؛ همین یک تابع پاسخ می‌دهد."""
    if not isinstance(result, dict):
        return True
    if "truncated" in result:
        return bool(result["truncated"])
    s = result.get("summary")
    if isinstance(s, dict) and "truncated" in s:
        return bool(s["truncated"])
    return True   # نمی‌دانیم ⇒ ادعای «کامل» نکن


def count_display(result: "dict | None", key: str = "files") -> str:
    """عددِ اسکن برای رندر — یا `UNKNOWN` اگر اسکن به سقف خورده باشد.

    C9: «اسکنی که به سقف بخورد باید UNKNOWN رندر کند **حتی اگر عدد تولید کرده
    باشد**.» عددِ بریده یک کف است، نه یک شمارش؛ نمایشش به‌عنوان شمارش همان
    دروغی است که کارتِ نقشه یک ماه می‌گفت (۱۶٬۱۶۲ در برابرِ ۲٬۱۲۷ markdownِ واقعی)."""
    if is_truncated(result):
        return UNKNOWN
    s = result.get("summary") if isinstance(result, dict) else None
    if not isinstance(s, dict) or not isinstance(s.get(key), int):
        return UNKNOWN
    return f"{s[key]:,}"


def summarize_manifest(result: dict) -> str:
    """خلاصهٔ کوتاهِ چندخطی برای toast/inline. content-free."""
    if not isinstance(result, dict):
        return "🐙 هنوز اسکنی انجام نشده."
    s = result.get("summary", {}) if isinstance(result.get("summary"), dict) else {}
    if not s:
        return "🐙 هنوز اسکنی انجام نشده."
    if is_truncated(result):
        why = result.get("truncated_reason") or s.get("truncated_reason") or "?"
        return (f"🗺️ نقشه: {UNKNOWN} فایل · {UNKNOWN} پوشه — اسکن به سقف خورد "
                f"({why}؛ دیده‌شده تا اینجا: {s.get('files', 0):,})")
    return (f"🗺️ نقشه: {s.get('files', 0):,} فایل · {s.get('dirs', 0):,} پوشه · "
            f"{s.get('bytes_human', '?')}")


def _summarize_to_md(result: dict) -> str:
    """گزارشِ markdown کامل‌تر برای reports/daily/."""
    s = result.get("summary", {}) if isinstance(result, dict) else {}
    exts = result.get("top_extensions", {}) if isinstance(result, dict) else {}
    tops = result.get("by_top_dir", {}) if isinstance(result, dict) else {}
    trunc = is_truncated(result)
    lines = [
        "# 🗺️ گزارش نقشه‌برداری metadata",
        "",
        f"- **تاریخ:** `{s.get('scanned_at', '?')}`",
        f"- **ریشه:** `{result.get('root', '?')}`",
        f"- **فایل‌ها:** `{count_display(result, 'files')}`",
        f"- **پوشه‌ها:** `{count_display(result, 'dirs')}`",
        f"- **دیده‌شده تا لحظهٔ قطع:** `{s.get('files', 0):,}` فایل"
        if trunc else f"- **حجم کل:** `{s.get('bytes_human', '?')}`",
        f"- **زمان اسکن:** `{s.get('elapsed_s', '?')}s`",
        f"- **خطاها:** `{s.get('errors', 0)}`",
        f"- **hash نمونه:** `{s.get('hash_sampled', 0)}`",
        f"- **ناقص (سقف):** {'بله' if trunc else 'خیر'}"
        + (f" — دلیل: `{result.get('truncated_reason')}`، "
           f"سقف: `{result.get('max_files')}` فایل / `{result.get('max_seconds')}` ثانیه"
           if trunc else ""),
        "",
        "## شکستِ پوشه‌های سطحِ یک",
        "",
        "| پوشه | فایل |",
        "|------|-----:|",
    ]
    for top, cnt in (tops.items() if isinstance(tops, dict) else []):
        lines.append(f"| `{top}` | {int(cnt):,} |")
    lines += [
        "",
        "## پراکندگیِ type (۱۵ تایِ بالا)",
        "",
        "| ext | تعداد | حجم |",
        "|-----|------:|-----:|",
    ]
    for ext, stat in (exts.items() if isinstance(exts, dict) else []):
        cnt, byts = (stat + [0, 0])[:2] if isinstance(stat, list) else (0, 0)
        lines.append(f"| `{ext or '(بدون پسوند)'}` | {int(cnt):,} | {_human_bytes(int(byts))} |")
    lines += [
        "",
        "## excludes",
        "",
        f"پوشه‌های نادیده‌گرفته‌شده: `{', '.join(sorted(EXCLUDE_DIRS))}`",
        "",
        "---",
        "*این گزارش فقط metadata است؛ هیچ محتوای فایل خوانده/نوشته نشده است.*",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    # دمو (روی ریشهٔ واقعی) — fail-soft، فقط metadata. سقفِ دمو عمداً پایین است
    # و `truncated=True` می‌دهد؛ خروجی هم صادقانه UNKNOWN می‌گوید.
    r = scan_metadata(max_files=1000, max_seconds=30)   # noqa: C9 — دمو، نه call siteِ تولیدی
    paths = write_manifest(r)
    print(summarize_manifest(r))
    print("paths:", paths)
