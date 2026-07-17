#!/usr/bin/env python3
"""dashboard/server.py — داشبورد زندهٔ اکتوپوس روی 127.0.0.1:8770.

سروری فقط‌خواندنی (به state) + کنترلی (فقط به OCTOPUS-flags.cmd و STOP-ORGANISM).
کاملاً جدا از organism.py — **هیچ import از organism ندارد** (crash 独立性، $0).

دو نکتهٔ ایمنیِ حیاتی:
  ۱) فقط فایل‌های state/ledger را می‌خواند (read-only).
  ۲) تنها writeها: _ops/OCTOPUS-flags.cmd (flag overrides) و _ops/STOP-ORGANISM (kill تمیز).
     هر دو control-file هستند و عین الگوی موجود در organism.py:199 هستند. هیچ ledger-write،
     هیچ spend، هیچ capability-gate باز نمی‌شود.

پورت: 127.0.0.1:8770 (همان که organism.py docstring خالی گذاشته: «8770 داشبورد است»).

برگه‌ها: / (ارگانیسم) · /capabilities (قابلیت‌ها + restart) · /activity (تلمتری/فیتنس/ریپلیکیشن)
         · /channels (کانال‌ها + ledger tail) · /ideas (ایده-گراف)
"""
from __future__ import annotations

import html
import json
import os
import socket
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ── مسیرها (بدون import از opslib/organism — خودکفا) ──────────────────────────────
_OPS = Path(__file__).resolve().parents[1]          # _ops/
_ROOT = _OPS.parent                                  # F:\backup
STATE_DIR = _OPS / "state"
STOP_ORGANISM = _OPS / "STOP-ORGANISM"
RESTART_REQUESTED = _OPS / "RESTART-REQUESTED"         # همراه STOP → bat ری‌استارت می‌کند
ENV_FILE = _OPS / "OCTOPUS-flags.cmd"                 # NON-secret flag overrides (batch-safe .cmd; loaded by RUN-ORGANISM.bat). Secrets belong in F:\backup\.env (env_loader), NEVER here.
FREEZE_FLAG = _OPS / "budget" / "FREEZE.flag"
LEDGER = _ROOT / "07 - Knowledge" / "genome-system" / "ledger" / "ledger.jsonl"
# de-mask بک‌آپ (OBS-02) + توقفِ سراسری/اهرم‌ها (DSH-02) — خودکفا خوانده می‌شوند (این فایل
# عمداً از opslib/organism چیزی import نمی‌کند؛ مسیرها آینهٔ opslib.GITWRITE_FAILED/HALT_ALL‌اند).
GITWRITE_FAILED = _OPS / "backup" / "GITWRITE-FAILED.flag"
HALT_ALL = _OPS / "HALT-ALL"
STOP_ARCHITECT = _ROOT / "04 - Architect System" / "STOP"
PORT = int(os.environ.get("DASHBOARD_PORT", "8770"))

# ── تعریفِ flagها + توضیحِ فارسی ─────────────────────────────────────────────────
# (name, label-fa, risk-level)  risk: safe = امن (paper-full)، risky = فقط دستی
WIRE_FLAGS = [
    ("OCTOPUS_WIRE_DOCTOR", "دکترِ تکاملی — run_cycle روی ضربان", "safe"),
    ("OCTOPUS_WIRE_NEURAL", "پشتهٔ عصبی (rhythm/circadian/sprint)", "safe"),
    ("OCTOPUS_WIRE_UNIFIED", "باس یکپارچه + نخاع (LiveLoop)", "safe"),
    ("OCTOPUS_WIRE_LEAD", "پایِ لید (LeadLeg)", "safe"),
    ("OCTOPUS_WIRE_LEAD_TICK", "تیکِ خودمختارِ LeadLeg (HLC/ack)", "safe"),
    ("OCTOPUS_WIRE_SCHOOL", "پلِ مدرسه (یادگیریِ آوران)", "safe"),
    ("OCTOPUS_WIRE_CONSOLIDATION", "تحکیمِ حافظهٔ کانونی", "safe"),
    ("OCTOPUS_WIRE_EVOLUTION", "تکاملِ RFC (تورنمنت/لیفت)", "safe"),
    ("OCTOPUS_WIRE_BOX", "خوشهٔ box (۱۲ فایل) به دکتر", "safe"),
    ("OCTOPUS_WIRE_IDEAS", "موتورِ ایده-گرافِ vault", "safe"),
    ("OCTOPUS_WIRE_SPECTRAL", "ماینِ طیفیِ مکمل (باسِ شکاف)", "safe"),
    ("OCTOPUS_WIRE_BARBELL", "تخصیصِ باربل (CORE/SATELLITE)", "risky"),
    ("OCTOPUS_WIRE_DEBATE", "حلقهٔ مناظرهٔ LLM در epoch", "risky"),
    ("OCTOPUS_WIRE_SCHEDULER", "دیسپچرِ propose-only (B6)", "safe"),
    ("OCTOPUS_WIRE_RECONCILE", "تطبیقِ روزانهٔ Track-B (A1)", "risky"),
    ("OCTOPUS_WIRE_FITNESS", "فیتنس outbox (A2، measure-only)", "risky"),
    ("OCTOPUS_WIRE_EPISTEMICS", "لایهٔ معرفت‌شناسی (۵ متریک)", "risky"),
    ("OCTOPUS_WIRE_SELFHEAL", "خودترمیمیِ pacemaker (circuit-breaker)", "risky"),
    ("OCTOPUS_WIRE_BIO", "ضربانِ آلوستاتیک (bio_rhythm + budget + baroreflex)", "risky"),
]

CADENCE_FLAGS = [
    ("CHRONO_DOCTOR_EVERY_N_BEATS", "دکتر هر N ضربان", "1440"),
    ("CHRONO_CONSOLIDATION_EVERY_N_BEATS", "تحکیم هر N ضربان", "720"),
    ("CHRONO_AFFERENT_EVERY_N_BEATS", "آوران هر N ضربان", "1440"),
    ("CHRONO_EPISTEMICS_EVERY_N_BEATS", "معرفت‌شناسی هر N ضربان", "720"),
    ("CHRONO_IDEAS_EVERY_N_BEATS", "ایده-گراف هر N ضربان", "1440"),
]

