#!/usr/bin/env python3
"""render.py — لایهٔ نمایشِ «مرکزِ تلگرام» (telegram_center): متن/کیبورد، خالص و بدونِ شبکه.

نقش: تنها جایی که feedهای کنترل-پلین به متنِ HTMLِ تلگرام و کیبوردِ inline تبدیل
می‌شوند. هیچ ارسالی اینجا نیست — tg_api می‌فرستد، center تصمیم می‌گیرد؛ این ماژول
فقط «چه چیزی دیده شود» را می‌سازد (ADHD-first: کوتاه، emoji-اول، هر تصمیم یک‌تاپ).

قواعد (قانونِ لایه):
  • خالص: هیچ شبکه‌ای، هیچ نوشتنی روی دیسک، هیچ اثرِ import-time.
  • fail-soft: هر ورودیِ خراب/غایب → خروجیِ امن (رشتهٔ کوتاه/{})، هرگز crashِ صداکننده.
  • collect_feeds تنها نقطهٔ I/O است — فقط «خواندنِ» تنبل و fail-soft از aggregatorهای
    موجود (execution_board/guidance_box/business_brain) + دو state-file (قلب/registry)،
    با الگویِ sys.path ِ live/server.py. هر feed مستقل try می‌شود؛ شکست = {} همان کلید.
  • containment: کلیدهای پا (leg) content-free اند؛ نامِ نمایشی از config ِ مالک در
    runtime می‌آید. هر رشتهٔ حاویِ echo ِ ممنوع (پاریته با execution_board._scrub /
    registry_scan.scrub) پیش از خروج redact می‌شود — هرگز نشتِ جزئی.
  • status ≤ ۵ خطِ کوتاه؛ دایجستِ هر پا ≤ ۳ خط؛ کیبوردِ تصمیم = ok/no/later:<id>.

$0 · stdlib-only · Persian-ok. مصرف‌کننده: _ops/telegram_center/center.py.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent          # _ops

# containment (پاریته با execution_board / guidance_box / registry_scan) —
# تنها جای مجاز برای این رشته‌ها در کد؛ هرگز جای دیگری echo نمی‌شوند.
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")
_REDACTED = "(redacted:containment)"

# ۸ پای ارگانیسم — کلیدها content-free و پایدار (کد/لاگ/state فقط با همین کلیدها).
# مقدارها = نامِ نمایشیِ پیش‌فرض؛ مالک در runtime از config (display_names) عوض می‌کند.
LEGS = {
    "lead":       "Lead-نقاشی",
    "ziman":      "Ziman Galerry",
    "mining":     "Mining",
    "crypto":     "Crypto-etoro",
    "accounting": "Accounting",
    "studio_pf":  "استودیو",
    "system":     "سیستم",
    "knowledge":  "دانش",
    "cartographer": "نقشه‌بردار",
    # ۲۰۲۶-۰۷-۲۷ — اتاقِ آینه: تنها جایی که هر پیام مستقیم به لایهٔ خودشناسی می‌رود
    # (بدونِ نگاشتِ فرمان). پا نیست — دایجستِ دوره‌ای ندارد؛ فقط گفتگو.
    "mirror": "آینه",
}

# ورودی‌هایی از LEGS که **اتاق‌اند نه پا**: نام و آیکنِ تاپیک دارند، ولی وضعیت،
# دایجست و چرخهٔ سلامت ندارند. بدونِ این مجموعه، «اتاق» فقط در ذهنِ نویسنده وجود
# داشت و هر مصرف‌کننده‌ای باید خودش حدس می‌زد — و یک تست هم دقیقاً سرِ همین حدس
# شکست. حالا مفهوم صریح است و یک‌جا تعریف شده.
ROOMS = frozenset({"mirror"})

# برندینگِ بصریِ هر پا (رأی مالک: media-first، آیکنِ ثابت per پا) — جدا از LEGS تا
# قراردادِ نام‌ها (تست/`display_name`) دست‌نخورده بماند. HQ برای تاپیک/هدرِ فرماندهی.
LEG_ICONS = {
    "lead": "🎨", "ziman": "🖼", "mining": "⛏", "crypto": "📈",
    "accounting": "🧾", "studio_pf": "🎬", "system": "⚙️", "knowledge": "🧠",
    "cartographer": "🗺",
    "mirror": "🪞",
    "hq": "🐙",
}
DIVIDER = "─────── ✦ ───────"


def topic_icon(leg_key: str, config: dict | None = None) -> str:
    """آیکنِ تاپیک — `topic_icons` در configِ مالک برنده است، مثل `display_names`.

    چرا override لازم شد: نامِ استعاری بدونِ آیکنِ هم‌خانواده گیج‌کننده است
    («⚙️ قلب»). نامِ کد شناسهٔ پروژه است و عوض نمی‌شود (`Lead-نقاشی` مسیرِ فایل و
    کلیدِ صفِ تأیید هم هست)، پس کلِ لایهٔ استعاره در config می‌نشیند و کد فقط
    fallbackِ content-free می‌ماند. fail-soft: هر خطا → آیکنِ پیش‌فرض."""
    k = str(leg_key or "")
    try:
        over = (config or {}).get("topic_icons") or {}
        if isinstance(over, dict) and isinstance(over.get(k), str) and over[k].strip():
            return over[k].strip()
    except (AttributeError, TypeError):
        pass
    return LEG_ICONS.get(k, "")


def topic_title(leg_key: str, config: dict | None = None) -> str:
    """عنوانِ تاپیکِ یک پا در سایدبارِ تلگرام: آیکنِ برند + نامِ نمایشیِ مالک.
    fail-soft: کلیدِ ناشناس = بدونِ آیکن."""
    name = display_name(leg_key, config)
    icon = topic_icon(leg_key, config)
    return f"{icon} {name}" if icon else name

# کلیدهای قراردادیِ خروجیِ collect_feeds — همیشه همه حاضرند ({} در شکست).
FEED_KEYS = ("board", "guidance", "business", "heart", "registry", "telemetry", "legs")

_SOURCE_ICON = {"money": "💰", "blocked": "⏸", "approval": "🙋",
                "fear": "😨", "needs": "📌"}
# callback_data باید ASCII-تمیز و کوتاه بماند (سقفِ ۶۴ بایتِ تلگرام + بدونِ leak)
_ID_SAFE = re.compile(r"[^A-Za-z0-9_.\-]")


# ─── ابزارهای خالصِ کوچک ─────────────────────────────────────────────────────────
def scrub(text) -> str:
    """هر خطِ حاویِ echo ِ ممنوع → کلِ همان خط redact (هرگز نشتِ جزئی؛ بقیهٔ خطوط سالم).

    پاریته با execution_board._scrub در سطحِ فیلد؛ اینجا خط‌به‌خط تا یک فیلدِ آلوده
    کلِ statusِ مالک را نکشد. همیشه str برمی‌گرداند (fail-soft روی None/عدد)."""
    out = []
    for ln in str(text if text is not None else "").splitlines():
        low = ln.lower()
        out.append(_REDACTED if any(b in low or b in ln for b in _BANNED_ECHO) else ln)
    return "\n".join(out)


def _esc(s) -> str:
    """HTML escape (parse_mode=HTML) — fail-soft روی None."""
    return html.escape(str(s if s is not None else ""))


def _int(v, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _one(s, cap: int = 120) -> str:
    """یک‌خطی‌سازِ امن: فاصله‌های تو‌در‌تو/خطِ‌نو → یک فاصله؛ کران‌دار."""
    return " ".join(str(s if s is not None else "").split())[:cap]


def _import_soft(modname: str):
    """importِ تنبل و fail-soft از _ops (الگوی live/server.py: sys.path insert).

    فقط collect_feeds صدایش می‌زند — import-time ِ خودِ render خالص می‌ماند."""
    try:
        for sub in ("budget", "cortex", ""):
            p = str(_OPS / sub) if sub else str(_OPS)
            if p not in sys.path:
                sys.path.insert(0, p)
        import importlib
        return importlib.import_module(modname)
    except Exception:  # noqa: BLE001 — feedِ غایب هرگز صداکننده را نمی‌کشد
        return None


def _read_json(p: Path) -> dict:
    try:
        d = json.loads(p.read_text("utf-8")) if p.exists() else {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def display_name(leg_key: str, config: dict | None = None) -> str:
    """نامِ نمایشیِ یک پا: اول configِ مالک (display_names یا نگاشتِ مستقیم)، بعد
    پیش‌فرضِ LEGS، بعد خودِ کلید. fail-soft: configِ خراب = پیش‌فرض."""
    key = str(leg_key or "")
    try:
        cfg = config or {}
        names = cfg.get("display_names") if isinstance(cfg.get("display_names"), dict) else cfg
        n = names.get(key) if isinstance(names, dict) else None
        if n:
            return str(n)
    except Exception:  # noqa: BLE001
        pass
    return LEGS.get(key, key or "?")


# نگاشتِ ۸ پا به دایجستِ زنده — هر کلیدِ پا → {status, detail[, next]} از بهترینِ
# سیگنالِ موجود؛ پیش‌فرضِ آرام وقتی منبعِ زنده نیست (fail-soft).
_LEG_DEFAULT = {"status": "⚪", "detail": "سیگنالِ زنده‌ای نیست"}
_LEG_RANK = {"🔴": 3, "🟡": 2, "🟢": 1, "⚪": 0}


def _collect_legs(feeds: dict) -> dict:
    """۸ پا → {status, detail[, next]}: business_brain (نگاشتِ نام → lead / studio_pf)،
    part_loops (خلاصهٔ سلامت → system)، و پیش‌فرضِ آرام برای بقیه.

    fail-soft: هر منبعِ غایب/خراب → پیش‌فرض. containment: studio_pf فقط status/detail
    از pf projection ِ content-free را برمی‌دارد — نامِ نمایشی از LEGS/config
    می‌آید، هرگز از این‌جا (نامِ واقعی هیچ‌گاه لمس نمی‌شود)."""
    legs = {k: dict(_LEG_DEFAULT) for k in LEGS}

    # business_brain.summary() → projects: نگاشت با نام → lead / studio_pf
    biz = feeds.get("business") if isinstance(feeds.get("business"), dict) else {}
    for p in (biz.get("projects") or []):
        if not isinstance(p, dict):
            continue
        low = str(p.get("name") or "").lower()
        cell = {"status": _one(p.get("status"), 12) or "⚪",
                "detail": _one(p.get("detail"))}
        if "lead" in low:
            legs["lead"] = cell
        elif "project-f" in low or "project_f" in low:
            legs["studio_pf"] = cell            # content-free: فقط وضعیت/جزئیات، نه نام

    # part_loops.summary() → parts: خلاصهٔ سلامتِ درونی روی پای system
    pl = _import_soft("part_loops")
    if pl is not None:
        try:
            s = pl.summary()
            parts = s.get("parts") if isinstance(s.get("parts"), list) else []
            n_prop = _int(s.get("n_proposals"))
        except Exception:  # noqa: BLE001
            parts, n_prop = [], 0
        if parts:
            worst, attention = "🟢", 0
            for p in parts:
                st = str(p.get("status") or "") if isinstance(p, dict) else ""
                if _LEG_RANK.get(st, 0) > _LEG_RANK.get(worst, 0):
                    worst = st
                if st in ("🔴", "🟡"):
                    attention += 1
            cell = {"status": worst,
                    "detail": (f"{len(parts)} بخش · {attention} نیازِ توجه" if attention
                               else f"{len(parts)} بخش سالم")}
            if n_prop:
                cell["next"] = f"{n_prop} پیشنهاد در صف"
            legs["system"] = cell

    # cartographer: drift-pulse از ORGANISM-STATE (سنتینلِ کهنگیِ نقشه) — content-free
    org = feeds.get("organism") if isinstance(feeds.get("organism"), dict) else {}
    carto = org.get("cartographer") if isinstance(org.get("cartographer"), dict) else {}
    if carto:
        mood = str(carto.get("mood") or "🟢")
        age = carto.get("map_age_days")
        drift = _int(carto.get("drift_files"))
        age_s = f"{age}d" if isinstance(age, int) else "?"
        cell = {"status": mood if mood in _LEG_RANK else "🟢",
                "detail": f"نقشه {age_s} · drift {drift} فایل"}
        if carto.get("refresh_recommended"):
            cell["next"] = "refresh پیشنهاد — نقشه را دوباره بکش"
        legs["cartographer"] = cell

    # ziman: ضربانِ محلیِ ZimanLeg (ORGANISM-STATE["ziman"] — نوشتهٔ ziman_beat پشتِ
    # OCTOPUS_WIRE_ZIMAN). LEG-07: بدونِ این خواندن، پای زندهٔ زیمان تاریک می‌ماند.
    # block نبود = flag خاموش → پیش‌فرضِ آرام (byte-identical به قبل). content-free:
    # فقط money_link/شمارش‌ها؛ هیچ نامِ اثر/گالری اینجا نیست.
    zi = org.get("ziman") if isinstance(org.get("ziman"), dict) else {}
    if zi:
        ml = _one(zi.get("money_link"), 16) or "incubating"
        drafts = _int(zi.get("drafts_count"))
        prop = _int(zi.get("proposals_total"))
        cell = {"status": "🟢" if ml == "active" else "🟡",
                "detail": f"{ml} · {drafts} پیش‌نویس · {prop} پیشنهاد"}
        hint = _one(zi.get("inventory_hint"), 80)
        if hint:
            cell["next"] = hint
        legs["ziman"] = cell

    # ۴ پای بیزنسِ تازه (mining/crypto/accounting/knowledge): قراردادِ مشترک —
    # WP-C در business_legs_beat هر <name>_status() ({"leg","live","signal","note"})
    # را در ORGANISM-STATE["business_legs"] جمع می‌کند؛ اینجا فقط سطحی‌سازی می‌شود.
    # شکلِ مقدار آزاد (dict-به-نام یا list) — هر دو fail-soft. skeleton (live=False)
    # note ِ صادقش را نشان می‌دهد نه پیش‌فرضِ خالی. غیاب = پیش‌فرضِ آرام (بدون crash).
    bl = org.get("business_legs")
    # فیکسِ P0 (2026-07-15): business_legs_beat خروجی را دولایه می‌نویسد —
    # ORGANISM["business_legs"] == {"business_legs": {mining,...}, "beat": N} —
    # ولی این‌جا شکلِ تخت فرض شده بود → هر ۴ پا ساکت default رندر می‌شدند.
    # هر دو شکل پذیرفته می‌شود (backward-compatible): لایهٔ داخلی هست و بیرونی پا ندارد → سطحی‌سازی.
    if (isinstance(bl, dict) and isinstance(bl.get("business_legs"), dict)
            and "mining" not in bl):
        bl = bl["business_legs"]
    entries: dict = {}
    if isinstance(bl, dict):
        for k, v in bl.items():
            if isinstance(v, dict):
                entries[str(v.get("leg") or k)] = v
    elif isinstance(bl, list):
        for v in bl:
            if isinstance(v, dict) and v.get("leg"):
                entries[str(v.get("leg"))] = v
    for name in ("mining", "crypto", "accounting", "knowledge"):
        e = entries.get(name)
        if not isinstance(e, dict):
            continue
        live = bool(e.get("live"))
        signal = _one(e.get("signal"))
        note = _one(e.get("note"))
        # زنده → signalِ سرخط؛ skeleton/خاموش → note ِ صادق (چرا داده‌ای نیست).
        detail = (signal or note if live else note or signal) or _LEG_DEFAULT["detail"]
        cell = {"status": "🟢" if live else "⚪", "detail": detail}
        if live and note and note != detail:
            cell["next"] = note
        legs[name] = cell

    return legs


# ─── I/O ِ فقط‌خواندنی: جمعِ feedها ────────────────────────────────────────────────
def collect_feeds() -> dict:
    """همهٔ feedهای کنترل-پلین در یک dict — هر کلید مستقل، fail-soft، {} در شکست.

    کلیدها (FEED_KEYS): board (execution_board.board) · guidance (guidance_box.guidance)
    · business (business_brain.summary) · heart (pulse/heart-shadow-latest.json)
    · registry (registry/registry-latest.json) · telemetry (telemetry-latest.json — پول).
    هیچ نوشتنی، هیچ شبکه‌ای؛ فقط خواندنِ stateِ موجود."""
    feeds: dict = {k: {} for k in FEED_KEYS}

    eb = _import_soft("execution_board")
    if eb is not None:
        try:
            b = eb.board()
            feeds["board"] = b if isinstance(b, dict) else {}
        except Exception:  # noqa: BLE001
            feeds["board"] = {}

    gb = _import_soft("guidance_box")
    if gb is not None:
        try:
            g = gb.guidance()
            feeds["guidance"] = g if isinstance(g, dict) else {}
        except Exception:  # noqa: BLE001
            feeds["guidance"] = {}

    bb = _import_soft("business_brain")
    if bb is not None:
        try:
            s = bb.summary()
            feeds["business"] = s if isinstance(s, dict) else {}
        except Exception:  # noqa: BLE001
            feeds["business"] = {}

    ops = _import_soft("opslib")
    if ops is not None:
        try:
            state = ops.STATE_DIR
            feeds["heart"] = _read_json(state / "pulse" / "heart-shadow-latest.json")
            feeds["registry"] = _read_json(state / "registry" / "registry-latest.json")
            feeds["telemetry"] = _read_json(state / "telemetry-latest.json")
            feeds["organism"] = _read_json(state / "ORGANISM-STATE.json")   # per-leg blocks (cartographer…)
        except Exception:  # noqa: BLE001
            pass

    # ۹ پا → دایجستِ زنده (مصرفِ center.beat: feeds['legs'][leg]) — fail-soft
    try:
        feeds["legs"] = _collect_legs(feeds)
    except Exception:  # noqa: BLE001
        feeds["legs"] = {k: dict(_LEG_DEFAULT) for k in LEGS}
    return feeds


# ─── نمایش: status ِ پین‌شده (≤ ۵ خط، یک‌نگاه) ────────────────────────────────────
def render_status(feeds: dict | None) -> str:
    """statusِ یک‌نگاه (ADHD-first): کل + شمارشِ خطوط + ضربان + پول + «چی ازم می‌خوای».

    ≤ ۵ خطِ کوتاهِ HTML. ورودیِ خراب/خالی = statusِ آرامِ پیش‌فرض (هرگز crash)."""
    f = feeds if isinstance(feeds, dict) else {}
    board = f.get("board") if isinstance(f.get("board"), dict) else {}
    counts = board.get("counts") if isinstance(board.get("counts"), dict) else {}
    q, run = _int(counts.get("queued")), _int(counts.get("running"))
    blk, aw = _int(counts.get("blocked")), _int(counts.get("awaiting_user"))
    done, quar = _int(counts.get("done")), _int(counts.get("quarantined"))
    guid = f.get("guidance") if isinstance(f.get("guidance"), dict) else {}
    n_guid = _int(guid.get("n"))
    heart = f.get("heart") if isinstance(f.get("heart"), dict) else {}
    tel = f.get("telemetry") if isinstance(f.get("telemetry"), dict) else {}

    # کل: قرنطینه = 🔴؛ چیزی منتظرِ مالک/مسدود = 🟡؛ وگرنه 🟢 (ساده و صادق)
    if quar > 0:
        overall, mood = "🔴", "یه چیزی قرنطینه شده"
    elif aw + blk + n_guid > 0:
        overall, mood = "🟡", "چند چیز منتظرِ توئه"
    else:
        overall, mood = "🟢", "همه‌چیز روبه‌راهه"

    lanes = (f"🧵 صف {q} · ▶️ {run} · ⏸ {blk} · 🙋 {aw} · ✅ {done} · ☣️ {quar}")

    # ضربان + پول در یک خطِ فشرده (ارتقای بصری: عددها monospace با <code>) —
    # خطِ آزادشده صرفِ دیوایدرِ برند می‌شود؛ سقفِ ≤۵ خط (قانونِ ADHD) حفظ است.
    if heart:
        period = heart.get("period_s")
        pw = heart.get("production_wire") if isinstance(heart.get("production_wire"), dict) else {}
        wire = "سیم باز 🟢" if bool(pw.get("open")) else "سیم بسته 🔒"
        beat = (f"💓 <code>{_esc(period)}s</code> · {wire}" if period is not None
                else f"💓 سایه · {wire}")
    else:
        beat = "💓 قلب هنوز نتپیده (سایه)"

    aud = (tel.get("month") or {}).get("aud") if isinstance(tel.get("month"), dict) else None
    try:
        money = f"💰 <code>AU${float(aud):.2f}</code>" if aud is not None else "💰 —"
    except (TypeError, ValueError):
        money = "💰 —"

    ask = (f"🧭 {n_guid} تصمیم منتظرِ توست — یک‌تاپ آره/نه" if n_guid
           else "🧭 چیزی همین حالا ازت نمی‌خواد")

    return scrub("\n".join([f"{overall} <b>اختاپوس</b> — {mood}",
                            lanes, f"{beat} · {money}", DIVIDER, ask][:5]))


# ─── نمایش: دایجستِ یک پا (≤ ۳ خط) ────────────────────────────────────────────────
def render_leg_digest(leg_key: str, leg: dict | None, config: dict | None = None) -> str:
    """دایجستِ کوتاهِ یک پا: «وضعیت + نام» / جزئیات / قدمِ بعد. حداکثر ۳ خط.

    شکلِ leg آزاد است (fail-soft): status/detail|summary/next|next_action خوانده
    می‌شوند؛ هر چه نبود، خطش حذف می‌شود. نامِ نمایشی از configِ مالک (پیش‌فرض LEGS)."""
    # اتاقِ آینه پا نیست — وضعیتی ندارد که دایجست شود. بدونِ این، حلقهٔ دایجست
    # روزی یک «🪞 آینه ⚪ سیگنالِ زنده‌ای نیست» می‌فرستد؛ یعنی اتاقِ گفتگو با نویزِ
    # خودکار پر می‌شود. حلقه با متنِ خالی فقط سررسید را جلو می‌برد (بی‌ضرر).
    if str(leg_key or "") in ROOMS:
        return ""
    d = leg if isinstance(leg, dict) else {}
    name = display_name(leg_key, config)
    icon = LEG_ICONS.get(str(leg_key or ""), "")
    status = _one(d.get("status"), 12) or "⚪"
    detail = _one(d.get("detail") if d.get("detail") is not None else d.get("summary"))
    nxt = _one(d.get("next") if d.get("next") is not None else d.get("next_action"), 100)
    head = f"{icon} <b>{_esc(name)}</b> {_esc(status)}" if icon \
        else f"{_esc(status)} <b>{_esc(name)}</b>"
    lines = [head]
    if detail:
        lines.append(_esc(detail))
    if nxt:
        lines.append(f"↳ {_esc(nxt)}")
    return scrub("\n".join(lines[:3]))


# ─── نمایش: کارتِ پیشنهادِ بودجه (propose-only — هرگز budgets.yaml را دست نمی‌زند) ──
def latest_epoch() -> dict:
    """آخرین epoch-<ts>.json از governor (فقط‌خواندنی، fail-soft → {})."""
    try:
        d = _OPS / "budget" / "epochs"
        files = sorted(d.glob("epoch-*.json"), key=lambda p: p.name,
                       reverse=True) if d.exists() else []
        return json.loads(files[0].read_text("utf-8")) if files else {}
    except (OSError, ValueError, IndexError):
        return {}


def render_budget_proposal(epoch: dict | None = None) -> str:
    """کارتِ «پیشنهادِ تخصیصِ ماهِ بعد» — خروجیِ زندهٔ governor_epoch را به کارتِ propose-only
    تبدیل می‌کند. ناوردی: فقط نمایش/پیشنهاد؛ هیچ نوشتنی روی budgets.yaml، هیچ money-gate."""
    e = epoch if isinstance(epoch, dict) else latest_epoch()
    ad = e.get("allocation_dry") if isinstance(e.get("allocation_dry"), dict) else {}
    grants = ad.get("grants") if isinstance(ad.get("grants"), dict) else {}
    if not grants:
        return scrub("🐙 <b>پیشنهادِ بودجه</b>\nهنوز epochِ تخصیصی نیست (governor نتپیده).")
    cap, explore = ad.get("cap_monthly_aud"), ad.get("explore_reserve_aud")
    ha = e.get("heart_autoreg") if isinstance(e.get("heart_autoreg"), dict) else {}
    advice = _one(ha.get("explore_advice"), 60)
    h1 = ad.get("h1_check") if isinstance(ad.get("h1_check"), dict) else {}
    try:
        cap_s = f"AU${float(cap):.2f}" if cap is not None else "—"
    except (TypeError, ValueError):
        cap_s = "—"
    try:
        exp_s = f"AU${float(explore):.2f}" if explore is not None else "—"
    except (TypeError, ValueError):
        exp_s = "—"
    lines = ["🐙 <b>پیشنهادِ تخصیصِ ماهِ بعد</b> · <i>propose-only</i>",
             f"سقف {_esc(cap_s)} · رزروِ کشف {_esc(exp_s)}"]
    rows = []
    for organ, g in grants.items():
        if not isinstance(g, dict):
            continue
        try:
            rows.append((float(g.get("total_month_aud") or 0), organ))
        except (TypeError, ValueError):
            continue
    for tot, organ in sorted(rows, reverse=True)[:8]:
        lines.append(f"• {_esc(organ)}: <code>AU${tot:.2f}</code>")
    bb = e.get("allocation_barbell") if isinstance(e.get("allocation_barbell"), dict) else {}
    pct = bb.get("organ_pct") if isinstance(bb.get("organ_pct"), dict) else {}
    if pct:
        top = sorted(((float(v or 0), k) for k, v in pct.items()), reverse=True)[:3]
        lines.append("🎯 barbell: " + " · ".join(f"{_esc(k)} {v*100:.0f}%" for v, k in top))
    if advice:
        lines.append(f"↳ explore: {_esc(advice)}")
    lines.append(DIVIDER)
    lines.append("✅ جمعِ پیشنهاد ≤ سقف" if h1.get("ok") else "⚠️ جمعِ پیشنهاد را چک کن")
    lines.append("<i>این فقط پیشنهاد است — budgets.yaml دست‌نخورده می‌ماند.</i>")
    return scrub("\n".join(lines))


# ─── نمایش: کارتِ تصمیم (یک‌تاپ: ok/no/later) ─────────────────────────────────────
def _decision_id(item: dict) -> str:
    """شناسهٔ تصمیم برای callback_data: idِ داده‌شده (فقط نویسه‌های امنِ ASCII، کران‌دار،
    هرگز حاویِ echo ِ ممنوع) وگرنه هشِ پایدارِ محتوا (deterministic، content-free)."""
    raw = str(item.get("id") or "").strip()
    if raw:
        clean = _ID_SAFE.sub("", raw)[:48]
        if clean and not any(b in clean.lower() for b in _BANNED_ECHO):
            return clean
    basis = f"{item.get('q', '')}|{item.get('source', '')}|{item.get('why', '')}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


def render_decision(item: dict | None) -> tuple:
    """کارتِ تصمیمِ یک‌تاپ: (متنِ HTML، کیبورد). کیبورد = یک ردیفِ ۳ دکمه با
    callback_data دقیقاً 'ok:<id>' / 'no:<id>' / 'later:<id>' (قراردادِ center).

    item = آیتمِ guidance ({q, why, source, priority[, id]}) یا هر dictِ مشابه؛
    fail-soft: ورودیِ خراب = کارتِ عمومی با هشِ پایدار."""
    d = item if isinstance(item, dict) else {}
    did = _decision_id(d)
    icon = _SOURCE_ICON.get(str(d.get("source") or ""), "🙋")
    q = _one(d.get("q") if d.get("q") is not None else d.get("summary"), 160) or "یک تصمیم"
    why = _one(d.get("why"), 160)
    prio = _one(d.get("priority"), 12)
    head = f"{icon} <b>تصمیم</b>" + (f" · <i>{_esc(prio)}</i>" if prio else "")
    text = f"{head}\n{_esc(q)}"
    if why:
        text += f"\n<i>↳ {_esc(why)}</i>"
    if str(d.get("source") or "") in ("money", "approval"):
        # راست‌گوییِ دکمه (2026-07-17): این کارت settle نمی‌کند (idش نامرتبط با effect_id) —
        # ✅ِ اینجا فقط ack بود و پولِ واقعی معلق می‌ماند. تأییدِ واقعی فقط در کارتِ توکنِ
        # approval_channel است؛ پس دکمهٔ جعلیِ آره/نه حذف، فقط اطلاع + «دیدم».
        text += "\n<i>⚠️ تأیید/رد فقط در کارتِ اصلیِ تأیید (approval_channel) انجام می‌شود.</i>"
        return scrub(text), [[{"text": "⏳ باشه، دیدم", "callback_data": f"later:{did}"}]]
    keyboard = [[
        {"text": "✅ آره", "callback_data": f"ok:{did}"},
        {"text": "❌ نه", "callback_data": f"no:{did}"},
        {"text": "⏳ بعداً", "callback_data": f"later:{did}"},
    ]]
    return scrub(text), keyboard


# ─── مرکزِ فرماندهی: منو + کارت‌های کنترل (رأی مالک 2026-07-17) ────────────────────
# callback-verbهای قرارداد (ASCII، ≤64B): mn:<page> ناوبری · lg:<key>:p|r مکث/ادامه ·
# pw:<act> مسلح‌کردنِ اکشنِ حساس · pwc:<act> تأییدِ نهایی · fg:<FLAG> toggleِ فلگ.
_BACK = {"text": "🔙 منو", "callback_data": "mn:menu"}


def render_menu(power: bool = False, feeds: dict | None = None,
                paused: dict | None = None) -> tuple:
    """منوی اصلیِ فرماندهی — زنده و context-aware.

    قانونِ مهندسی: دکمهٔ اول باید «مهم‌ترین کارِ الانِ مالک» باشد، نه یک منوی ثابت.
    این تابع همچنان خالص است: فقط از feeds/paused تزریق‌شده می‌خواند و هیچ I/O ندارد.
    همهٔ دکمه‌ها content-free اند: شمارش/فعل/کلید، نه محتوا یا هویت."""
    f = feeds if isinstance(feeds, dict) else {}
    board = f.get("board") if isinstance(f.get("board"), dict) else {}
    counts = board.get("counts") if isinstance(board.get("counts"), dict) else {}
    guidance = f.get("guidance") if isinstance(f.get("guidance"), dict) else {}
    n_guid = _int(guidance.get("n"))
    quar = _int(counts.get("quarantined"))
    awaiting = _int(counts.get("awaiting_user"))
    blocked = _int(counts.get("blocked"))
    running = _int(counts.get("running"))
    q = _int(counts.get("queued"))
    pmap = paused if isinstance(paused, dict) else {}
    n_paused = sum(1 for v in pmap.values() if bool(v))

    mood = "نیاز فوری نیست"
    if quar:
        mood = f"{quar} قرنطینه نیازِ رسیدگی دارد"
    elif n_guid:
        mood = f"{n_guid} تصمیم منتظر توست"
    elif awaiting:
        mood = f"{awaiting} مورد منتظر پاسخ توست"
    elif blocked:
        mood = f"{blocked} مورد مسدود است"

    text = ("🐙 <b>مرکزِ فرماندهیِ اختاپوس</b>\n"
            f"🧭 اولویت الان: {_esc(mood)}\n"
            f"🧵 صف <code>{q}</code> · ▶️ <code>{running}</code> · ⏸ <code>{blocked}</code> · "
            f"🙋 <code>{awaiting}</code> · ☣️ <code>{quar}</code>\n"
            + ("⚡ ردهٔ قدرت: روشن" if power else "🔒 ردهٔ قدرت: خاموش"))

    kb: list = []
    # اولویت‌ها: هر چه خطر/نیاز بیشتر، بالاتر.
    if quar:
        kb.append([{"text": f"☣️ {quar} قرنطینه — رسیدگی", "callback_data": "mn:qr"}])
    if n_guid:
        kb.append([{"text": f"🧭 {n_guid} تصمیم منتظر تو", "callback_data": "mn:ap"}])
    if awaiting and not n_guid:
        kb.append([{"text": f"🙋 {awaiting} منتظر پاسخ تو", "callback_data": "mn:ap"}])
    if n_paused:
        kb.append([{"text": f"▶️ {n_paused} پای متوقف — ادامه؟", "callback_data": "mn:lg"}])
    if blocked and not (quar or n_guid):
        kb.append([{"text": f"⏸ {blocked} مسدود — بررسی وضعیت", "callback_data": "mn:st"}])

    # دکمه‌های همیشگی پایین‌تر می‌آیند؛ اما همچنان یک‌تاپ و عملگرا هستند.
    kb.extend([[{"text": "📊 وضعیت/تازه‌سازی", "callback_data": "mn:st"},
                {"text": "🦵 پاها", "callback_data": "mn:lg"}],
               [{"text": "🐙 بودجه", "callback_data": "mn:bg"},
                {"text": "💰 درآمد", "callback_data": "mn:rv"}],
               [{"text": "🗺 نقشه‌برداری", "callback_data": "mn:map"},
                {"text": "📮 صف تأیید", "callback_data": "mn:ap"}],
               [{"text": "🧬 مأموریت‌ها", "callback_data": "mn:ms"},
                {"text": "⚙️ سیستم", "callback_data": "mn:sy"}]])
    return scrub(text), kb


def render_organs(paused: dict | None, config: dict | None = None) -> tuple:
    """کارتِ پاها: وضعِ مکث/فعالِ هر پا + دکمهٔ برعکسش (راست‌گو: از فایلِ واقعی)."""
    p = paused if isinstance(paused, dict) else {}
    names = {**{k: k for k in p}, **(config or {}).get("display_names", {})} \
        if isinstance((config or {}).get("display_names"), dict) else {k: k for k in p}
    lines = ["🦵 <b>پاهای اختاپوس</b> — مکث/ادامه (بدونِ restart)"]
    kb: list = []
    for key, is_p in p.items():
        label = _esc(str(names.get(key, key)))
        lines.append(f"{'⏸' if is_p else '▶️'} {label}")
        kb.append([{"text": (f"▶️ ادامهٔ {label}" if is_p else f"⏸ مکثِ {label}"),
                    "callback_data": f"lg:{key}:{'r' if is_p else 'p'}"}])
    kb.append([_BACK])
    return scrub("\n".join(lines)), kb


def render_power(power: bool, sentinels: dict | None = None) -> tuple:
    """کارتِ سیستم: وضعِ واقعیِ سنتینل‌ها + اکشن‌ها (همه دوکلیک). ترمزِ اضطراری
    (پنیک/توقف/ادامه) همیشه آزاد است؛ restart/فلگ/بودجه پشتِ فلگِ قدرت."""
    s = sentinels if isinstance(sentinels, dict) else {}
    lines = ["⚙️ <b>کنترلِ سیستم</b>",
             f"{'🔴' if s.get('stop') else '🟢'} STOP-ORGANISM "
             f"· {'🔴' if s.get('halt') else '🟢'} HALT-ALL "
             f"· {'♻️' if s.get('restart') else '—'} restart-pending",
             "🟢 اضطراری (همیشه آزاد، دوکلیک): پنیک · توقف · ادامه"]
    if not power:
        lines.append("🔒 بقیه (ری‌استارت/فلگ/بودجه) پشتِ <code>OCTOPUS_TG_POWER=1</code>.")
    kb = [[{"text": "🚨 پنیک", "callback_data": "pw:pn"},
           {"text": "⛔ توقف", "callback_data": "pw:st"}],
          [{"text": "▶️ ادامه از پنیک", "callback_data": "pw:re"}],
          [{"text": "♻️ ری‌استارت 🔒" if not power else "♻️ ری‌استارت",
            "callback_data": "pw:rs"},
           {"text": "🚩 فلگ‌ها 🔒" if not power else "🚩 فلگ‌ها",
            "callback_data": "mn:fl"}],
          [_BACK]]
    return scrub("\n".join(lines)), kb


def render_flags(states: dict | None) -> tuple:
    """کارتِ فلگ‌ها (whitelist) — صادق: env=الان، file=بوتِ بعد؛ toggle دوکلیک."""
    st = states if isinstance(states, dict) else {}
    lines = ["🚩 <b>فلگ‌ها</b> — اثرِ تغییر فقط در بوتِ بعدی (♻️)"]
    kb: list = []
    for name, info in st.items():
        lines.append(f"• <code>{_esc(name)}</code> — {_esc(str(info))}")
        kb.append([{"text": f"🔁 {name}", "callback_data": f"pw:fg-{name}"}])
    kb.append([_BACK])
    return scrub("\n".join(lines)), kb


def render_confirm(action_label: str, act_key: str) -> tuple:
    """کارتِ تأییدِ دوکلیک — قدمِ دومِ هر اکشنِ حساس."""
    text = f"❗ <b>مطمئنی؟</b>\n{_esc(action_label)}\n<i>این تأیید ۳ دقیقه اعتبار دارد.</i>"
    kb = [[{"text": "✅ بله، اجرا کن", "callback_data": f"pwc:{act_key}"},
           {"text": "❌ انصراف", "callback_data": "mn:sy"}]]
    return scrub(text), kb


# ─── صفحهٔ نقشه‌برداری metadata (فاز D — فقط‌خواندنی، propose-only) ───────────────
def render_map_page(scan_state: dict | None = None) -> tuple:
    """کارتِ نقشه‌برداری: وضعیت اسکن + دکمه‌های شروع/وضعیت/گزارش.

    scan_state = خروجیِ metadata_scan.load_state()
    ({status, files_seen, dirs_seen, bytes_total, latest_manifest, ...}).
    خالص: فقط نمایش؛ اجرای واقعیِ scan در center/map:start با gیتِ owner انجام می‌شود.
    هیچ‌چیز مخرب: scan فقط metadata می‌خواند، ولی کارت start قبل از اجرا تصدیق می‌شود."""
    st = scan_state if isinstance(scan_state, dict) else {}
    status = str(st.get("status") or "idle")
    files = _int(st.get("files_seen"))
    dirs = _int(st.get("dirs_seen"))
    bytes_total = _int(st.get("bytes_total"))
    latest = st.get("latest_manifest")
    status_emoji = {"idle": "⚪", "running": "🔄", "done": "✅", "error": "❌"}.get(status, "⚪")
    lines = [f"🗺️ <b>نقشه‌برداری metadata</b> · <i>propose-only</i>",
             f"{status_emoji} وضعیت: <code>{_esc(status)}</code>"]
    if files or dirs:
        lines.append(f"📂 <code>{files:,}</code> فایل · <code>{dirs:,}</code> پوشه")
        try:
            lines.append(f"💾 <code>{float(bytes_total)/(1024*1024):.1f} MiB</code>")
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    if latest:
        lines.append(f"📄 آخرین manifest: <code>{_esc(str(latest))}</code>")
    else:
        lines.append("📄 هنوز manifestی ساخته نشده.")
    lines.append(DIVIDER)
    lines.append("<i>فقط metadata (path/size/mtime)؛ محتوای فایل هرگز خوانده نمی‌شود.</i>")
    # دکمه‌ها: شروع scan (خطر کم — فقط خواندن، ولی dry-run-نما)، وضعیت، گزارش، منو
    kb = [[{"text": "🗺 شروع scan metadata", "callback_data": "map:start"}],
          [{"text": "🔄 تازه‌سازی", "callback_data": "mn:map"},
           {"text": "📄 آخرین گزارش", "callback_data": "map:report"}],
          [{"text": "🔙 منو", "callback_data": "mn:menu"}]]
    return scrub("\n".join(lines)), kb


# ─── صفحهٔ صف تأیید واقعی (فاز E — bridge اختاپوس) ───────────────────────────────
_PAGE = 5          # سقفِ ردیف در هر صفحه (کیبوردِ تلگرام)
_RISK_ORDER = {"high": 0, "medium": 1, "med": 1, "read": 2, "low": 2}


def _by_priority(jobs: list) -> list:
    """پرخطرها اول. با سقفِ ۵ ردیف، **کدام** ۵تا مهم‌تر از خودِ سقف است:
    اگر یک کارتِ 🔴 در ردیفِ ۱۲ باشد، عملاً وجود ندارد."""
    return sorted([j for j in jobs if isinstance(j, dict)],
                  key=lambda j: _RISK_ORDER.get(str(j.get("risk") or "read"), 2))


# ─── بازمانده‌های مناظره: کارتِ واقعی با دکمهٔ واقعی (WS-E) ──────────────────────
DEBATE_JOB_TYPE = "debate"
DEBATE_FLAG = "OCTOPUS_WIRE_DEBATE_VERDICT"
_DEBATE_MAX = 3            # سه ردیف = شش دکمه؛ بیش از این کارت را غیرقابل‌خواندن می‌کند


def _debate_on() -> bool:
    return os.environ.get(DEBATE_FLAG) == "1"


def _ap_callback(action: str, jid: str, mint=None) -> str:
    """callback_data از **رجیستریِ** actions، نه از رشتهٔ hardcode.

    چرا این مسیر: callbackِ اختراعی دکمه‌ای می‌سازد که هیچ handlerی ندارد — بدتر از
    نبودِ دکمه، چون مالک فکر می‌کند رأی داد. `actions.approval.approve/reject` تنها
    دو مدخلی‌اند که `center._handle_approval_callback` امروز واقعاً اجرا می‌کند.
    توکنِ HMAC دقیقاً مثلِ حلقهٔ اصلیِ همین فایل الحاق می‌شود (وگرنه وقتی
    OCTOPUS_WIRE_CB_TOKEN روشن باشد، هر تپ «توکنِ نامعتبر» می‌خورد)."""
    name = "approval.approve" if action == "ok" else "approval.reject"
    base = ""
    try:
        _here = str(Path(__file__).resolve().parent)
        if _here not in sys.path:
            sys.path.insert(0, _here)
        import actions as _act  # noqa: WPS433 — lazy؛ import-time ِ render خالص می‌ماند
        base = str(_act.callback_for(name, id=jid) or "")
    except Exception:  # noqa: BLE001
        base = ""
    if not base:
        base = f"ap:{action}:{jid}"     # fail-soft: همان قراردادِ رجیستری
    return f"{base}:{mint(jid, action) or 'x'}" if callable(mint) else base


def _debate_pending_path() -> Path:
    """`_ops/debate/survivors-pending.jsonl` — پروژکشنی که پروسهٔ ارگانیسم می‌نویسد.

    env-اول (همان قرارداد `opslib.OPS`): مسیرِ مشتق از `__file__` بی‌صدا به درختِ
    **زنده** می‌خورد حتی وقتی نویسنده در worktree/تستِ ایزوله می‌نویسد — دو طرفِ این
    پل باید به یک فایل نگاه کنند وگرنه کارت همیشه خالی است."""
    ops = os.environ.get("OPS_DIR")
    base = Path(ops) if ops else Path(__file__).resolve().parent.parent
    return base / "debate" / "survivors-pending.jsonl"


def ingest_debate_survivors(limit: int = 200) -> list:
    """پروژکشنِ مناظره → jobِ واقعیِ صفِ تأیید. خروجی: ردیف‌های pending ِ debate.

    ⚠️ چرا این‌جا و نه در debate_loop: قفلِ `approval_store` یک `threading.RLock`
    است، پس ناوردیِ مستندش می‌گوید فقط **یک** پروسه اجازهٔ نوشتنِ approvals.json را
    دارد و آن پروسه همین مرکز است (گارد: S1-05 t_o_single_consumer_process_invariant).
    debate_loop داخلِ تیکِ organism می‌دود؛ اگر خودش add_pending می‌زد، می‌توانست
    approve ِ همان لحظهٔ مالک را clobber کند. پس ارگانیسم فقط append می‌کند و
    تبدیلش این‌جا — کنارِ تنها مصرف‌کنندهٔ `ap:` — انجام می‌شود.

    idempotent: شناسه‌ها قطعی‌اند (`dbt-<sig>`)، jobی که قبلاً تصمیم‌گرفته‌شده باشد
    دوباره ساخته نمی‌شود. fail-soft → [] (کارت بدونِ بخشِ مناظره رندر می‌شود)."""
    p = _debate_pending_path()
    try:
        import approval_store as _aps  # noqa: WPS433 — درونِ telegram_center: مجاز
    except Exception:  # noqa: BLE001
        return []
    seen: dict = {}
    try:
        if p.exists():
            for ln in p.read_text("utf-8", errors="replace").splitlines()[-limit:]:
                try:
                    rec = json.loads(ln)
                except ValueError:
                    continue
                if isinstance(rec, dict) and rec.get("id"):
                    seen[str(rec["id"])] = rec      # آخرین نسخهٔ هر شناسه برنده است
    except OSError:
        return []
    for jid, rec in seen.items():
        try:
            if _aps.get(jid) is not None:
                continue                            # قبلاً هست (pending یا تصمیم‌شده)
            _aps.add_pending({"id": jid, "type": DEBATE_JOB_TYPE,
                              "title": rec.get("title") or "ایدهٔ مناظره",
                              "risk": rec.get("risk") or "medium",
                              "requires_confirmation": True,
                              "source": f"debate:{rec.get('topic_id', '')}"})
        except Exception:  # noqa: BLE001 — یک ردیفِ خراب کلِ کارت را نمی‌کشد
            continue
    try:
        return [j for j in (_aps.load_pending() or [])
                if isinstance(j, dict) and str(j.get("type")) == DEBATE_JOB_TYPE]
    except Exception:  # noqa: BLE001
        return []


def render_debate_survivors(rows: list | None = None, mint=None) -> tuple:
    """(متن، کیبورد) برای ایده‌های مناظره‌ای که منتظرِ رأیِ مالک‌اند.

    rows = jobهای pending با ``type == "debate"`` (از approval_store.load_pending()).
    تا امروز این‌ها فقط یک **عدد** داخلِ کارتِ مغز بودند؛ اینجا هر ایده متنِ خودش و
    دو دکمهٔ آره/نه را می‌گیرد. شماره روی دکمه‌ها عمدی است: بدونِ آن سه ردیفِ «آره»
    از هم قابلِ تشخیص نیستند. rows تهی → ("", []) تا صداکننده چیزی نچسباند."""
    items = [r for r in (rows or []) if isinstance(r, dict)]
    if not items:
        return "", []
    page = items[:_DEBATE_MAX]
    lines = [f"⚖️ <b>مناظره</b> — <code>{len(items)}</code> ایده منتظرِ رأیِ توست"]
    kb: list = []
    for i, job in enumerate(page, 1):
        jid = str(job.get("id", "?"))[:48]
        lines.append(f"<b>{i}.</b> {_esc(_one(job.get('title'), 150))}")
        kb.append([{"text": f"✅ آره {i}", "callback_data": _ap_callback("ok", jid, mint)},
                   {"text": f"❌ نه {i}", "callback_data": _ap_callback("no", jid, mint)},
                   {"text": "📝 جزئیات", "callback_data": f"ap:detail:{jid}"}])
    hidden = len(items) - len(page)
    if hidden:
        lines.append(f"▸ {hidden} ایدهٔ دیگر در صف — بعد از رأی به این‌ها می‌آیند")
    return scrub("\n".join(lines)), kb


def render_approvals_queue(pending: list | None = None,
                           summary_counts: dict | None = None,
                           legacy_recent: list | None = None,
                           mint=None, offset: int = 0) -> tuple:
    """کارتِ صفِ تأیید: pending jobs با دکمه‌های ap:ok/no/detail.

    pending = approval_store.load_pending()
    summary_counts = approval_store.summary()  ({pending,approved,rejected,done})
    legacy_recent = approval_store.sync_to_octopus_state()["recent"]  (تاریخچه).

    هر job با id/type/risk نشان داده می‌شود (content-free). risk=read → دکمهٔ تأیید
    سبک؛ risk=high → هشدار + نیاز به power-gate جداگانه (اینجا فقط ack)."""
    pend = pending if isinstance(pending, list) else []
    sc = summary_counts if isinstance(summary_counts, dict) else {}
    leg = legacy_recent if isinstance(legacy_recent, list) else []

    # ۲۰۲۶-۰۷-۲۷ — قبلاً هدر عددِ درست (۴۵) می‌گفت و بدنه ۵ ردیف نشان می‌داد،
    # **بدونِ هیچ اشاره‌ای** به ۴۰ تای دیگر و بدونِ هیچ راهی برای رسیدن به آن‌ها.
    # عددِ صادق در هدر، بریدنِ خاموش در بدنه را جبران نمی‌کند: مالک می‌دید ۴۵ تا
    # هست ولی نمی‌توانست بیش از ۵ تا را لمس کند.
    pend = _by_priority(pend)
    # ── WS-E (پشتِ OCTOPUS_WIRE_DEBATE_VERDICT، پیش‌فرض خاموش) ────────────────
    # ایده‌های مناظره از فهرستِ صفحه‌بندی‌شده بیرون کشیده می‌شوند و بخشِ خودشان را
    # می‌گیرند. علتش اندازه‌گیری است، نه سلیقه: امروز هر ۹۴ jobِ pending ِ زنده
    # risk=high‌اند، پس یک ایدهٔ risk=medium در صفحهٔ ۱۹ می‌افتد — یعنی دکمه‌ای که
    # هست ولی هیچ‌وقت دیده نمی‌شود، همان «خاموش دقیقاً روی خطی که رفتار عوض می‌شود».
    # فلگ خاموش → dbt_rows تهی، pend دست‌نخورده، خروجی بایت‌به‌بایتِ امروز.
    dbt_rows: list = []
    if _debate_on():
        dbt_rows = ingest_debate_survivors()      # پروژکشن → jobِ واقعی (این پروسه)
        _dbt_ids = {str(j.get("id")) for j in dbt_rows}
        _dbt_ids |= {str(j.get("id")) for j in pend
                     if str(j.get("type")) == DEBATE_JOB_TYPE}
        if _dbt_ids:
            # از فهرستِ صفحه‌بندی‌شده بیرون (وگرنه دو بار دکمه می‌گیرند)
            pend = [j for j in pend if str(j.get("id")) not in _dbt_ids]
            _have = {str(j.get("id")) for j in dbt_rows}
            dbt_rows += [j for j in (pending if isinstance(pending, list) else [])
                         if isinstance(j, dict) and str(j.get("type")) == DEBATE_JOB_TYPE
                         and str(j.get("id")) not in _have]
    total = len(pend)
    try:
        off = max(0, min(int(offset), max(0, total - 1)))
    except (TypeError, ValueError):
        off = 0
    page = pend[off:off + _PAGE]
    hidden = max(0, total - (off + len(page)))
    n_pend = _int(sc.get("pending")) or total
    lines = [f"📮 <b>صف تأیید</b> · <code>{n_pend}</code> منتظر",
             f"✅ تأییدشده <code>{_int(sc.get('approved'))}</code> · "
             f"❌ ردشده <code>{_int(sc.get('rejected'))}</code> · "
             f"🎯 انجام‌شده <code>{_int(sc.get('done'))}</code>"]
    dbt_text, dbt_kb = render_debate_survivors(dbt_rows, mint=mint)
    if dbt_text:
        lines.append(DIVIDER)
        lines.append(dbt_text)
    if not pend:
        lines.append("هیچ jobی منتظرِ تأیید نیست.")
    else:
        lines.append(DIVIDER)
        for job in page:
            if not isinstance(job, dict):
                continue
            jid = str(job.get("id", "?"))[:48]
            risk = str(job.get("risk", "read"))[:12]
            title = _one(job.get("title"), 60)
            risk_emoji = "🔴" if risk == "high" else ("🟡" if risk == "medium" else "🟢")
            lines.append(f"{risk_emoji} <code>{_esc(jid)}</code> · {_esc(title)}")
        if hidden or off:
            lines.append(f"▸ نمایش {off + 1}–{off + len(page)} از {total} "
                         f"(پرخطر اول){' · ' + str(hidden) + ' تای دیگر مانده' if hidden else ''}")
    if leg:
        lines.append(DIVIDER)
        lines.append("📜 آخرین verdictها:")
        for v in leg[:3]:
            if isinstance(v, dict):
                emo = {"ok": "✅", "no": "❌", "later": "⏳"}.get(str(v.get("verdict")), "•")
                lines.append(f"{emo} <code>{_esc(str(v.get('id', '?'))[:32])}</code>")
    # کیبورد: بازمانده‌های مناظره اول (اگر فلگ روشن) + per-job ok/no/detail + refresh
    kb: list = list(dbt_kb)
    for job in page:
        if not isinstance(job, dict):
            continue
        jid = str(job.get("id", "?"))[:48]
        # P3 (2026-07-20 Stage-1): اگر mint داده شده (فلگ OCTOPUS_WIRE_CB_TOKEN روشن)،
        # ok/no توکنِ HMAC می‌گیرند → ap:ok:<id>:<tok>. mint=None → بایت‌به‌بایتِ قبلی.
        # detail خواندنی است و توکن نمی‌گیرد.
        if callable(mint):
            ok_cb = f"ap:ok:{jid}:{mint(jid, 'ok') or 'x'}"
            no_cb = f"ap:no:{jid}:{mint(jid, 'no') or 'x'}"
        else:
            ok_cb, no_cb = f"ap:ok:{jid}", f"ap:no:{jid}"
        kb.append([{"text": f"✅ تأیید {jid[:20]}", "callback_data": ok_cb},
                   {"text": f"❌ رد {jid[:20]}", "callback_data": no_cb},
                   {"text": "📝 جزئیات", "callback_data": f"ap:detail:{jid}"}])
    # صفحه‌بندی: بدونِ این، آیتمِ ششم به بعد از هیچ سطحی قابلِ لمس نبود.
    nav = []
    if off > 0:
        nav.append({"text": "◀️ قبلی",
                    "callback_data": f"ap:page:{max(0, off - _PAGE)}"})
    if hidden:
        nav.append({"text": f"بعدی ({hidden}) ▶️",
                    "callback_data": f"ap:page:{off + _PAGE}"})
    if nav:
        kb.append(nav)
    kb.append([{"text": "🔄 تازه‌سازی", "callback_data": "mn:ap"}])
    kb.append([{"text": "🔙 منو", "callback_data": "mn:menu"}])
    return scrub("\n".join(lines)), kb


# ─── نمایش: کارتِ درآمد (aggregate، PII-safe — نامِ شریک هرگز echo نمی‌شود) ────────
def render_revenue(rev: dict | None = None) -> str:
    """کارتِ نمایشِ درآمد (aggregate، PII-safe): جمعِ CONFIRMED AUD، پوششِ انتساب،
    شمارشِ claimed/confirmed، و per-cell. نامِ شریک هرگز echo نمی‌شود (فقط شمارش + جمع).
    دیدِ خودتأمینیِ اختاپوس؛ هیچ money-gate/نوشتنی."""
    d = rev if isinstance(rev, dict) else {}
    by_cell = d.get("by_cell") if isinstance(d.get("by_cell"), dict) else {}
    by_partner = d.get("by_partner") if isinstance(d.get("by_partner"), dict) else {}
    coverage = d.get("attribution_coverage")
    claimed, confirmed = _int(d.get("claimed")), _int(d.get("confirmed"))
    total = 0.0
    for v in by_cell.values():
        try:
            total += float(v or 0)
        except (TypeError, ValueError):
            continue
    cov_s = f"{float(coverage)*100:.0f}%" if isinstance(coverage, (int, float)) else "—"
    lines = ["💰 <b>درآمدِ تأییدشده</b> (aggregate)",
             f"جمع <code>AU${total:.2f}</code> · پوشش {cov_s} · "
             f"{confirmed}/{claimed} تأیید/ادعا"]
    rows = []
    for cell, v in by_cell.items():
        try:
            rows.append((float(v or 0), cell))
        except (TypeError, ValueError):
            continue
    for amt, cell in sorted(rows, reverse=True)[:8]:
        lines.append(f"• {_esc(cell)}: <code>AU${amt:.2f}</code>")
    if not rows:
        lines.append("هنوز per-cellِ تأییدشده‌ای نیست.")
    if by_partner:
        psum = 0.0
        for v in by_partner.values():
            try:
                psum += float(v or 0)
            except (TypeError, ValueError):
                continue
        lines.append(DIVIDER)
        lines.append(f"👥 {len(by_partner)} شریک · جمعِ سهم <code>AU${psum:.2f}</code>")
    return scrub("\n".join(lines))


if __name__ == "__main__":
    # فقط‌خواندنی: نمونهٔ statusِ زنده از stateِ موجود (هیچ ارسال/نوشتنی)
    print(render_status(collect_feeds()))
