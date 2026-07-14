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
}

# برندینگِ بصریِ هر پا (رأی مالک: media-first، آیکنِ ثابت per پا) — جدا از LEGS تا
# قراردادِ نام‌ها (تست/`display_name`) دست‌نخورده بماند. HQ برای تاپیک/هدرِ فرماندهی.
LEG_ICONS = {
    "lead": "🎨", "ziman": "🖼", "mining": "⛏", "crypto": "📈",
    "accounting": "🧾", "studio_pf": "🎬", "system": "⚙️", "knowledge": "🧠",
    "cartographer": "🗺",
    "hq": "🐙",
}
DIVIDER = "─────── ✦ ───────"


def topic_title(leg_key: str, config: dict | None = None) -> str:
    """عنوانِ تاپیکِ یک پا در سایدبارِ تلگرام: آیکنِ برند + نامِ نمایشیِ مالک.
    fail-soft: کلیدِ ناشناس = بدونِ آیکن."""
    name = display_name(leg_key, config)
    icon = LEG_ICONS.get(str(leg_key or ""))
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
    keyboard = [[
        {"text": "✅ آره", "callback_data": f"ok:{did}"},
        {"text": "❌ نه", "callback_data": f"no:{did}"},
        {"text": "⏳ بعداً", "callback_data": f"later:{did}"},
    ]]
    return scrub(text), keyboard


if __name__ == "__main__":
    # فقط‌خواندنی: نمونهٔ statusِ زنده از stateِ موجود (هیچ ارسال/نوشتنی)
    print(render_status(collect_feeds()))