PROFILES = {
    "bare": "همه off — دیباگ/اضطراری (بدون wiring)",
    "paper-full": "تمامِ wiringِ امنِ propose-only (۱۱ flag) — پیش‌فرض",
    "live": "paper-full + effectorهای پول (همچنان capability-gated)",
}

PAPER_FULL_FLAGS = {
    "OCTOPUS_WIRE_DOCTOR", "OCTOPUS_WIRE_NEURAL", "OCTOPUS_WIRE_UNIFIED",
    "OCTOPUS_WIRE_LEAD", "OCTOPUS_WIRE_SCHOOL", "OCTOPUS_WIRE_CONSOLIDATION",
    "OCTOPUS_WIRE_EVOLUTION", "OCTOPUS_WIRE_BOX", "OCTOPUS_WIRE_LEAD_TICK",
    "OCTOPUS_WIRE_IDEAS", "OCTOPUS_WIRE_SPECTRAL",
}

# ── استایل (هم‌خانوادهٔ panel/server.py) ─────────────────────────────────────────
STYLE = """
  :root{
    --bg:#f5f3ee; --card:#fff; --ink:#242320; --muted:#77746c; --line:#eee;
    --green:#1f6d3a; --greenbg:#e2f3e6; --amber:#8a5a10; --amberbg:#faf1de;
    --red:#9b3232; --redbg:#fce8e8; --blue:#2a5599; --bluebg:#e6eefb;
  }
  *{box-sizing:border-box}
  body{margin:0;padding:0;background:var(--bg);font-family:Vazirmatn,Tahoma,Arial,sans-serif;
       color:var(--ink);line-height:1.8}
  .wrap{max-width:880px;margin:0 auto;padding:1.2rem}
  .card{background:var(--card);border-radius:14px;padding:1.6rem 1.8rem;box-shadow:0 1px 3px rgba(0,0,0,.06);
        margin-bottom:1.2rem}
  h1{font-size:22px;font-weight:700;margin:0 0 .4rem}
  h2{font-size:17px;font-weight:600;margin:1.6rem 0 .8rem;color:var(--ink)}
  p.sub{color:var(--muted);margin:0 0 1rem;font-size:13.5px}
  .nav{display:flex;gap:.3rem;flex-wrap:wrap;background:var(--card);border-radius:12px;padding:.5rem;
       margin-bottom:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.05);position:sticky;top:8px;z-index:10}
  .nav a{padding:.5rem .9rem;border-radius:8px;text-decoration:none;color:var(--muted);font-size:13.5px;font-weight:600}
  .nav a:hover{background:var(--bg);color:var(--ink)}
  .nav a.active{background:var(--ink);color:#fff}
  /* کارت‌های شاخص */
  .metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.8rem;margin-bottom:1.2rem}
  .metric{background:var(--card);border-radius:12px;padding:1rem 1.1rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}
  .metric .k{font-size:11.5px;color:var(--muted);font-weight:600}
  .metric .v{font-size:22px;font-weight:700;margin-top:.2rem}
  .metric .v.good{color:var(--green)} .metric .v.bad{color:var(--red)} .metric .v.warn{color:var(--amber)}
  /* بَج‌ها */
  .badge{display:inline-block;padding:.15rem .6rem;border-radius:20px;font-size:12px;font-weight:600}
  .b-green{background:var(--greenbg);color:var(--green)} .b-amber{background:var(--amberbg);color:var(--amber)}
  .b-red{background:var(--redbg);color:var(--red)} .b-blue{background:var(--bluebg);color:var(--blue)}
  .b-gray{background:#eeece5;color:#8a887f}
  /* جدول */
  table{width:100%;border-collapse:collapse;font-size:13.5px;margin:.6rem 0}
  td{padding:.45rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
  td.k{color:var(--muted);width:45%;font-weight:600}
  tr:hover td{background:#fafaf7}
  /* toggle */
  .flag{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;padding:.7rem 0;border-bottom:1px solid var(--line)}
  .flag:last-child{border-bottom:none}
  .flag .ftxt{flex:1}
  .flag .ftitle{font-weight:600;font-size:13.5px}
  .flag .fdesc{font-size:12px;color:var(--muted)}
  .toggle{position:relative;width:42px;height:24px;flex-shrink:0;cursor:pointer}
  .toggle input{opacity:0;width:0;height:0;position:absolute}
  .toggle .slider{position:absolute;inset:0;background:#ccc;border-radius:24px;transition:.2s}
  .toggle .slider:before{content:"";position:absolute;height:18px;width:18px;left:3px;top:3px;background:#fff;border-radius:50%;transition:.2s}
  .toggle input:checked + .slider{background:var(--green)}
  .toggle input:checked + .slider:before{transform:translateX(18px)}
  .toggle.risky input:checked + .slider{background:var(--amber)}
  input[type=number]{width:80px;padding:.3rem .4rem;border:1px solid #ddd9cf;border-radius:6px;font-family:inherit;font-size:13px}
  button{background:var(--ink);color:#fff;border:none;border-radius:8px;padding:.7rem 1.4rem;font-size:14px;
         font-weight:600;cursor:pointer;font-family:inherit;transition:.15s}
  button:hover{background:#403e38}
  button.secondary{background:#fff;color:var(--ink);border:1px solid #ddd9cf}
  button.secondary:hover{background:var(--bg)}
  button.danger{background:var(--red)} button.danger:hover{background:#7a2828}
  .actions{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1rem}
  pre.ledger{direction:ltr;text-align:left;background:#1e1e1e;color:#d4d4d4;padding:1rem;border-radius:8px;
             font-size:11.5px;overflow-x:auto;max-height:340px;font-family:Consolas,monospace;line-height:1.5}
  .note{font-size:12px;color:var(--muted);margin-top:1rem}
  .flash{padding:.7rem 1rem;border-radius:8px;margin-bottom:1rem;font-size:13.5px}
  .flash.ok{background:var(--greenbg);color:var(--green)} .flash.warn{background:var(--amberbg);color:var(--amber)}
  a{color:#4a6fa5}
  .refresh-bar{font-size:11.5px;color:var(--muted);margin-bottom:.8rem}
"""


# ════════════════════════════════════════════════════════════════════════════════
# خواندنِ state (read-only) — هیچ import از organism
# ════════════════════════════════════════════════════════════════════════════════
def _read_json(name: str) -> dict:
    p = STATE_DIR / name
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def _read_jsonl_tail(name: str, n: int = 5) -> list[dict]:
    """آخرین n خطِ یک jsonl زیرِ state (read-only، fail-soft). نبود/خطا → []."""
    p = STATE_DIR / name
    if not p.exists():
        return []
    try:
        lines = [ln for ln in p.read_text("utf-8").splitlines() if ln.strip()][-n:]
    except OSError:
        return []
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


