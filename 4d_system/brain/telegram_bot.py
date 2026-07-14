"""
brain/telegram_bot.py — رابطِ تلگرامِ «خیلی ساده» (ADHD-محور).

هدف: با ADHD و چند پروژه، در یک پیامِ کوتاه بدانی «کجایی، این پروژه چیست، و فقط
یک تصمیم باهات کار دارد». همه‌چیز با دکمه (نه تایپ)، آرام و بدونِ سرریز.

امنیت: فقط به chat_idِ مالک (TELEGRAM_CHAT_ID) پاسخ می‌دهد؛ هر پیامِ دیگری نادیده.
تأییدِ کد از همین‌جا هم می‌رود از گیتِ کاملِ self_code (تست + TCB + بازگردانی).

اجرا:  python -m brain.telegram_bot     (کنارِ python -m brain.daemon)
long-polling است — نه webhook، نه URLِ عمومی لازم دارد.
"""
from __future__ import annotations

import os
import time
import logging

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"


# ── پیکربندی ─────────────────────────────────────────────────────────────

def _token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


def _owner_id() -> str:
    return os.getenv("TELEGRAM_CHAT_ID", "").strip()


def is_configured() -> bool:
    return bool(_token() and _owner_id())


def _is_owner(chat_id) -> bool:
    return str(chat_id) == _owner_id()


# ── شبکه (نازک) ──────────────────────────────────────────────────────────

def _api(method: str, **params):
    import requests
    try:
        r = requests.post(_API.format(token=_token(), method=method),
                          json=params, timeout=35)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        logger.warning("telegram %s failed: %s", method, type(e).__name__)
        return None


def _kb(rows: list[list[tuple[str, str]]]) -> dict:
    """inline keyboard از (متن, callback_data)."""
    return {"inline_keyboard": [
        [{"text": t, "callback_data": d} for t, d in row] for row in rows]}


# ── داده‌ها (دفاعی) ──────────────────────────────────────────────────────

def _snapshot() -> dict:
    """وضعیتِ فشرده از منابعِ موجود؛ هر بخش مستقل fail-safe."""
    s = {"paused": False, "last_tick": "—", "generation": 0,
         "frontier": None, "pending": 0, "budget": None, "running_hint": ""}
    try:
        from brain.daemon import _load_state, _pause_path
        st = _load_state()
        s["paused"] = _pause_path().exists()
        s["last_tick"] = (st.get("last_tick_at") or "—")[11:16]
        s["generation"] = st.get("generation", 0)
    except Exception:
        pass
    try:
        from brain import self_code
        s["pending"] = len(self_code.list_pending())
    except Exception:
        pass
    try:
        from brain import budget
        b = budget.status()
        s["budget"] = f"{b.get('cloud_calls','?')}/{b.get('cap','?')}"
    except Exception:
        pass
    try:
        from brain import frontier
        for name in ("coverage", "distinct_cells"):
            if hasattr(frontier, name):
                v = getattr(frontier, name)
                s["frontier"] = v() if callable(v) else v
                break
    except Exception:
        pass
    return s


def _current_goal() -> str:
    try:
        from brain import research_agenda as ra
        now = ra.goals_now()
        if now:
            return now[0].get("title_fa") or now[0].get("title", "—")
        return (ra.MISSION_FA or "—")[:80]
    except Exception:
        return "کشفِ ساختارِ پنهان + آزمونِ نظریه‌های شناخت"


# ── سازنده‌های پیام (خالص، تست‌پذیر) ─────────────────────────────────────

PROJECT_LABEL = "🌌 ایده‌یاب (4d_system)"


def build_status_text(s: dict | None = None) -> str:
    s = s or _snapshot()
    state = "⏸ مکث" if s["paused"] else "🟢 فعال"
    attention = (f"⚠️ *{s['pending']} پیشنهادِ کد* منتظرِ توست"
                 if s["pending"] else "✅ چیزی لازم نیست — آروم باش")
    frontier = f" · مرزِ دانش {s['frontier']}" if s["frontier"] is not None else ""
    return (
        f"{PROJECT_LABEL}\n"
        f"🎯 {_current_goal()}\n\n"
        f"{state} · نسل {s['generation']}{frontier}\n"
        f"آخرین فعالیت: {s['last_tick']} · بودجه {s.get('budget','—')}\n\n"
        f"{attention}"
    )


