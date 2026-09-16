#!/usr/bin/env python3
"""
ORPHAN 2026-07-16 → REVIVED 2026-08-02: path mismatch fixed (paused.flag → daemon.pause).
4D brain APIs all verified present (self_code, budget, frontier, research_agenda, self_growth, events).
Zero live callers remains — wiring into _ops telegram launch chain is the next step (see Track B plan).

⚠️ **DEPRECATED (۲۰۲۶-۰۸-۰۹، رأیِ مالک، مگاپرامپتِ تناقضات، آیتمِ ب-۱۱).**
تردیدِ قبلی («REVIVED + Track B plan فعال ممکن است پشتش باشد») با حافظهٔ خودِ
اختاپوس رفع شد: [[../../07 - Knowledge/_audit/OPEN_LOOPS|OPEN_LOOPS.md]] صریح
می‌گوید «Track B هرگز روی ledger زنده نرفته — ۰ رویدادِ MONEY_ATTRIBUTION،
reconcile/ فقط README». یعنی «REVIVED» بالا آرزو بود نه واقعیت. retire رسمی:
`approval_channel.py` (۴۹۱۷ خط) صفِ تأییدِ واقعیِ زندهٔ باتِ تلگرام است و
کافی است. این فایل کدِ زنده‌ای نمی‌شکند؛ اگر قابلیتِ نویی لازم شد، به
approval_channel.py اضافه شود، نه این‌جا.

approval_channel_merge.py — پلِ ادغامِ کانالِ تأییدِ _ops با مغزِ 4d_system.

هدف: یک Unified Approval Channel بسازد که هر دو دنیا (_ops governance + 4d_system brain)
را بشناسد. این ماژول رویِ TelegramApprovalChannel موجود می‌نشیند و قابلیت‌های
brain-aware (وضعیتِ daemon، pending proposals، budget cloud) را اضافه می‌کند.

(CH-04: Telegram bot unify → _ops/budget/approval_channel_merge.py)

قرارداد:
  • واردکردنِ این ماژول TelegramApprovalChannel را از approval_channel وارد می‌کند.
  • کلاسِ UnifiedApprovalChannel از TelegramApprovalChannel ارث‌می‌برد.
  • هیچ کدِ قدیمی شکسته نمی‌شود — approval_channel.py دست‌نخورده می‌ماند.
  • event emission به هر دو سیستم (brain/events.py + _ops/events.py).
  • stdlib-only — هیچ وابستگیٔ خارجی.

نحوهٔ استفاده:
    from approval_channel_merge import UnifiedApprovalChannel
    ch = UnifiedApprovalChannel(token=..., owner_chat_id=...)
    ch.run_forever()
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# ── bootstrap مسیر ─────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# approval_channel اصلی را وارد کن (بدون تغییر)
from approval_channel import (
    TelegramApprovalChannel,
    Approval,
    _load_offset,
    _save_offset,
    _cteq,
    _today_iso,
    _mask_token,
    TELEGRAM_API_BASE,
)
import opslib  # noqa: E402

logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────
# مسیرهای مغز (4d_system)
# REVIVAL 2026-08-02: was `paused.flag` (never existed). daemon.py line 54 uses
# `daemon.pause`; canonical stop is `daemon.stop` (line 47). Path mismatch was the
# only real rot — every 4D brain API imported below still exists.
_4D_ROOT = _HERE.parents[1] / "4d_system"
_4D_OUTPUT = _4D_ROOT / "outputs"
_DAEMON_STATE = _4D_OUTPUT / "daemon_state.json"
_PAUSE_FILE = _4D_OUTPUT / "daemon.pause"

# ── helpers: brain state (fail-safe) ───────────────────────────────────────


def _brain_snapshot() -> dict:
    """وضعیتِ فشردهٔ 4d_system را برمی‌گرداند؛ هر بخش مستقل fail-safe."""
    s = {
        "paused": False,
        "last_tick": "—",
        "generation": 0,
        "frontier": None,
        "pending": 0,
        "budget": None,
        "running_hint": "",
    }
    # ۱) pause state
    try:
        s["paused"] = _PAUSE_FILE.exists()
    except OSError:
        pass
    # ۲) daemon_state.json
    try:
        if _DAEMON_STATE.exists():
            ds = json.loads(_DAEMON_STATE.read_text("utf-8"))
            s["generation"] = int(ds.get("generation", 0))
            s["last_tick"] = (ds.get("last_tick_at") or "—")[11:16]
    except Exception:
        pass
    # ۳) pending proposals (self_code)
    try:
        sys.path.insert(0, str(_4D_ROOT / "brain"))
        import self_code  # noqa: E402
        s["pending"] = len(self_code.list_pending())
    except Exception:
        pass
    # ۴) cloud budget
    try:
        sys.path.insert(0, str(_4D_ROOT / "brain"))
        import budget  # noqa: E402
        b = budget.status()
        s["budget"] = f"{b.get('cloud_calls', '?')}/{b.get('cap', '?')}"
    except Exception:
        pass
    # ۵) frontier
    try:
        sys.path.insert(0, str(_4D_ROOT / "brain"))
        import frontier  # noqa: E402
        for name in ("coverage", "distinct_cells"):
            if hasattr(frontier, name):
                v = getattr(frontier, name)
                s["frontier"] = v() if callable(v) else v
                break
    except Exception:
        pass
    return s


def _brain_current_goal() -> str:
    """هدفِ پژوهشیِ فعلی از research_agenda."""
    try:
        sys.path.insert(0, str(_4D_ROOT / "brain"))
        import research_agenda as ra  # noqa: E402
        now = ra.goals_now()
        if now:
            return now[0].get("title_fa") or now[0].get("title", "—")
        return (ra.MISSION_FA or "—")[:80]
    except Exception:
        return "کشفِ ساختارِ پنهان + آزمونِ نظریه‌های شناخت"


# ── UnifiedApprovalChannel ─────────────────────────────────────────────────


class UnifiedApprovalChannel(TelegramApprovalChannel):
    """کانالِ تأییدِ یکپارچه: _ops governance + 4d_system brain.

    این کلاس TelegramApprovalChannel موجود را گسترش می‌دهد تا:
      ۱. دستوراتِ مغز (/status_brain /goal /pending /pause /resume /portrait) را هم بشناسد.
      ۲. وضعیتِ unified را در کابین نشان دهد (ادغامِ organism + brain).
      ۳. event emission به هر دو سیستم (brain/events.py + _ops/events.py).
      ۴. callbackهای brain (approve/reject proposal) را هم route کند.

    secret-guard: همان قراردادِ approval_channel — token از env، هرگز hardcode.
    """

    name = "unified"

    def __init__(self, *args, **kwargs):
        # brain bridge — callbacks ثبت‌شده از سمتِ 4d_system
        self._brain_callbacks: dict[str, callable] = {}
        super().__init__(*args, **kwargs)

    def register_brain_callback(self, name: str, fn: callable) -> None:
        """یک callback مغز ثبت کن (مثلاً 'pause' → callable)."""
        self._brain_callbacks[name] = fn

    # ─── event emission به هر دو سیستم ────────────────────────────────────
    @staticmethod
    def _emit_unified(
        event_name: str,
        agent_id: str,
        *,
        status: str = "ok",
        summary: str = "",
        next_action: str = "",
        approval_state: str = "unknown",
    ) -> None:
        """یک رویداد به هر دو event system بفرست (fail-safe هر دو طرف)."""
        # _ops/events.py
        try:
            sys.path.insert(0, str(_HERE.parent))
            import events as ops_events  # noqa: E402
            ops_events.emit(
                event_name,
                agent_id,
                status=status,
                summary=summary,
                next_action=next_action,
                approval_state=approval_state,
            )
        except Exception:
            pass
        # brain/events.py
        try:
            sys.path.insert(0, str(_4D_ROOT / "brain"))
            import events as brain_events  # noqa: E402
            brain_events.emit(
                event_name=event_name,
                agent_id=agent_id,
                status=status,
                summary=summary,
                next_action=next_action,
                approval_state=approval_state,
            )
        except Exception:
            pass

    # ─── override status report: unified ───────────────────────────────────
    def status_report_v2(self) -> str:
        """وضعیتِ یکپارچه: organism + brain در یک نگاه."""
        # بخشِ _ops (organism)
        ops_part = super().status_report_v2()
        # بخشِ brain
        bs = _brain_snapshot()
        state = "⏸ مکث" if bs["paused"] else "🟢 فعال"
        attention = (
            f"⚠️ *{bs['pending']} پیشنهادِ کد* منتظرِ توست"
            if bs["pending"]
            else "✅ چیزی لازم نیست — آروم باش"
        )
        frontier = (
            f" · مرزِ دانش {bs['frontier']}" if bs["frontier"] is not None else ""
        )
        brain_lines = [
            f"\n🧠 <b>مغز (4d_system)</b>",
            f"🎯 {_brain_current_goal()}",
            f"{state} · نسل {bs['generation']}{frontier}",
            f"آخرین فعالیت: {bs['last_tick']} · بودجه {bs.get('budget', '—')}",
            f"{attention}",
        ]
        return ops_part + "\n".join(brain_lines)

    # ─── brain commands ────────────────────────────────────────────────────
    def handle_command(self, text: str) -> str | dict | None:
        """routerِ یکپارچه: brain commands → _ops commands → نادیده."""
        t = (text or "").strip()
        if not t:
            return None

        # === brain commands ===
        if t == "/status_brain" or t == "/brain_status":
            return self._brain_status_text()
        if t == "/goal":
            return self._brain_goal_text()
        if t == "/portrait":
            return self._brain_portrait_text()
        if t == "/pending":
            return self._brain_pending_text()
        if t == "/pause":
            return self._brain_pause()
        if t == "/resume":
            return self._brain_resume()

        # === unified shortcuts ===
        if t == "/unified" or t == "/u":
            return {
                "text": self.status_report_v2(),
                "reply_markup": self.MENU_KEYBOARD,
            }

        # بقیه را به _ops بسپار
        return super().handle_command(t)

    # ─── brain message builders ────────────────────────────────────────────
    def _brain_status_text(self) -> str:
        s = _brain_snapshot()
        state = "⏸ مکث" if s["paused"] else "🟢 فعال"
        attention = (
            f"⚠️ *{s['pending']} پیشنهادِ کد* منتظرِ توست"
            if s["pending"]
            else "✅ چیزی لازم نیست"
        )
        frontier = f" · مرزِ دانش {s['frontier']}" if s["frontier"] is not None else ""
        return (
            f"🌌 ایده‌یاب (4d_system)\n"
            f"🎯 {_brain_current_goal()}\n\n"
            f"{state} · نسل {s['generation']}{frontier}\n"
            f"آخرین فعالیت: {s['last_tick']} · بودجه {s.get('budget', '—')}\n\n"
            f"{attention}"
        )

    def _brain_goal_text(self) -> str:
        try:
            sys.path.insert(0, str(_4D_ROOT / "brain"))
            import research_agenda as ra  # noqa: E402
            mission = (ra.MISSION_FA or "")[:220]
        except Exception:
            mission = "بسترِ آزمونِ نظریه‌های شناخت + کشفِ بُعدِ پنهان."
        return (
            f"🌌 ایده‌یاب (4d_system)\n\n"
            f"🎯 *چرا این پروژه؟*\n{mission}\n\n"
            f"📍 هدفِ الان: {_brain_current_goal()}\n\n"
            f"_وقتی گم شدی، همین‌جا رو بخون. یه قدم کافیه._"
        )

    def _brain_portrait_text(self) -> str:
        try:
            sys.path.insert(0, str(_4D_ROOT / "brain"))
            import self_growth  # noqa: E402
            caps = self_growth.learned_capabilities(5)
            focus = self_growth.current_focus(len(caps))
        except Exception:
            return "🌌 ایده‌یاب (4d_system)\n\n🪞 خودنگاره در دسترس نیست."
        lines = [
            "🌌 ایده‌یاب (4d_system)",
            "",
            "🪞 *خودنگاره* (صادقانه: خودمدل، نه آگاهی)",
            "",
            f"🎯 کانونِ الان: {focus.get('goal', '—')}",
        ]
        if focus.get("limitation"):
            lines.append(f"🧩 روی محدودیت: {focus['limitation'][:60]}")
        lines.append("\n📚 *تازه چه آموختم* (با تأییدِ تو):")
        if caps:
            for c in caps:
                lines.append(
                    f"• `{c.get('target', '')}` → {(c.get('goal') or '')[:40]}"
                )
        else:
            lines.append("• هنوز قابلیتی با تأییدِ تو آموخته نشده")
        return "\n".join(lines)

    def _brain_pending_text(self) -> str | dict:
        try:
            sys.path.insert(0, str(_4D_ROOT / "brain"))
            import self_code  # noqa: E402
            proposals = self_code.list_pending()
        except Exception:
            proposals = []
        if not proposals:
            return (
                "🌌 ایده‌یاب (4d_system)\n\n"
                "✅ هیچ پیشنهادِ کدی منتظرِ تأیید نیست. آروم باش."
            )
        lines = [
            "🌌 ایده‌یاب (4d_system)",
            "",
            f"🧩 *{len(proposals)} پیشنهادِ کد* (هرکدوم آزمونش سبز شده):",
            "",
        ]
        rows = []
        for p in proposals[:5]:
            lines.append(
                f"• `{p.get('target', '?')}` — "
                f"{(p.get('rationale', '') or '')[:60]}"
            )
            pid = p["id"]
            rows.append(
                [
                    {
                        "text": f"✅ {p.get('target', '?').split('/')[-1]}",
                        "callback_data": f"brain:approve:{pid}",
                    },
                    {"text": "❌", "callback_data": f"brain:reject:{pid}"},
                ]
            )
        lines.append("\nبرای هرکدوم دکمهٔ تأیید/رد پایینه 👇")
        rows.append(
            [{"text": "📋 وضعیت", "callback_data": "menu:status"}]
        )
        return {
            "text": "\n".join(lines),
            "reply_markup": {"inline_keyboard": rows},
        }

    def _brain_pause(self) -> str:
        try:
            cb = self._brain_callbacks.get("pause")
            if cb:
                cb(True)
            else:
                # fallback: فایلِ flag
                _PAUSE_FILE.parent.mkdir(parents=True, exist_ok=True)
                _PAUSE_FILE.write_text("paused", encoding="utf-8")
        except Exception as e:
            logger.warning("brain pause failed: %s", e)
            return f"⚠️ مکث نشد: {e}"
        self._emit_unified(
            "system.heartbeat",
            "telegram_unified",
            status="ok",
            summary="brain paused by owner",
        )
        return "⏸ مغز مکث شد. هر وقت خواستی /resume بزن."

    def _brain_resume(self) -> str:
        try:
            cb = self._brain_callbacks.get("resume")
            if cb:
                cb(False)
            else:
                if _PAUSE_FILE.exists():
                    _PAUSE_FILE.unlink()
        except Exception as e:
            logger.warning("brain resume failed: %s", e)
            return f"⚠️ ادامه نشد: {e}"
        self._emit_unified(
            "system.heartbeat",
            "telegram_unified",
            status="ok",
            summary="brain resumed by owner",
        )
        return "▶️ مغز ادامه داد. 🟢"

    # ─── callback router override ──────────────────────────────────────────
    def dispatch_callback(self, data: str) -> str | dict:
        """routerِ یکپارچهٔ callback: brain proposals → _ops approvals → menu."""
        parts = str(data or "").split(":")

        # === brain callbacks ===
        if len(parts) == 3 and parts[0] == "brain":
            verb, pid = parts[1], parts[2]
            return self._dispatch_brain_callback(verb, pid)

        # === unified home shortcuts ===
        if parts[0] == "unified":
            return self._dispatch_unified(parts)

        # بقیه را به _ops بسپار
        return super().dispatch_callback(data)

    def _dispatch_brain_callback(self, verb: str, pid: str) -> str | dict:
        """تأیید/ردِ پیشنهادِ کدِ مغز (self_code)."""
        try:
            sys.path.insert(0, str(_4D_ROOT / "brain"))
            import self_code  # noqa: E402
        except Exception as e:
            logger.error("cannot import self_code: %s", e)
            return "❌ مغز در دسترس نیست."

        if verb == "approve":
            res = self_code.approve(pid)
            ok = res.get("ok")
            self._emit_unified(
                "approval.required",
                "telegram_unified",
                status=("ok" if ok else "error"),
                summary=f"brain proposal {pid} approved={ok}",
                approval_state=("approved" if ok else "denied"),
            )
            props = self_code.list_pending()
            if ok:
                return (
                    "✅ *اعمال شد!* " + res.get("reason", "")
                    + "\n\n"
                    + self._build_pending_summary(props)
                )
            return (
                "❌ نشد: " + res.get("reason", "") + "\n\n" + self._build_pending_summary(props)
            )

        if verb == "reject":
            self_code.reject(pid)
            self._emit_unified(
                "approval.required",
                "telegram_unified",
                status="ok",
                summary=f"brain proposal {pid} rejected",
                approval_state="denied",
            )
            props = self_code.list_pending()
            return "❌ رد شد.\n\n" + self._build_pending_summary(props)

        return "نادیده"

    def _build_pending_summary(self, proposals: list[dict]) -> str:
        if not proposals:
            return "✅ هیچ پیشنهادِ کدی منتظرِ تأیید نیست."
        lines = [f"🧩 *{len(proposals)} پیشنهادِ کد*:", ""]
        for p in proposals[:5]:
            lines.append(
                f"• `{p.get('target', '?')}` — "
                f"{(p.get('rationale', '') or '')[:60]}"
            )
        return "\n".join(lines)

    def _dispatch_unified(self, parts: list[str]) -> str | dict:
        """میان‌برهای unified (مثلاً unified:status, unified:home)."""
        if len(parts) < 2:
            return "نادیده"
        sub = parts[1]
        if sub == "status":
            return {"text": self.status_report_v2(), "reply_markup": self.MENU_KEYBOARD}
        if sub == "home":
            return self._simple_home()
        return "نادیده"

    # ─── override simple home: include brain decisions ─────────────────────
    def _gather_decisions(self) -> list[dict]:
        """همهٔ تصمیماتِ نیازمندِ مالک: _ops + brain."""
        # اول _ops
        out = super()._gather_decisions()
        # بعد brain proposals
        try:
            sys.path.insert(0, str(_4D_ROOT / "brain"))
            import self_code  # noqa: E402
            for p in self_code.list_pending()[:3]:
                pid = p["id"]
                summ = str(p.get("rationale", "") or "").strip()[:50]
                q = f"🧩 پیشنهادِ کد: {summ}... — تأیید کنم؟"
                out.append(
                    {
                        "q": q,
                        "yes": f"brain:approve:{pid}",
                        "no": f"brain:reject:{pid}",
                    }
                )
        except Exception:
            pass
        return out[:5]


# ─── factory: ساختِ کانالِ یکپارچه از env ──────────────────────────────────

def build_unified_channel(
    token: str | None = None,
    owner_chat_id: int | None = None,
    state_dir=None,
    gate=None,
    ledger=None,
    leg=None,
    readmodel=None,
) -> UnifiedApprovalChannel:
    """کارخانهٔ کانالِ یکپارچه — پارامترهای اختیاری از env می‌خواند."""
    return UnifiedApprovalChannel(
        token=token,
        owner_chat_id=owner_chat_id,
        state_dir=state_dir,
        gate=gate,
        ledger=ledger,
        leg=leg,
        readmodel=readmodel,
    )


# ─── main (تستِ مستقل) ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    ch = build_unified_channel()
    if not ch.wired:
        print(" unified channel not wired — check TELEGRAM_BOT_TOKEN and TELEGRAM_OWNER_CHAT_ID")
        sys.exit(1)
    print(f"🐙 Unified ApprovalChannel ready: {ch!r}")
    # یک پالسِ تست
    ch.send_text("🐙 <b>Unified ApprovalChannel</b> online.")
    ch.run_forever()