# ORPH-* — پرچمِ default-off برای سطح‌نماییِ سه آرتیفکتِ سایه. خاموش = هیچ کارتی افزوده
# نمی‌شود (خروجیِ صفحه بایت‌همسانِ الان). فقط‌خواندنی مطلق — صفر نوشتن، صفر رفتار.
DEADWRITE_FLAG = "OCTOPUS_WIRE_DEADWRITE_CARDS"


def _deadwrite_on() -> bool:
    ov = _read_env_overrides().get(DEADWRITE_FLAG)
    if ov is not None:
        return ov == "1"
    return os.environ.get(DEADWRITE_FLAG) == "1"


def _deadwrite_card() -> str:
    """کارتِ فقط‌خواندنیِ سه آرتیفکتِ سایه که نوشته می‌شدند ولی خوانده نمی‌شدند
    (calibration-latest · work-health · route-decisions). نبودِ هر فایل → «—/absent».
    صفر نوشتن، صفر رفتار — فقط رصدپذیری. fail-soft."""
    cal = _read_json("cortex/calibration-latest.json")
    wh = _read_json("pulse/work-health.json")
    rd = _read_jsonl_tail("cortex/route-decisions.jsonl", 5)
    if cal:
        cal_row = (f'Brier {html.escape(str(cal.get("brier", "—")))} · '
                   f'AURC {html.escape(str(cal.get("aurc", "—")))} · '
                   f'n={html.escape(str(cal.get("n", "—")))} · '
                   f'abstain&lt;{html.escape(str(cal.get("abstain_below", "—")))}')
    else:
        cal_row = "—/absent"
    if wh:
        wh_row = (f'σ {html.escape(str(wh.get("sigma", "—")))} · '
                  f'ضربان {html.escape(str(wh.get("period_shadow_s", "—")))}s · '
                  f'gate0 {"🟢" if wh.get("gate0") else "🔴"}')
    else:
        wh_row = "—/absent"
    if rd:
        tiers = "/".join(html.escape(str(r.get("tier", "—"))) for r in rd)
        rd_row = f'{len(rd)} تصمیمِ اخیر · {tiers}'
    else:
        rd_row = "—/absent"
    rows = (f'<tr><td class="k">📐 واسنجی (calibration)</td><td>{cal_row}</td></tr>'
            f'<tr><td class="k">🫀 سلامتِ کار (work-health)</td><td>{wh_row}</td></tr>'
            f'<tr><td class="k">🧭 مسیریابی (route-decisions)</td><td>{rd_row}</td></tr>')
    return ('<div class="card"><h2>🩺 آرتیفکت‌های سایه (نوشته‌می‌شد، خوانده‌نمی‌شد)</h2>'
            '<p class="sub">فقط‌خواندنی — این سه فایل سایه‌اند؛ صفر نوشتن، صفر رفتار.</p>'
            f'<table>{rows}</table></div>')


def _gitwrite_failed() -> str | None:
    """دلیلِ شکستِ آخرین git-write اگر GITWRITE-FAILED.flag برافراشته باشد؛ وگرنه None (OBS-02).
    خودکفا و fail-soft — ولی وجودِ فایل هرگز پنهان نمی‌شود (پرچمِ برافراشته = همیشه قرمز)."""
    try:
        if not GITWRITE_FAILED.exists():
            return None
    except OSError:
        return None
    try:
        txt = GITWRITE_FAILED.read_text("utf-8", errors="replace")
    except OSError:
        txt = ""
    txt = txt.lstrip("﻿").strip()
    first = txt.splitlines()[0].strip() if txt else ""
    return first or "GITWRITE-FAILED (بدونِ دلیلِ متنی)"


def _armed_activation_flags() -> list[str]:
    """نامِ ACTIVATION-*.flag ِ برافراشته در _ops (اهرمِ فعال‌سازیِ فقط-مالک) — DSH-02. fail-soft."""
    try:
        return sorted(p.name for p in _OPS.glob("ACTIVATION-*.flag"))
    except OSError:
        return []


def _halt_reason() -> str | None:
    """توقفِ سراسری برای نمایش (خودکفا، fail-soft): HALT-ALL ← STOP(architect). None = هیچ."""
    try:
        if HALT_ALL.exists():
            return "HALT-ALL"
        if STOP_ARCHITECT.exists():
            return "STOP(architect)"
    except OSError:
        return None
    return None