def build_goal_text() -> str:
    try:
        from brain import research_agenda as ra
        mission = (ra.MISSION_FA or "")[:220]
    except Exception:
        mission = "بسترِ آزمونِ نظریه‌های شناخت + کشفِ بُعدِ پنهان."
    return (f"{PROJECT_LABEL}\n\n🎯 *چرا این پروژه؟*\n{mission}\n\n"
            f"📍 هدفِ الان: {_current_goal()}\n\n"
            f"_وقتی گم شدی، همین‌جا رو بخون. یه قدم کافیه._")


def build_pending_text(proposals: list[dict]) -> str:
    if not proposals:
        return f"{PROJECT_LABEL}\n\n✅ هیچ پیشنهادِ کدی منتظرِ تأیید نیست. آروم باش."
    lines = [f"{PROJECT_LABEL}", "", f"🧩 *{len(proposals)} پیشنهادِ کد* (هرکدوم آزمونش سبز شده):", ""]
    for p in proposals[:5]:
        lines.append(f"• `{p.get('target','?')}` — {(p.get('rationale','') or '')[:60]}")
    lines.append("\nبرای هرکدوم دکمه‌ی تأیید/رد پایینه 👇")
    return "\n".join(lines)


def build_portrait_text() -> str:
    """خودنگاره‌ی کوتاه — «من چه‌ام، چه آموختم» (ADHD: کوتاه)."""
    try:
        from brain import self_growth
        caps = self_growth.learned_capabilities(5)
        focus = self_growth.current_focus(len(caps))
    except Exception:
        return f"{PROJECT_LABEL}\n\n🪞 خودنگاره در دسترس نیست."
    lines = [f"{PROJECT_LABEL}", "", "🪞 *خودنگاره* (صادقانه: خودمدل، نه آگاهی)", "",
             f"🎯 کانونِ الان: {focus.get('goal','—')}"]
    if focus.get("limitation"):
        lines.append(f"🧩 روی محدودیت: {focus['limitation'][:60]}")
    lines.append("\n📚 *تازه چه آموختم* (با تأییدِ تو):")
    if caps:
        for c in caps:
            lines.append(f"• `{c.get('target','')}` → {(c.get('goal') or '')[:40]}")
    else:
        lines.append("• هنوز قابلیتی با تأییدِ تو آموخته نشده")
    return "\n".join(lines)


def _main_kb(s: dict) -> dict:
    pause_btn = ("▶️ ادامه", "resume") if s["paused"] else ("⏸ مکث", "pause")
    return _kb([
        [("📋 وضعیت", "status"), ("🎯 چرا؟", "goal")],
        [(f"🧩 تأییدها ({s['pending']})", "pending"), ("🪞 خودنگاره", "portrait")],
        [pause_btn],
    ])


# ── مسیریابی (خالص) ──────────────────────────────────────────────────────

_HELP = (f"{PROJECT_LABEL}\n\nدستورها (یا فقط دکمه بزن):\n"
         "/status — کجاییم + تنها کارِ منتظرِ تو\n"
         "/goal — چرا این پروژه (بازـتمرکز)\n"
         "/pending — پیشنهادهای کد برای تأیید\n"
         "/pause · /resume — مکث/ادامه‌ی خودمختار\n")


def route_command(text: str) -> tuple[str, dict | None]:
    """(متن, keyboard) برای یک فرمانِ متنی. side-effect فقط pause/resume."""
    cmd = (text or "").strip().lower().split()[0] if text.strip() else ""
    cmd = cmd.lstrip("/")
    if cmd in ("start", "status", ""):
        s = _snapshot()
        return build_status_text(s), _main_kb(s)
    if cmd == "goal":
        return build_goal_text(), _main_kb(_snapshot())
    if cmd == "portrait":
        return build_portrait_text(), _main_kb(_snapshot())
    if cmd == "pending":
        from brain import self_code
        props = self_code.list_pending()
        return build_pending_text(props), _pending_kb(props)
    if cmd == "pause":
        _set_pause(True)
        return "⏸ مکث شد. هر وقت خواستی /resume بزن.", _main_kb(_snapshot())
    if cmd == "resume":
        _set_pause(False)
        return "▶️ ادامه دادیم. 🟢", _main_kb(_snapshot())
    if cmd == "help":
        return _HELP, None
    return _HELP, None


