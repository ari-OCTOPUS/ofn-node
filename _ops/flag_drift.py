#!/usr/bin/env python3
"""پروبِ رانشِ فلگ — «مسلح» در برابرِ «بارگذاری‌شده».

مسئله‌ای که این ماژول حل می‌کند
────────────────────────────────
`_ops/OCTOPUS-flags.cmd` سرِ **boot** خوانده می‌شود. هر ویرایشی بعد از آن تا
ری‌استارتِ بعدی **هیچ اثری ندارد** — و تا امروز هیچ سطحی در کلِ سیستم این را
نمی‌گفت. نتیجه‌اش این بود که هر جلسه فلگی را مسلح می‌کرد، فکر می‌کرد کار تمام
است، و رفتارِ زنده دست‌نخورده می‌ماند. این دقیقاً همان بیماریِ §۱ است: ادعایی
(«فلگ روشن شد») که هیچ مشاهده‌ای نمی‌توانست ابطالش کند.

قرارداد
───────
۱. سرِ boot، **هر پروسه** `snapshot_boot("<نام>")` را صدا می‌زند →
   `_ops/state/flags-loaded-<نام>.json` می‌نویسد: کدام فلگ‌ها واقعاً در envِ
   *همان پروسه* بارگذاری شدند، فایلِ فلگ در آن لحظه چه چیزی تعریف می‌کرد، و
   mtimeش چه بود. (وصل‌شده ۲۰۲۶-۰۷-۲۹ به organism/center/cortex/live.)
۲. هر زمان، `probe_all()` فایلِ فلگ را دوباره پارس می‌کند و با snapshotِ **هر
   پروسه جداگانه** دیف می‌گیرد. خروجی: کدام پروسه‌ها کدِ کهنه دارند.
۳. بدونِ snapshot، دروغ نمی‌گوید: `status="no_snapshot"` برمی‌گرداند.

چرا per-process: با یک فایلِ واحد، آخرین پروسه‌ای که بوت می‌شد بقیه را پاک
می‌کرد و پروب وضعیتِ یکی را به نامِ همه گزارش می‌داد — یعنی همان سبزِ دروغی که
این ماژول برای گرفتنش ساخته شده. دامنهٔ ادعا هم به فلگ‌هایی محدود است که
*فایل* مدیریتشان می‌کند؛ متغیرِ envای که هرگز در فایل نبوده (کلیدهای `.env`)
رانش نیست و شمردنش پروب را دائماً قرمز و بی‌اعتبار می‌کرد.

ابطال‌پذیریِ ساختاری: یک فلگ را در فایل عوض کن و ری‌استارت **نکن** →
`count` باید دقیقاً ۱ شود. اگر نشد، این ماژول خراب است، نه سیستم.

قواعدِ سخت که این ماژول رعایت می‌کند
──────────────────────────────────
* فقط‌خواندنی. هیچ‌وقت `OCTOPUS-flags.cmd` را نمی‌نویسد.
* fail-soft. هر استثنا → `status="error"` و `count=0`. هرگز صدازننده را نمی‌کشد.
* **هیچ مقدارِ رازی هرگز چاپ نمی‌شود.** نامی که الگوی راز دارد
  (SECRET/TOKEN/KEY/PASS/PWD/CRED) مقدارش با `REDACTED` جایگزین می‌شود، ولی
  *وجود و تغییرش* همچنان گزارش می‌شود — چون «کلید عوض شد» خودش یک واقعیتِ
  عملیاتیِ لازم است.

اجرا:
    python _ops/flag_drift.py            # خلاصهٔ انسانی
    python _ops/flag_drift.py --json     # خروجیِ ماشین‌خوان
    python _ops/flag_drift.py --snapshot # ثبتِ وضعیتِ بارگذاری‌شدهٔ همین پروسه
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

SCHEMA = "flag-drift.v1"
SNAPSHOT_SCHEMA = "flags-loaded.v1"

REDACTED = "<redacted>"

# پیشوندهایی که این پروب پیگیری می‌کند. عمداً محدود: env کلِ ویندوز صدها کلید
# دارد و ما فقط دربارهٔ فلگ‌های ارگانیسم ادعا می‌کنیم.
TRACKED_PREFIXES = ("OCTOPUS_", "PAID_", "FUGU_", "TELEGRAM_")

_SECRET_TOKENS = ("SECRET", "TOKEN", "KEY", "PASS", "PWD", "CRED", "AUTH")

# ۲۰۲۶-۰۷-۲۹ — شناسه‌های چت/کاربر شبه‌راز اند و باید مثلِ راز رفتار شوند.
# چرا اضافه شد: با سیم‌کشیِ snapshot به boot، `TELEGRAM_OWNER_CHAT_ID` مقدارِ
# واقعی‌اش را رمزنگاری‌نشده در `flags-loaded-*.json` می‌نوشت — هیچ‌کدام از
# توکن‌های بالا نامش را نمی‌گرفتند. الگوها عمداً **دقیق**اند نه «ID» خالی،
# وگرنه `OCTOPUS_WIRE_IDENTITY_EQ` هم بی‌دلیل redact می‌شد.
_ID_TOKENS = ("CHAT_ID", "CHAT_IDS", "OWNER_ID", "OWNER_CHAT", "ALLOWED_IDS")

# `set "X=Y"`  |  `set X=Y`  — هرجای خط (مثلاً بعد از `if not defined X`).
_RE_QUOTED = re.compile(r'(?:^|\s|@)set\s+"([A-Za-z_][A-Za-z0-9_]*)=([^"]*)"')
_RE_BARE = re.compile(r'(?:^|\s|@)set\s+([A-Za-z_][A-Za-z0-9_]*)=([^\r\n]*)')


def is_secret_name(name: str) -> bool:
    """تنها منبعِ حقیقت برای «آیا این نام ممکن است راز باشد؟».

    محافظه‌کارانه: هر شکی = راز. ماژول‌های دیگر باید همین را import کنند تا دو
    تعریفِ متفاوت از «راز» در سیستم وجود نداشته باشد.
    """
    up = str(name or "").upper()
    return any(tok in up for tok in _SECRET_TOKENS + _ID_TOKENS)


def _safe(name: str, value):
    return REDACTED if is_secret_name(name) else value


def _tracked(name: str) -> bool:
    return str(name or "").upper().startswith(TRACKED_PREFIXES)


def parse_flags_file(path):
    """پارسِ یک فایلِ .cmd → (flags, stats).

    * معناشناسیِ cmd: **آخرین تعریف برنده است**.
    * خطوطِ `rem` و `::` نادیده گرفته می‌شوند.
    * `duplicates` شمرده می‌شود چون تعریفِ دوگانه همان کلاسِ باگی است که در
      `.env` با `FUGU_API_KEY` دیده شد: مبهم، و بی‌صدا.
    """
    flags: dict[str, str] = {}
    dupes: dict[str, int] = {}
    lines = 0
    p = Path(path)
    raw = p.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    for line in text.splitlines():
        lines += 1
        s = line.strip()
        if not s:
            continue
        low = s.lower().lstrip("@")
        if low.startswith("rem ") or low.startswith("::") or low.startswith("rem\t"):
            continue
        m = _RE_QUOTED.search(s) or _RE_BARE.search(s)
        if not m:
            continue
        name, value = m.group(1).upper(), m.group(2).strip()
        if name in flags:
            dupes[name] = dupes.get(name, 1) + 1
        flags[name] = value
    stats = {
        "lines": lines,
        "bytes": len(raw),
        "crlf": raw.count(b"\r\n"),
        "lone_lf": raw.count(b"\n") - raw.count(b"\r\n"),
        "defined": len(flags),
        "duplicates": {k: v for k, v in sorted(dupes.items())},
        "mtime": p.stat().st_mtime,
    }
    return flags, stats


def loaded_from_env(env=None) -> dict[str, str]:
    """فلگ‌هایی که واقعاً در env این پروسه بارگذاری شده‌اند."""
    env = os.environ if env is None else env
    return {k.upper(): v for k, v in env.items() if _tracked(k)}


def snapshot(flags_path, out_path, env=None, extra=None) -> dict:
    """وضعیتِ بارگذاری‌شده را ثبت می‌کند. سرِ boot صدا زده شود، یک‌بار."""
    file_flags, stats = parse_flags_file(flags_path)
    env_flags = loaded_from_env(env)
    doc = {
        "schema": SNAPSHOT_SCHEMA,
        "source": str(flags_path),
        "source_mtime": stats["mtime"],
        "pid": os.getpid(),
        "flags": {k: _safe(k, v) for k, v in sorted(env_flags.items())},
        "secret_names": sorted(k for k in env_flags if is_secret_name(k)),
        # ۲۰۲۶-۰۷-۲۹: نامِ فلگ‌هایی که *فایل* در لحظهٔ boot تعریف کرده بود.
        # بدونِ این، probe نمی‌تواند «فلگی که فایل مدیریتش می‌کند» را از
        # «متغیرِ envای که هرگز در فایل نبوده» (مثلاً کلیدهای .env) جدا کند و
        # هر بار چند «removed»ِ کاذب می‌دهد — یعنی پروبِ همیشه‌قرمز.
        "file_flags": sorted(k for k in file_flags if _tracked(k)),
    }
    if extra:
        doc.update(extra)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def probe(flags_path, snapshot_path, boot_mtime=None) -> dict:
    """دیفِ «مسلح» در برابر «بارگذاری‌شده». هرگز استثنا پرتاب نمی‌کند.

    `boot_mtime` اختیاری است: اگر snapshot وجود نداشت ولی زمانِ startِ پروسه را
    می‌دانی، دستِ‌کم جوابِ سطحِ فایل داده می‌شود («فایل بعد از boot عوض شده؟»)،
    که همان هم عملی است.
    """
    try:
        flags, stats = parse_flags_file(flags_path)
    except Exception as exc:  # noqa: BLE001 — پروب هرگز صدازننده را نمی‌کشد
        return {"schema": SCHEMA, "status": "error", "count": 0,
                "error": f"{type(exc).__name__}: {exc}", "drifted": []}

    armed = {k: v for k, v in flags.items() if _tracked(k)}
    snap = None
    try:
        sp = Path(snapshot_path)
        if sp.exists():
            snap = json.loads(sp.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        snap = None

    base = {
        "schema": SCHEMA,
        "file": str(flags_path),
        "file_mtime": stats["mtime"],
        "armed_count": len(armed),
        "hygiene": {"crlf": stats["crlf"], "lone_lf": stats["lone_lf"],
                    "duplicates": stats["duplicates"]},
    }

    if not isinstance(snap, dict) or snap.get("schema") != SNAPSHOT_SCHEMA:
        newer = None
        if boot_mtime is not None:
            try:
                newer = stats["mtime"] > float(boot_mtime)
            except (TypeError, ValueError):
                newer = None
        base.update({
            "status": "no_snapshot",
            "count": 0,
            "drifted": [],
            "file_newer_than_boot": newer,
            "hint": ("هیچ پروسه‌ای هنوز سرِ boot ثبت نکرده. سیم‌کشی از "
                     "۲۰۲۶-۰۷-۲۹ هست ولی اثرش از **بوتِ بعدیِ هر پروسه** "
                     "شروع می‌شود — تا آن لحظه این پروب صادقانه نمی‌داند."),
        })
        return base

    loaded = {k.upper(): v for k, v in (snap.get("flags") or {}).items()}
    # دامنهٔ ادعا: فقط نام‌هایی که *فایلِ فلگ* مدیریتشان می‌کند — الان یا در
    # لحظهٔ boot. متغیرِ envای که هرگز در فایل نبوده (کلیدهای .env مثلِ
    # TELEGRAM_*) رانش نیست؛ شمردنش پروب را دائماً قرمز و بی‌اعتبار می‌کرد.
    # snapshotِ قدیمی (بدونِ file_flags) → رفتارِ سابق، بدونِ تغییر.
    file_at_boot = snap.get("file_flags")
    if isinstance(file_at_boot, list):
        universe = set(armed) | (set(loaded) & {str(n).upper() for n in file_at_boot})
    else:
        universe = set(armed) | set(loaded)
    drifted = []
    for name in sorted(universe):
        a = armed.get(name)
        l = loaded.get(name)
        if name in armed and name not in loaded:
            kind = "added"
        elif name in loaded and name not in armed:
            kind = "removed"
        elif is_secret_name(name):
            # مقدارِ راز در snapshot از قبل REDACTED است، پس مقایسهٔ مقدار
            # بی‌معناست. تنها ادعای صادقانه: نمی‌دانیم. اعلامش می‌کنیم.
            continue
        elif a != l:
            kind = "changed"
        else:
            continue
        drifted.append({"name": name, "kind": kind,
                        "loaded": _safe(name, l), "armed": _safe(name, a)})

    base.update({
        "status": "ok",
        "count": len(drifted),
        "drifted": drifted,
        "snapshot_source_mtime": snap.get("source_mtime"),
        "file_changed_since_snapshot": (
            stats["mtime"] > float(snap.get("source_mtime") or 0)),
        "secrets_not_compared": snap.get("secret_names") or [],
    })
    return base


# ── سطحِ per-process (۲۰۲۶-۰۷-۲۹، رأیِ مالک: «به boot لانچرها وصل کن») ───────
# چرا per-process و نه یک فایلِ واحد: چهار پروسه (organism/center/cortex/live)
# هم‌زمان و در ساعت‌های متفاوت بوت می‌شوند. با یک فایل، آخرین بوت بقیه را پاک
# می‌کرد و probe وضعیتِ *یک* پروسه را به نامِ همه گزارش می‌داد — همان سبزِ دروغی
# که این ماژول برای گرفتنش نوشته شده. نمونهٔ عینیِ همان روز: organism ‏۰۶:۵۲ و
# center ‏۱۶:۳۱ بوت شدند و فایلِ فلگ ۱۶:۳۰ عوض شد؛ فقط یکی‌شان تازه بود.

SNAPSHOT_PREFIX = "flags-loaded-"
SNAPSHOT_GLOB = SNAPSHOT_PREFIX + "*.json"

_RE_PROC_UNSAFE = re.compile(r"[^a-z0-9_-]+")


def proc_slug(proc: str) -> str:
    """نامِ پروسه → slugِ امنِ فایل. نامِ ناسالم هرگز مسیر نمی‌سازد."""
    s = _RE_PROC_UNSAFE.sub("-", str(proc or "").strip().lower()).strip("-")
    return (s or "unknown")[:32]


def snapshot_path_for(proc: str, state_dir=None) -> Path:
    sd = Path(state_dir) if state_dir is not None else _default_paths()[1].parent
    return sd / f"{SNAPSHOT_PREFIX}{proc_slug(proc)}.json"


def snapshot_boot(proc: str, flags_path=None, state_dir=None, env=None):
    """سرِ boot، از داخلِ خودِ پروسه، یک‌بار صدا زده می‌شود.

    fail-soft **مطلق**: هر استثنا بلعیده و `None` برگردانده می‌شود. این تابع در
    مسیرِ بوتِ ارگانیسمِ زنده است و حق ندارد چیزی را بکشد — نبودِ پروب بدتر از
    ارگانیسمِ نبوت‌شده نیست.
    """
    try:
        fp = Path(flags_path) if flags_path is not None else _default_paths()[0]
        out = snapshot_path_for(proc, state_dir)
        return snapshot(fp, out, env=env,
                        extra={"proc": proc_slug(proc), "boot_ts": time.time()})
    except Exception:  # noqa: BLE001 — بوت هرگز به‌خاطرِ پروب نمی‌میرد
        return None


def probe_all(flags_path=None, state_dir=None) -> dict:
    """رانشِ فلگ برای **هر پروسه‌ای که سرِ boot ثبت کرده**. هرگز استثنا نمی‌دهد.

    اگر هیچ snapshotِ per-process نبود، به مسیرِ legacy تک‌فایلی برمی‌گردد تا
    رفتارِ قبلی (و `no_snapshot`ِ صادق) حفظ شود.
    """
    try:
        fp = Path(flags_path) if flags_path is not None else _default_paths()[0]
        sd = Path(state_dir) if state_dir is not None else _default_paths()[1].parent
        snaps = sorted(sd.glob(SNAPSHOT_GLOB)) if sd.is_dir() else []
    except Exception as exc:  # noqa: BLE001
        return {"schema": SCHEMA, "status": "error", "count": 0, "procs": [],
                "error": f"{type(exc).__name__}: {exc}", "drifted": []}

    if not snaps:
        base = probe(fp, (Path(state_dir) if state_dir is not None
                          else _default_paths()[1].parent) / "flags-loaded.json")
        base["procs"] = []
        return base

    procs, total, stale = [], 0, 0
    for sp in snaps:
        r = probe(fp, sp)
        try:
            snap = json.loads(sp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            snap = {}
        r["proc"] = snap.get("proc") or sp.stem[len(SNAPSHOT_PREFIX):]
        r["pid"] = snap.get("pid")
        r["boot_ts"] = snap.get("boot_ts")
        n = int(r.get("count") or 0)
        total += n
        if n:
            stale += 1
        procs.append(r)

    return {
        "schema": SCHEMA,
        "status": "ok",
        "file": str(fp),
        "count": total,
        "procs": procs,
        "proc_count": len(procs),
        "stale_procs": stale,
        "hygiene": (procs[0].get("hygiene") if procs else {}),
        # سازگاری با صدازننده‌هایی که فقط `drifted` را می‌خوانند
        "drifted": [dict(d, proc=p.get("proc")) for p in procs
                    for d in (p.get("drifted") or [])],
    }


# ── bidi (۲۰۲۶-۰۷-۲۹، از مشاهدهٔ کارتِ واقعی در گروه) ────────────────────────
# نسخهٔ اول این خط را می‌ساخت: «center · بوت 0.1h پیش: 0» و تلگرام آن را
# «center · 0.1h بوت پیش: 0» نشان می‌داد — عددِ لاتینِ برهنه داخلِ جملهٔ فارسی
# با الگوریتمِ bidi جابه‌جا می‌شود. دو درمان با هم: رقمِ فارسی (خنثی نیست،
# ذاتاً RTL است) و ایزولهٔ صریح دورِ نامِ لاتینِ پروسه.
_RLM, _LRI, _PDI = "‏", "⁦", "⁩"
_FA_DIGITS = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")


def fa_num(x) -> str:
    """عدد → رقمِ فارسی. جداکنندهٔ اعشار هم فارسی می‌شود."""
    return str(x).translate(_FA_DIGITS)


def ltr(s: str) -> str:
    """نامِ لاتین را ایزوله کن تا متنِ فارسیِ اطرافش را نکشد."""
    return f"{_LRI}{s}{_PDI}"


def _age_fa(boot_ts) -> str:
    """سنِ بوت به فارسی — دقیقه تا یک ساعت، بعد ساعت. «0.1h» برای مالک
    خواندنی نبود و در RTL هم جابه‌جا می‌شد."""
    try:
        sec = max(0.0, time.time() - float(boot_ts))
    except (TypeError, ValueError):
        return ""
    if sec < 3600:
        return f" · بوت {fa_num(int(sec // 60))} دقیقه پیش"
    return f" · بوت {fa_num(round(sec / 3600.0, 1))} ساعت پیش"


def render_all(result: dict) -> str:
    """کارتِ per-process. عددِ اول = چند پروسه کدِ کهنه دارند."""
    if result.get("status") != "ok" or not result.get("procs"):
        return render(result)          # error / no_snapshot / مسیرِ legacy
    procs = result["procs"]
    stale = [p for p in procs if int(p.get("count") or 0)]
    head = (_RLM + (f"✅ رانشِ فلگ: ۰ در هر {fa_num(len(procs))} پروسهٔ ثبت‌شده."
            if not stale else
            f"🚩 {fa_num(len(stale))} از {fa_num(len(procs))} پروسه کدِ کهنه "
            f"دارند (مجموعِ رانش: {fa_num(result.get('count'))})."))
    rows = []
    for p in procs:
        n = int(p.get("count") or 0)
        when = _age_fa(p["boot_ts"]) if p.get("boot_ts") else ""
        mark = "✅" if n == 0 else "🚩"
        names = "، ".join(ltr(d["name"]) for d in (p.get("drifted") or [])[:4])
        tail = f" ← {names}" if names else ""
        # ترتیب عمدی: نام، بعد عددِ رانش، بعد سنِ بوت. عدد چسبیده به «رانش»
        # می‌ماند نه به «پیش» — در نسخهٔ قبل «پیش: 0» خوانده می‌شد.
        rows.append(f"{_RLM}  {mark} {ltr(p.get('proc'))} — "
                    f"رانش {fa_num(n)}{when}{tail}")
    hy = result.get("hygiene") or {}
    warn = ""
    if hy.get("lone_lf"):
        warn += f"\n⚠️ {hy['lone_lf']} خطِ LF تنها در فایلِ .cmd — cmd خراب می‌شود."
    if hy.get("duplicates"):
        warn += f"\n⚠️ تعریفِ تکراری: {', '.join(hy['duplicates'])}"
    fix = ("\nکاری که لازم است: ری‌استارتِ همان پروسه‌ها. تا آن لحظه رفتار عوض نمی‌شود."
           if stale else "")
    return head + "\n" + "\n".join(rows) + fix + warn


# ── سطحِ انسانی ─────────────────────────────────────────────────────────────

def render(result: dict) -> str:
    """خلاصهٔ کوتاه. ADHD-friendly: عدد اول، بعد چرا، بعد چه‌کار."""
    st = result.get("status")
    if st == "error":
        return f"🚩 پروبِ فلگ خطا داد: {result.get('error')} (بی‌اثر — fail-soft)"
    if st == "no_snapshot":
        nb = result.get("file_newer_than_boot")
        tail = ("\nفایلِ فلگ بعد از boot عوض شده → احتمالاً بارگذاری نشده."
                if nb else "")
        hint = result.get("hint")
        return ("🚩 snapshot ندارم، پس نمی‌دانم چه چیزی بارگذاری شده.\n"
                f"مسلح در فایل: {result.get('armed_count')} فلگ." + tail
                + (f"\n{hint}" if hint else ""))
    n = result.get("count", 0)
    hy = result.get("hygiene") or {}
    warn = ""
    if hy.get("lone_lf"):
        warn += f"\n⚠️ {hy['lone_lf']} خطِ LF تنها در فایلِ .cmd — cmd خراب می‌شود."
    if hy.get("duplicates"):
        warn += f"\n⚠️ تعریفِ تکراری: {', '.join(hy['duplicates'])}"
    if n == 0:
        return f"✅ رانشِ فلگ: ۰. مسلح = بارگذاری‌شده ({result.get('armed_count')} فلگ)." + warn
    rows = "\n".join(
        f"  · {d['name']}: بارگذاری‌شده={d['loaded']} → مسلح={d['armed']} ({d['kind']})"
        for d in result["drifted"][:12])
    more = "" if n <= 12 else f"\n  … و {n - 12} تای دیگر"
    return (f"🚩 رانشِ فلگ: {n}. این‌ها در فایل عوض شده‌اند ولی پروسهٔ زنده "
            f"هنوز نسخهٔ قدیمی را دارد:\n{rows}{more}\n"
            f"کاری که لازم است: ری‌استارتِ همان پروسه. تا آن لحظه رفتار عوض نمی‌شود." + warn)


def _default_paths():
    here = Path(__file__).resolve().parent
    return here / "OCTOPUS-flags.cmd", here / "state" / "flags-loaded.json"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    flags_path, snap_path = _default_paths()
    if "--snapshot" in argv:
        # نامِ پروسه اجباری نیست ولی توصیه‌شده: بدونش با نامِ «cli» ثبت می‌شود
        # تا snapshotِ دستی هرگز جای پروسهٔ واقعی جا نزند.
        i = argv.index("--proc") if "--proc" in argv else -1
        proc = argv[i + 1] if 0 <= i < len(argv) - 1 else "cli"
        doc = snapshot_boot(proc)
        if doc is None:
            print("snapshot نوشته نشد (fail-soft)")
            return 1
        out = snapshot_path_for(proc)
        print(f"snapshot نوشته شد: {out} ({len(doc['flags'])} فلگ، proc={doc['proc']})")
        return 0
    res = probe_all()
    if "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render_all(res))
    # exit codeِ معنادار: صفر یعنی «هیچ رانشی نیست»، ۱ یعنی «رانش هست».
    # status ناشناخته هرگز سبز گزارش نمی‌شود (§۱۴: نبودِ خطا برابرِ پاس نیست).
    return 0 if (res.get("status") == "ok" and res.get("count") == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