def _read_env_overrides() -> dict[str, str]:
    """flag overrides از OCTOPUS-flags.cmd (اگر هست). خطوطِ `set KEY=VALUE` یا `KEY=VALUE`."""
    out: dict[str, str] = {}
    if not ENV_FILE.exists():
        return out
    try:
        for line in ENV_FILE.read_text("utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("rem ") or line.startswith("#"):
                continue
            if line.lower().startswith("set "):
                line = line[4:]
            if "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def _effective_flags() -> dict[str, bool]:
    """حالتِ مؤثرِ هر flag: env override > profile-default > actual-os.environ."""
    profile = _read_env_overrides().get("OCTOPUS_PROFILE") or os.environ.get("OCTOPUS_PROFILE", "paper-full")
    out: dict[str, bool] = {}
    for name, _, _ in WIRE_FLAGS:
        ov = _read_env_overrides().get(name)
        if ov is not None:
            out[name] = ov == "1"
        elif name in os.environ:
            out[name] = os.environ[name] == "1"
        elif profile in ("paper-full", "live") and name in PAPER_FULL_FLAGS:
            out[name] = True
        else:
            out[name] = False
    return out


def _effective_cadences() -> dict[str, str]:
    ov = _read_env_overrides()
    out: dict[str, str] = {}
    for name, _, default in CADENCE_FLAGS:
        out[name] = ov.get(name) or os.environ.get(name, default)
    return out


def _effective_profile() -> str:
    return _read_env_overrides().get("OCTOPUS_PROFILE") or os.environ.get("OCTOPUS_PROFILE", "paper-full")


def _ledger_tail(n: int = 10) -> list[dict]:
    if not LEDGER.exists():
        return []
    try:
        lines = LEDGER.read_text("utf-8").splitlines()
        tails = [ln for ln in lines[-n:] if ln.strip()]
        out = []
        for ln in tails:
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out
    except OSError:
        return []


def _latest_epoch() -> dict:
    d = _OPS / "budget" / "epochs"
    if not d.exists():
        return {}
    try:
        files = sorted(d.glob("epoch-*.json"), key=lambda p: p.name, reverse=True)
        if not files:
            return {}
        return json.loads(files[0].read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _age_fa(ts_iso: str) -> str:
    if not ts_iso:
        return "—"
    try:
        # فرمت‌های بدون/با timezone
        t = ts_iso.replace("Z", "+00:00")
        dt = time.mktime(time.strptime(t[:19], "%Y-%m-%dT%H:%M:%S"))
    except (ValueError, OverflowError):
        return "؟"
    mins = int((time.time() - dt) / 60)
    if mins < 1:
        return "همین الان"
    if mins < 60:
        return f"{mins} دقیقه پیش"
    if mins < 1440:
        return f"{mins // 60} ساعت پیش"
    return f"{mins // 1440} روز پیش"


def _is_live(st: dict) -> tuple[bool, str]:
    """آیا organism زنده است؟ بر اساسِ کهنگیِ ts."""
    age = _age_fa(str(st.get("ts", "")))
    fresh = ("دقیقه" in age and "روز" not in age) or age == "همین الان"
    return fresh, age


# ════════════════════════════════════════════════════════════════════════════════
# رندرِ صفحات
# ════════════════════════════════════════════════════════════════════════════════
def _shell(body: str, active: str, title: str = "داشبورد اکتوپوس", refresh: int = 0) -> bytes:
    nav_items = [
        ("/", "🫀 ارگانیسم", "org"),
        ("/capabilities", "🔧 قابلیت‌ها", "cap"),
        ("/activity", "📊 فعالیت", "act"),
        ("/channels", "📡 کانال‌ها", "ch"),
        ("/ideas", "🧠 ایده-گراف", "ideas"),
    ]
    nav = "".join(
        f'<a href="{href}" class="{"active" if active == key else ""}">{lbl}</a>'
        for href, lbl, key in nav_items
    )
    refresh_tag = f'<meta http-equiv="refresh" content="{refresh}">' if refresh else ""
    return (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">{refresh_tag}'
        f"<title>{title}</title><style>{STYLE}</style></head>"
        f'<body><div class="wrap"><div class="nav">{nav}</div>{body}</div></body></html>'
    ).encode("utf-8")


def _badge(text: str, kind: str) -> str:
    return f'<span class="badge b-{kind}">{html.escape(text)}</span>'


def _metric(k: str, v, cls: str = "") -> str:
    return f'<div class="metric"><div class="k">{html.escape(k)}</div><div class="v {cls}">{v}</div></div>'


def page_organism() -> bytes:
    st = _read_json("ORGANISM-STATE.json")
    if not st:
        body = (
            "<h1>🫀 ارگانیسم</h1>"
            '<p class="sub">هنوز روشن نشده — هیچ state‌ای در <code>_ops/state/</code> نیست.</p>'
            '<div class="flash warn">برای روشن‌کردن: دابل‌کلیک روی '
            '<code>F:\\backup\\_ops\\RUN-ORGANISM.bat</code></div>'
            '<p class="note">توقف تمیز: ساختن فایل <code>_ops/STOP-ORGANISM</code> و یک تیک صبر (۵ دقیقه).</p>'
        )
        return _shell(body, "org")

    live, age = _is_live(st)
    month = st.get("month") or {}
    today = st.get("today") or {}
    chrono = st.get("chrono") or {}
    wiring = st.get("wiring") or {}

    halted = st.get("halted")
    frozen = st.get("frozen")
    stopped = st.get("stop_organism")
    proto = st.get("protective_mode") or st.get("protective_skip")
    err = st.get("last_error")

    # کارت‌های شاخصِ بالایی
    if stopped:
        status_badge = _badge("🔴 STOP درخواست شده", "red")
    elif halted:
        status_badge = _badge(f"🔴 halted: {html.escape(str(halted))}", "red")
    elif proto:
        status_badge = _badge("🟠 حالت محافظتی", "amber")
    elif live:
        status_badge = _badge("🟢 زنده", "green")
    else:
        status_badge = _badge("🟠 کهنه/غیرپاسخگو", "amber")

    cards = "".join([
        _metric("وضعیت", status_badge),
        _metric("آخرین تیک", age),
        _metric("خرج ماه", f"AU${month.get('aud', 0):.2f}" if isinstance(month.get('aud'), (int, float)) else "—",
                "good" if not month.get('aud') else ""),
        _metric("خرج امروز", f"US${today.get('usd', 0):.4f}" if isinstance(today.get('usd'), (int, float)) else "—"),
        _metric("σ تکثیر", st.get("sigma", "—")),
        _metric("germline lag", f"{st.get('germline_lag_h', '—')}h",
                "warn" if isinstance(st.get('germline_lag_h'), (int, float)) and st.get('germline_lag_h', 0) > 4 else "good"),
    ])
    # سلامتِ بک‌آپ (OBS-02): پرچمِ صریحِ شکستِ git-write غالب است — mtimeِ germline بالا
    # سبزِ کاذب می‌سازد، این کارت آن را قرمز می‌کند. فقط‌خواندنی، خودکفا.
    _gw_fail = _gitwrite_failed()
    if _gw_fail:
        cards += _metric("بک‌آپ (git-write)", _badge("🔴 شکست‌خورده", "red"), "bad")
    else:
        cards += _metric("بک‌آپ (git-write)", _badge("🟢 سالم", "green"), "good")
    # کارتِ ضربانِ آلوستاتیک (اگر OCTOPUS_WIRE_BIO فعّال باشد)
    cardio = st.get("cardiac") or {}
    if cardio.get("enabled"):
        bio = cardio.get("bio_rhythm") or {}
        bud = cardio.get("budget") or {}
        pace = bio.get("pace", "—")
        pace_cls = {"mice": "warn", "whale": "good", "balanced": ""}.get(pace, "")
        period = bio.get("period_s")
        period_str = f"{period:.0f}ث" if isinstance(period, (int, float)) else "—"
        cards += _metric("ضربان (bio)", f"{pace} · {period_str}", pace_cls)
        if bud.get("daily_cap"):
            rem = bud.get("remaining", 0)
            cap = bud.get("daily_cap", 0)
            cards += _metric("بودجهٔ ضربان", f"{rem}/{cap}", "bad" if bud.get("depleted") else "")

    # جدولِ کامل
    rows = [
        ("شروع", str(st.get("started", "—"))[:19].replace("T", " ")),
        ("مد epoch", str(st.get("epoch_mode", "—"))),
        ("نبض chrono (beat)", str(chrono.get("beat_seq", chrono.get("beat", "—"))) if chrono else "—"),
        ("pacemaker", _badge("روشن", "green") if chrono.get("running") else _badge("خاموش", "gray")),
        ("فشار epoch", str((st.get("pressure") or {}).get("pressure", "—"))),
        ("epoch بعدی (دقیقه)", str(st.get("next_epoch_minutes", "—"))),
        ("متر مشکوک صفر", str(st.get("suspect_zero_total", "—"))),
        ("تعارض تلمتری", str(len(st.get("conflicts") or []))),
        ("halted", str(halted or "—")),
        ("frozen", "✅ بله" if frozen else "نه"),
        ("STOP درخواست", "✅ بله" if stopped else "نه"),
        ("حالت محافظتی", "✅ فعّال" if proto else "نه"),
    ]
    if err:
        rows.append(("آخرین خطا", html.escape(str(err)[:300])))
    table = "".join(f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in rows)

    # wiring summary
    if wiring:
        witems = "".join(
            f'<span class="badge {"b-green" if v else "b-gray"}">{html.escape(k).replace("wire_", "")}</span>'
            for k, v in sorted(wiring.items())
        )
        wbox = f'<h2>Wiring فعّال</h2><div style="display:flex;gap:.3rem;flex-wrap:wrap">{witems}</div>'
    else:
        wbox = '<p class="sub">هیچ wiring‌ای فعّال نیست (profile = bare).</p>'

    # توقفِ سراسری + اهرم‌های فعال‌سازی (DSH-02) + شکستِ بک‌آپ (OBS-02) — کارتِ صریح
    halt_r = _halt_reason()
    armed = _armed_activation_flags()
    halt_flash = ""
    if halt_r:
        halt_flash += f'<div class="flash warn">🛑 توقفِ سراسری فعّال است: <b>{html.escape(halt_r)}</b></div>'
    if _gw_fail:
        halt_flash += (f'<div class="flash warn">💾 بک‌آپ شکست خورده — git-write ناموفق '
                       f'(<code>_ops/backup/GITWRITE-FAILED.flag</code>): {html.escape(_gw_fail)[:160]}</div>')
    if armed:
        arm_badges = "".join(_badge(f"⚡ {a}", "blue") for a in armed)
        arm_box = (f'<div class="card"><h2>اهرم‌های فعال‌سازی برافراشته (فقط-مالک)</h2>'
                   f'<div style="display:flex;gap:.3rem;flex-wrap:wrap">{arm_badges}</div>'
                   f'<p class="note">وجودِ هر فایلِ <code>ACTIVATION-*.flag</code> = verdictِ صریحِ تو.</p></div>')
    else:
        arm_box = ('<div class="card"><h2>اهرم‌های فعال‌سازی</h2>'
                   '<p class="sub">هیچ <code>ACTIVATION-*.flag</code> برافراشته نیست — همه‌چیز propose-only.</p></div>')

    body = (
        '<div class="refresh-bar">🔄 auto-refresh هر ۱۰ ثانیه</div>'
        "<h1>🫀 ارگانیسم — وضعیت زنده</h1>"
        '<p class="sub">همه‌چیز سایه و $۰. بودجهٔ زنده پشتِ گیتِ دوقفلهٔ خودت.</p>'
        + halt_flash +
        f'<div class="metrics">{cards}</div>'
        f'<div class="card"><h2>جزئیات</h2><table>{table}</table></div>'
        + arm_box +
        f'<div class="card">{wbox}</div>'
        '<p class="note">دستگاهِ کنترل: <a href="/capabilities">قابلیت‌ها</a> · '
        '<a href="/activity">فعالیت</a></p>'
    )
    return _shell(body, "org", refresh=10)


def page_capabilities(flash: str = "", flash_kind: str = "ok") -> bytes:
    eff = _effective_flags()
    cad = _effective_cadences()
    profile = _effective_profile()
    overrides = _read_env_overrides()

    # profile selector
    prof_opts = "".join(
        f'<label class="opt" style="display:block;margin:.4rem 0;padding:.6rem;border:1px solid #ddd9cf;'
        f'border-radius:8px;cursor:pointer">'
        f'<input type="radio" name="OCTOPUS_PROFILE" value="{p}" {"checked" if profile == p else ""} '
        f'style="margin-left:.5rem"> <b>{p}</b>'
        f' — <span style="color:var(--muted);font-size:12.5px">{desc}</span></label>'
        for p, desc in PROFILES.items()
    )

    # flag toggles
    flags_html = []
    for name, label, risk in WIRE_FLAGS:
        on = eff.get(name, False)
        risk_badge = _badge("ریسکی", "amber") if risk == "risky" else _badge("امن", "green")
        overridden = name in overrides
        ov_mark = ' <span class="badge b-blue" title="از OCTOPUS-flags.cmd override شده">override</span>' if overridden else ""
        flags_html.append(
            f'<div class="flag {"risky" if risk == "risky" else ""}">'
            f'<div class="ftxt"><div class="ftitle">{html.escape(name)} {ov_mark}</div>'
            f'<div class="fdesc">{html.escape(label)} · {risk_badge}</div></div>'
            f'<label class="toggle"><input type="checkbox" name="{name}" value="1" {"checked" if on else ""}>'
            f'<span class="slider"></span></label></div>'
        )

    # cadence
    cad_html = []
    for name, label, default in CADENCE_FLAGS:
        val = cad.get(name, default)
        cad_html.append(
            f'<div class="flag"><div class="ftxt"><div class="ftitle">{html.escape(name)}</div>'
            f'<div class="fdesc">{html.escape(label)}</div></div>'
            f'<input type="number" name="{name}" value="{html.escape(str(val))}" min="1"></div>'
        )

    flash_html = f'<div class="flash {flash_kind}">{flash}</div>' if flash else ""

    body = (
        "<h1>🔧 قابلیت‌ها</h1>"
        '<p class="sub">flagها در زمانِ بوت خوانده می‌شوند. تغییرها بعد از ری‌استارت اعمال می‌شوند.</p>'
        + flash_html +
        '<div class="card"><h2>پروفایل</h2>'
        f'<div>{prof_opts}</div></div>'
        '<div class="card"><h2>flagهای wiring (۱۹)</h2>'
        f'<div>{"".join(flags_html)}</div></div>'
        '<div class="card"><h2>ضربان (cadence)</h2>'
        f'<div>{"".join(cad_html)}</div></div>'
        '<div class="card"><h2>وضعیتِ فعلی</h2>'
        f'<p class="sub">پروفایلِ مؤثر: <b>{html.escape(profile)}</b> · '
        f'{sum(eff.values())} flag روشن از {len(eff)} · '
        f'{"OCTOPUS-flags.cmd موجود" if overrides else "بدون OCTOPUS-flags.cmd (پیش‌فرض‌ها)"}</p>'
        '<form method="post" action="/save"><div class="actions">'
        '<button type="submit" name="action" value="save">💾 ذخیرهٔ موقت</button>'
        '<button type="submit" name="action" value="restart" class="danger">💾 ذخیره + ری‌استارت ارگانیسم</button>'
        '</div></form>'
        '<p class="note">ذخیره → <code>_ops/OCTOPUS-flags.cmd</code> · '
        'ری‌استارت → STOP-ORGANISM (تمیز) + شروع مجدد با env جدید</p>'
        '</div>'
    )
    return _shell(body, "cap")


def page_activity() -> bytes:
    tele = _read_json("telemetry-latest.json")
    fit = _read_json("fitness-latest.json")
    rep = _read_json("replication-latest.json")
    ep = _latest_epoch()

    # telemetry
    g = tele.get("genome") or {}
    b = tele.get("brain") or {}
    per_organ = tele.get("per_organ_alltime_musd") or {}
    tele_rows = [
        ("رویداد genome", str(g.get("events", "—"))),
        ("هزینه genome (μ$)", str(g.get("cost_musd", "—"))),
        ("ردیف brain", str(b.get("rows", "—"))),
        ("هزینه brain (μ$)", str(b.get("cost_musd", "—"))),
        ("نرخ تبدیل AUD/USD", str((tele.get("fx_aud_per_usd") or {}).get("rate", "—"))),
        ("متر مشکوک صفر", str(tele.get("suspect_zero_total", "—"))),
    ]
    tele_t = "".join(f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in tele_rows)

    organ_rows = ""
    if per_organ:
        organ_rows = "<h2>هزینهٔ همه‌جانب (μ$)</h2><table>"
        for k, v in per_organ.items():
            organ_rows += f'<tr><td class="k">{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>'
        organ_rows += "</table>"

    # fitness
    auth = fit.get("authoritative")
    auth_badge = _badge("✅ معتبر", "green") if auth else _badge("🔒 سایه (تا ۲۸ روز)", "amber")
    attr = fit.get("attribution") or {}
    weights = fit.get("weights") or {}
    fit_rows = [
        ("وضعیت", auth_badge),
        ("تجربه (روز)", str(fit.get("experience_span_days", "—"))),
        ("CLAIMED", str(attr.get("claimed", "—"))),
        ("CONFIRMED", str(attr.get("confirmed", "—"))),
        ("alerts", str(len(fit.get("integrity_alerts") or []))),
    ]
    fit_t = "".join(f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in fit_rows)
    w_items = "".join(f'<span class="badge b-blue">{html.escape(k)}={v}</span>' for k, v in weights.items())

    # replication
    sig = rep.get("sigma") or {}
    lg = rep.get("live_gate") or {}
    sig_badge = _badge(f"σ={sig.get('sigma_effective', '—')} · {sig.get('zone', '—')}", "blue")
    rep_rows = [
        ("σ", sig_badge),
        ("spawn پیشنهاد", str(sig.get("spawn_proposed", "—"))),
        ("spawn تأیید", str(sig.get("spawn_approved", "—"))),
        ("max cells", str((rep.get("config") or {}).get("max_cells", "—"))),
        ("live_gate", _badge("✅ باز", "green") if lg.get("open") else _badge("🔒 قفل", "amber")),
        ("دلیلِ قفل", html.escape(str(lg.get("why", "—")))),
    ]
    rep_t = "".join(f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in rep_rows)

    # epoch
    ep_rows = ""
    if ep:
        pressure = ep.get("pressure") or {}
        alloc = ep.get("allocation_dry") or {}
        grants = alloc.get("grants") or []
        ep_rows = (
            f'<table><tr><td class="k">فشار</td><td>{pressure.get("pressure", "—")}</td></tr>'
            f'<tr><td class="k">epoch بعدی (دقیقه)</td><td>{ep.get("next_epoch_minutes", "—")}</td></tr>'
            f'<tr><td class="k">خرج ماه AU$</td><td>{alloc.get("spent_month_aud", "—")}</td></tr>'
            f'<tr><td class="k">سقف ماه AU$</td><td>{alloc.get("cap_monthly_aud", "—")}</td></tr></table>'
        )
        if grants:
            ep_rows += '<h2>تخصیصِ dry-run به ارگان‌ها</h2><table>'
            # grants می‌تواند dict {organ: details} یا list باشد
            items = grants.items() if isinstance(grants, dict) else enumerate(grants)
            for organ, gr in items:
                if not isinstance(gr, dict):
                    continue
                organ_name = organ if isinstance(organ, str) else gr.get("organ", "?")
                verdict = gr.get("verdict", "—")
                total = gr.get("total_month_aud", "—")
                tag = gr.get("tag", "")
                vb = "green" if "GRANT" in str(verdict).upper() or "GREEN" in str(verdict).upper() else (
                    "amber" if "AMBER" in str(verdict).upper() else "gray")
                ep_rows += (f'<tr><td class="k">{html.escape(str(organ_name))}</td><td>'
                            f'<span class="badge b-{vb}">{html.escape(str(verdict))}</span> '
                            f'AU${total} <span class="note">{html.escape(str(tag))[:60]}</span></td></tr>')
            ep_rows += "</table>"

    # ORPH-* — کارتِ آرتیفکت‌های سایه (فقط پشتِ پرچمِ default-off؛ خاموش = "" = بایت‌همسان)
    dw_card = _deadwrite_card() if _deadwrite_on() else ""

    body = (
        "<h1>📊 فعالیت</h1>"
        '<p class="sub">تلمتری، فیتنس، ریپلیکیشن و آخرین epoch — همه سایه/propose-only.</p>'
        f'<div class="card"><h2>تلمتری</h2><table>{tele_t}</table>{organ_rows}</div>'
        f'<div class="card"><h2>فیتنس</h2><table>{fit_t}</table>'
        f'<div style="margin-top:.6rem;display:flex;gap:.3rem;flex-wrap:wrap">{w_items}</div></div>'
        f'<div class="card"><h2>ریپلیکیشن (σ)</h2><table>{rep_t}</table></div>'
        f'<div class="card"><h2>آخرین epoch</h2>{ep_rows or "<p class=\"sub\">داده‌ای نیست</p>"}</div>'
        + dw_card
    )
    return _shell(body, "act")


def page_channels() -> bytes:
    ch = _read_json("channel-status.json")
    # P1 راست‌گویی (2026-07-15): channel-status.json نویسندهٔ زنده ندارد (snapshot ِ فریز
    # 2026-07-08). قانونِ کابین: دادهٔ کهنه/بی‌نویسنده هرگز «🟢 زنده» رندر نمی‌شود.
    import time as _time
    _stale, _snap_ts = True, "?"
    try:
        _mt = (STATE_DIR / "channel-status.json").stat().st_mtime
        _snap_ts = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(_mt))
        _stale = (_time.time() - _mt) > 3600
    except OSError:
        pass
    channels = ch.get("channels") or {}
    ch_rows = ""
    if _stale:
        ch_rows += (f'<tr><td class="k">⚠️</td><td>snapshot ِ کهنه — آخرین نوشتن {_snap_ts}؛ '
                    f'این فایل نویسندهٔ زنده ندارد؛ وضعیت‌های زیر «زنده» نیستند، عکسِ قدیمی‌اند.</td></tr>')
    for name, info in channels.items():
        live = info.get("live")
        mode = info.get("mode", "—")
        extra = ""
        req = info.get("required_env") or []
        if req and not live:
            extra = f'<br><span class="note">نیاز: {html.escape(", ".join(req))}</span>'
        if _stale:
            badge = f'⚪ {"زنده" if live else "خاموش"} <span class="note">(در snapshot ِ {_snap_ts})</span>'
        else:
            b = "green" if live else "red"
            badge = f'<span class="badge b-{b}">{"🟢 زنده" if live else "🔴 خاموش"}</span>'
        ch_rows += (f'<tr><td class="k">{html.escape(name)}</td><td>'
                    f'{badge} · {html.escape(str(mode))}{extra}</td></tr>')

    # ledger tail
    tails = _ledger_tail(10)
    if tails:
        ledger_lines = []
        for row in tails:
            t = row.get("type", "?")
            ts = str(row.get("ts", ""))[:19]
            sub = (row.get("payload") or {}).get("subtype", "")
            actor = row.get("actor", "")
            ledger_lines.append(f'<span style="color:#6a9955">{ts}</span> '
                                f'<span style="color:#c586c0">{t}</span> '
                                f'<span style="color:#9cdcfe">{html.escape(str(sub))}</span> '
                                f'<span style="color:#808080">← {html.escape(actor)}</span>')
        ledger_html = '<pre class="ledger">' + "<br>".join(ledger_lines) + "</pre>"
    else:
        ledger_html = '<p class="sub">ledger خالی یا پیدا نشد.</p>'

    body = (
        "<h1>📡 کانال‌ها + دفتر</h1>"
        '<div class="card"><h2>وضعیتِ کانال‌ها</h2>'
        f'<table>{ch_rows}</table></div>'
        '<div class="card"><h2>آخرین نبضِ ledger (۱۰ ردیف)</h2>'
        f'{ledger_html}'
        '<p class="note">این ردیف‌ها قراردادِ append-only LANGAR هستند — '
        'شواهدِ واقعیِ اینکه حلقه می‌زند.</p></div>'
        '<div class="card"><h2>صفِ تأیید (RFC/Telegram)</h2>'
        '<p class="sub">صف‌های تأیید در RAM-only هستند. برای دیدنِ کارت‌های تأیید باید '
        'Telegram را فعال کنی (توکن لازم). بدونِ کانال، Doctor RFCها را '
        'به‌صورت <code>submitted-no-channel</code> نگه می‌دارد (بی‌خطر).</p>'
        '<p class="note">راه‌اندازی: خطِ <code>TELEGRAM_BOT_TOKEN=...</code> را در <code>F:\\backup\\.env</code> بگذار '
        '(نه در فایلِ flags — آنجا secret git-ignored و توسط env_loader در بوت لود می‌شود) + ری‌استارت.</p>'
        '</div>'
    )
    return _shell(body, "ch")


def page_ideas() -> bytes:
    eff = _effective_flags()
    on = eff.get("OCTOPUS_WIRE_IDEAS", False)
    # idea_beat ممکن است یک state بنویسد؛ اگر نبود، فقط وضعیت را نشان بده
    idea_state = _read_json("idea-graph-latest.json")
    if idea_state:
        nodes = idea_state.get("nodes_count", "—")
        edges = idea_state.get("edges_count", "—")
        hubs = idea_state.get("hubs") or []
        hubs_html = "".join(
            f'<li>{html.escape(str(h.get("title", h)))}</li>' for h in (hubs[:5] if isinstance(hubs, list) else [])
        ) or "<li>—</li>"
        body = (
            "<h1>🧠 ایده-گراف</h1>"
            f'<p class="sub">موتورِ ایده-گراف {"🟢 فعّال" if on else "🔴 خاموش"} (OCTOPUS_WIRE_IDEAS).</p>'
            f'<div class="metrics">{_metric("نوت‌ها", nodes)}{_metric("یال‌ها", edges)}</div>'
            f'<div class="card"><h2>هاب‌ها (مرکزی‌ترین ایده‌ها)</h2><ul>{hubs_html}</ul></div>'
        )
    else:
        body = (
            "<h1>🧠 ایده-گراف</h1>"
            f'<div class="flash {"ok" if on else "warn"}">موتورِ ایده-گراف '
            f'{"🟢 فعّال است" if on else "🔴 خاموش است"} (OCTOPUS_WIRE_IDEAS).</div>'
            '<div class="card"><h2>ایده-گراف چیکار می‌کند؟</h2>'
            '<p class="sub">تمامِ فایل‌های markdown پروژه‌ها/دانش/inbox (حدود ۵۶۶ نوت) را '
            'می‌خواند، frontmatter و wikilinkها را پارس می‌کند، و گرافِ ارتباطِ ایده‌ها را '
            'می‌سازد: هاب‌ها، خوشه‌ها، پل‌ها، و یال‌های پیشنهادی.</p>'
            '<p class="sub">propose-only مطلق — هیچ effector. فقط تحلیل و پیشنهاد.</p>'
            + ('<p class="note">هنوز تحلیلی ننوشته — ممکن است بیتِ بعدی (cadence) فعال نشده باشد.</p>' if on else
               '<p class="note">برای فعال‌کردن: <a href="/capabilities">قابلیت‌ها</a> → OCTOPUS_WIRE_IDEAS → ذخیره + ری‌استارت.</p>')
            + '</div>'
        )
    return _shell(body, "ideas")


# ════════════════════════════════════════════════════════════════════════════════
# نوشتنِ env + restart (تنهایی writeهای مجاز)
# ════════════════════════════════════════════════════════════════════════════════
_WRITE_LOCK = threading.Lock()


def _write_env(form: dict[str, str]) -> str:
    """نوشتنِ _ops/OCTOPUS-flags.cmd به‌صورتِ atomic. برمی‌گرداند: خلاصه."""
    lines = ["rem OCTOPUS-flags.cmd — تولید‌شده توسط dashboard. در زمانِ بوت توسط RUN-ORGANISM.bat لود می‌شود."]
    profile = form.get("OCTOPUS_PROFILE", "paper-full")
    if profile not in PROFILES:  # F-1: allowlist ضدِ تزریقِ CRLF به فایلِ اجرایی (RCE در بوت)
        profile = "paper-full"
    lines.append(f"set OCTOPUS_PROFILE={profile}")
    for name, _, _ in WIRE_FLAGS:
        val = "1" if form.get(name) == "1" else "0"
        lines.append(f"set {name}={val}")
    for name, _, default in CADENCE_FLAGS:
        val = form.get(name) or default
        try:
            int(val)  # اعتبارسنجی
        except ValueError:
            val = default
        lines.append(f"set {name}={val}")
    # F-3: کلیدهای unmanaged (گاردهای ضدجعلِ human-append، مسیریابیِ مغز، اولاما، ...) را
    # از فایلِ موجود seed کن تا این بازسازیِ atomic آن‌ها را بی‌صدا پاک نکند (OWASP-A05).
    _managed = {"OCTOPUS_PROFILE"} | {n for n, _, _ in WIRE_FLAGS} | {n for n, _, _ in CADENCE_FLAGS}
    for _k, _v in _read_env_overrides().items():
        if _k not in _managed and _v is not None:
            lines.append(f"set {_k}={_v}")
    content = "\r\n".join(lines) + "\r\n"
    tmp = ENV_FILE.with_name(ENV_FILE.name + ".tmp")
    with _WRITE_LOCK:
        tmp.write_text(content, "utf-8")
        os.replace(tmp, ENV_FILE)   # atomic
    on_count = sum(1 for n, _, _ in WIRE_FLAGS if form.get(n) == "1")
    return f"ذخیره شد: پروفایل={profile} · {on_count} flag روشن · فایل: _ops/OCTOPUS-flags.cmd"


def _do_restart() -> str:
    """ساختِ STOP-ORGANISM + RESTART-REQUESTED → organism تیکِ بعد تمیز خارج می‌شود،
    bat می‌بیند که RESTART درخواست شده، هر دو را پاک می‌کند و با env جدید دوباره بوت می‌کند."""
    try:
        STOP_ORGANISM.write_text("dashboard-restart\n", "utf-8")
        RESTART_REQUESTED.write_text("dashboard\n", "utf-8")
        return ("STOP-ORGANISM + RESTART-REQUESTED ساخته شد. organism تیکِ بعد "
                "(حداکثر ۵ دقیقه) تمیز خارج می‌شود، سپس RUN-ORGANISM.bat هر دو را پاک "
                "کرده و با env جدید ری‌استارت می‌کند.")
    except OSError as e:
        return f"خطا در ساختِ فایل‌های restart: {e}"


# ════════════════════════════════════════════════════════════════════════════════
# HTTP handler
# ════════════════════════════════════════════════════════════════════════════════
class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/" or path == "/organism":
            self._send(page_organism())
        elif path == "/capabilities":
            self._send(page_capabilities())
        elif path == "/activity":
            self._send(page_activity())
        elif path == "/channels":
            self._send(page_channels())
        elif path == "/ideas":
            self._send(page_ideas())
        elif path == "/api/state":
            self._json(_read_json("ORGANISM-STATE.json"))
        elif path == "/api/flags":
            self._json({"profile": _effective_profile(), "flags": _effective_flags(),
                        "cadences": _effective_cadences(), "env_overrides": _read_env_overrides()})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):  # noqa: N802
        import sys as _s, os as _o
        _p = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
        if _p not in _s.path:
            _s.path.insert(0, _p)
        try:
            import httpauth as _ha  # RC1: گاردِ CSRF/Origin پشتِ OCTOPUS_HTTP_AUTH
            if not _ha.guard_post(self):
                return
        except Exception:  # noqa: BLE001 — گارد اختیاری؛ فلگ‌خاموش/خطا = رفتارِ امروز
            pass
        path = self.path.split("?", 1)[0]
        if path not in ("/save",):
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        from urllib.parse import parse_qs
        form_flat = parse_qs(raw, keep_blank_values=True)
        form = {k: v[0] if v else "" for k, v in form_flat.items()}
        action = form.get("action", "save")
        msg = _write_env(form)
        kind = "ok"
        if action == "restart":
            msg += "<br><br>" + _do_restart()
            kind = "warn"
        # redirect GET /capabilities (PRG pattern — refresh-safety)
        self.send_response(303)
        self.send_header("Location", f"/capabilities?saved=1&action={action}")
        self.end_headers()

    def _send(self, body: bytes, ct: str = "text/html; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj: dict):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):   # ساکت
        pass


def main() -> int:
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"dashboard: زنده روی {url}")
    if os.environ.get("DASHBOARD_AUTOOPEN"):
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("dashboard: خروج.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