def _pending_kb(proposals: list[dict]) -> dict | None:
    if not proposals:
        return _kb([[("📋 وضعیت", "status")]])
    rows = []
    for p in proposals[:5]:
        pid = p["id"]
        rows.append([(f"✅ {p.get('target','?').split('/')[-1]}", f"approve:{pid}"),
                     ("❌", f"reject:{pid}")])
    rows.append([("📋 وضعیت", "status")])
    return _kb(rows)


def route_callback(data: str) -> tuple[str, dict | None, str]:
    """(متن, keyboard, alert کوتاه) برای دکمه‌ها. approve/reject → گیتِ self_code."""
    data = data or ""
    if data == "status":
        s = _snapshot()
        return build_status_text(s), _main_kb(s), ""
    if data == "goal":
        return build_goal_text(), _main_kb(_snapshot()), ""
    if data == "portrait":
        return build_portrait_text(), _main_kb(_snapshot()), ""
    if data == "pending":
        from brain import self_code
        props = self_code.list_pending()
        return build_pending_text(props), _pending_kb(props), ""
    if data == "pause":
        _set_pause(True)
        return "⏸ مکث شد.", _main_kb(_snapshot()), "مکث ✓"
    if data == "resume":
        _set_pause(False)
        return "▶️ ادامه.", _main_kb(_snapshot()), "ادامه ✓"
    if data.startswith("approve:"):
        pid = data.split(":", 1)[1]
        from brain import self_code
        res = self_code.approve(pid)
        ok = res.get("ok")
        props = self_code.list_pending()
        txt = ("✅ *اعمال شد!* " + res.get("reason", "")) if ok else \
              ("❌ نشد: " + res.get("reason", ""))
        return txt + "\n\n" + build_pending_text(props), _pending_kb(props), \
            ("اعمال شد ✓" if ok else "نشد")
    if data.startswith("reject:"):
        pid = data.split(":", 1)[1]
        from brain import self_code
        self_code.reject(pid)
        props = self_code.list_pending()
        return "❌ رد شد.\n\n" + build_pending_text(props), _pending_kb(props), "رد شد"
    s = _snapshot()
    return build_status_text(s), _main_kb(s), ""


def _set_pause(on: bool) -> None:
    try:
        from brain.daemon import _pause_path
        p = _pause_path()
        if on:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("paused", encoding="utf-8")
        elif p.exists():
            p.unlink()
    except Exception as e:
        logger.warning("set_pause failed: %s", e)


# ── حلقه‌ی long-poll ─────────────────────────────────────────────────────

def poll_once(offset: int) -> int:
    """یک دورِ getUpdates + پردازش. آخرین update_id+1 را برمی‌گرداند."""
    resp = _api("getUpdates", offset=offset, timeout=30)
    if not resp or not resp.get("ok"):
        return offset
    for upd in resp.get("result", []):
        offset = upd["update_id"] + 1
        try:
            if "message" in upd:
                msg = upd["message"]
                chat_id = msg.get("chat", {}).get("id")
                if not _is_owner(chat_id):
                    continue                       # فقط مالک
                text, kb = route_command(msg.get("text", ""))
                _api("sendMessage", chat_id=chat_id, text=text,
                     parse_mode="Markdown", reply_markup=kb)
            elif "callback_query" in upd:
                cq = upd["callback_query"]
                chat_id = cq.get("message", {}).get("chat", {}).get("id")
                if not _is_owner(chat_id):
                    continue
                _api("answerCallbackQuery", callback_query_id=cq["id"])
                text, kb, alert = route_callback(cq.get("data", ""))
                _api("sendMessage", chat_id=chat_id, text=text,
                     parse_mode="Markdown", reply_markup=kb)
        except Exception as e:
            logger.error("update handling error: %s", e)
    return offset


def run_bot() -> None:
    if not is_configured():
        print("تلگرام تنظیم نشده — TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID را در .env بگذار.")
        print("راهنما: TELEGRAM_SETUP.md")
        return
    print("🤖 بات روشن شد. در تلگرام /start بزن.  (Ctrl+C برای توقف)")
    # پیامِ خوش‌آمد
    s = _snapshot()
    _api("sendMessage", chat_id=_owner_id(),
         text="🤖 بات روشنه.\n\n" + build_status_text(s),
         parse_mode="Markdown", reply_markup=_main_kb(s))
    offset = 0
    while True:
        try:
            offset = poll_once(offset)
        except KeyboardInterrupt:
            print("\nبات خاموش شد.")
            break
        except Exception as e:
            logger.error("poll loop error: %s", e)
            time.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s")
    run_bot()
