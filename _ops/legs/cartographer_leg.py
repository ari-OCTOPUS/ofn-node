#!/usr/bin/env python3
"""cartographer_leg.py — Phase 4 · L-3: پای نقشه‌بردارِ معماری (read-only، propose-only).

آروم آروم / OLP-1 · Increment 3 (code leg، اسکلت). قرارداد: `05 - Agents/vault-cartographer.manifest.yaml`.

نقشِ کمینهٔ این پا در ارگانیسم = **سنتینلِ کهنگیِ نقشه** (drift-pulse): چند anchor را
می‌خواند، اگر نقشهٔ master نسبت به repo کهنه بود یک *پیشنهادِ refresh* (propose-only) می‌دهد
و یک ردِ content-free در Anchor Ledger می‌گذارد. نقشهٔ کاملِ کلِ vault کارِ subagentِ
on-demand (`.claude/agents/vault-cartographer.md`) است، نه این پا (حفظِ IsolationModel).

سخت‌گیری‌ها (وارثِ Leg):
  * propose-only: هیچ متدِ send/publish/pay/trade (ساختاری، در Leg نیست).
  * read-only floor: هیچ Write/commit/move/delete؛ خروجی فقط Proposal + ledger event.
  * صفر جهش، صفر اکشنِ خارجی، صفر spend (budget_aud=0، organ در budgets نیست → incubating).
  * صفر echo از secret/کلید/seed یا هویتِ Project-F (ledger هم _BANNED_ECHO را scrub می‌کند).

inert-until-wired: این فایل تا وقتی `make_cartographer_leg()` (گام ۴) در wiring نیاید،
توسط organism اجرا نمی‌شود. تست‌ها آن را مستقیم می‌سازند. rollback = حذفِ همین فایل + تستش.
additive · $0 offline · stdlib-only · fail-soft.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from leg import Leg, Proposal, TaskPacket          # noqa: E402

# anchorهای پایدارِ read-allowlist (isolation: چند نوت، نه کلِ vault — نه wildcard).
CARTO_ANCHORS = (
    "05 - Agents/AGENT_REGISTRY.md",
    "05 - Agents/Vault Cartographer.md",
    "05 - Agents/Vault-Cartographer-LIMB.md",
    "04 - Architect System/architect/ARCHITECT_CHARTER.md",
    "01 - Dashboard/HANDOFF.md",
    "ROTATION_CHECKLIST.md",
    "06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-09.md",
)
_STALE_DAYS_DEFAULT = 14
# event_names طبقِ قراردادِ ledger (manifest §ledger)
_EV_STARTED, _EV_DONE, _EV_FAILED = "task.started", "task.completed", "task.failed"


def default_packet() -> TaskPacket:
    """TaskPacket استانداردِ پای نقشه‌بردار — secrets خالی، spawn=0، بدونِ wildcard، بودجهٔ صفر."""
    return TaskPacket(
        leg_id="vault-cartographer",
        organ="CARTOGRAPHER",
        read_allowlist=CARTO_ANCHORS,
        tools=("status_snapshot", "map_staleness_check", "propose_refresh"),
        budget_aud=0.0,          # $0 — read-only، هرگز reserve نمی‌کند
        spawn=0,
        secrets=(),
    )


def _parse_iso(ts):
    """ISO8601 → datetime آگاه (UTC). None اگر رشته نبود/غیرقابل‌parse. naive = UTC."""
    if not isinstance(ts, str):
        return None
    s = ts.strip()
    if not s:
        return None
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    dt = None
    for cand in (s, s + "T00:00:00"):
        try:
            dt = datetime.fromisoformat(cand)
            break
        except ValueError:
            dt = None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class CartographerLeg(Leg):
    """پای نقشه‌بردار — سنتینلِ کهنگیِ نقشه، propose-only، read-only. هرگز خودش نمی‌نویسد/نمی‌فرستد."""

    def __init__(self, packet: TaskPacket | None = None,
                 organ_table: dict | None = None,
                 emitter=None):
        super().__init__(packet or default_packet(), organ_table=organ_table)
        # emitter تزریق‌پذیر (تست بدونِ نوشتن در ledgerِ واقعی)؛ None → events.emit واقعی (lazy).
        self._emitter = emitter

    # ─── Anchor-Ledger (content-free، fail-soft، injectable) ─────────────────────
    def _emit(self, event_name: str, summary: str, *, status: str = "ok",
              approval_state: str = "none", next_action: str = "",
              trace_id: str = "") -> dict | None:
        """یک ردِ ساختاریافته در Anchor Ledger. هرگز crash نمی‌کند. content-free.
        summary/next_action فقط عبارتِ عمومی + citation؛ scrubِ _BANNED_ECHO در events.py backstop است."""
        fn = self._emitter
        if fn is None:
            try:
                import events                            # noqa: WPS433 — _ops/events.py
                fn = events.emit
            except Exception:                            # noqa: BLE001
                return None
        try:
            return fn(event_name, "vault-cartographer", status=status,
                      summary=str(summary or "")[:180], next_action=str(next_action or "")[:120],
                      approval_state=approval_state, trace_id=str(trace_id or "")[:40],
                      enrich=True)                        # control-plane از registry (fail-soft)
        except Exception:                                # noqa: BLE001
            return None

    # ─── status (read-only) ──────────────────────────────────────────────────────
    def status_snapshot(self) -> dict:
        """snapshotِ فقط‌خواندنی برای master/organism. صفر جهش، صفر بیرونی."""
        return {
            "leg_id": self.packet.leg_id,
            "organ": self.packet.organ,
            "money_link": self.money_link,               # incubating تا organ در budgets
            "autonomy_floor": "read-only",
            "autonomy_ceiling": "propose-only",
            "read_only": True,
            "mutates": False,
            "external_action": False,
            "spend_aud": 0,
            "execution_state": "ZERO mutation · ZERO outward · map/report/propose only",
            "tools": list(self.packet.tools),
            "proposals_emitted": len(self.proposals),
        }

    # ─── staleness (pure، offline، تزریقِ _now برای تستِ قطعی) ───────────────────
    def map_staleness_check(self, map_updated_iso, max_age_days: int = _STALE_DAYS_DEFAULT,
                            _now=None) -> dict:
        """آیا نقشهٔ master کهنه است؟ pure. تاریخِ نامعلوم/غیرقابل‌parse → stale (fail-closed:
        نمی‌توان تازگی را تأیید کرد → refresh پیشنهاد شود)."""
        dt = _parse_iso(map_updated_iso)
        now = _now if _now is not None else datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        if dt is None:
            return {"stale": True, "age_days": None,
                    "reason": "تاریخِ نقشه نامعلوم/غیرقابل‌parse — refresh پیشنهاد می‌شود (fail-closed)."}
        age = (now - dt).days
        if age < 0:
            return {"stale": False, "age_days": age, "reason": "تاریخِ نقشه در آینده — نادیده (تازه فرض)."}
        stale = age > max_age_days
        return {"stale": stale, "age_days": age,
                "reason": (f"کهنه: {age} روز > سقفِ {max_age_days}." if stale
                           else f"تازه: {age} روز ≤ {max_age_days}.")}

    # ─── drift-pulse assessment (pure؛ سیگنالِ propose-only، بدونِ I/O) ──────────
    def assess_map(self, map_updated_iso, drift_count: int = 0,
                   max_age_days: int = _STALE_DAYS_DEFAULT, _now=None) -> dict:
        """ارزیابیِ drift-pulse: کهنگیِ نقشه (age) + دریفتِ کد (فایل‌های _ops تغییرکرده
        از تاریخِ نقشه). pure — beat مقادیرِ واقعی را تزریق می‌کند. صفر I/O، صفر mutate.

        refresh_recommended = نقشه کهنه است، یا دریفتِ کد قابل‌توجه (>=۵ فایل) — حتی اگر
        تاریخِ نقشه تازه باشد (نقشه‌ای که ۳ روزه ولی ۴۰ فایل بعدش عوض شده = محتواً کهنه).
        """
        st = self.map_staleness_check(map_updated_iso, max_age_days=max_age_days, _now=_now)
        try:
            drift = max(0, int(drift_count))
        except (TypeError, ValueError):
            drift = 0
        stale = bool(st.get("stale"))
        age = st.get("age_days")
        refresh = stale or drift >= 5
        if stale or drift >= 5:
            mood = "🔴"
        elif drift > 0 or (age is not None and age > max(1, max_age_days // 2)):
            mood = "🟡"
        else:
            mood = "🟢"
        return {
            "map_updated": map_updated_iso if isinstance(map_updated_iso, str) else None,
            "age_days": age,
            "stale": stale,
            "drift_files": drift,
            "refresh_recommended": refresh,
            "mood": mood,
            "reason": st.get("reason"),
        }

    # ─── propose refresh (propose-only + ledger) ─────────────────────────────────
    def propose_refresh(self, reason: str, map_updated_iso=None,
                        trace_id: str = "", hlc: tuple = (0, 0)) -> Proposal:
        """پیشنهادِ بازتولیدِ نقشهٔ master. فقط Proposal (publish=False) + یک ردِ content-free در ledger.
        اکشنِ واقعیِ نقشه‌کشی = subagentِ on-demand؛ نوشتنِ نقشه = human/master (این پا فقط پیشنهاد)."""
        st = self.map_staleness_check(map_updated_iso) if map_updated_iso is not None else None
        payload = {
            "draft_only": True,
            "publish": False,
            "recommendation": "regenerate MASTER-ARCHITECTURE map from real repo (subagent, on-demand)",
            "reason": str(reason or "")[:200],
            "staleness": st,
            "authority": "propose-only — map write is human/master (leg never writes it)",
            "no_mutation": True,
            "external_action": False,
        }
        p = self.emit_proposal("cartography_refresh", payload, hlc=hlc)
        # ردِ ledger: پیشنهاد ثبت شد (نه اکشنِ گیت‌دار → approval_state=none).
        self._emit(_EV_DONE, "cartography refresh proposed (map staleness sentinel)",
                   approval_state="none",
                   next_action="owner/master: run cartographer subagent to regenerate map",
                   trace_id=trace_id)
        return p

    # ─── tick (فقط status؛ بدونِ side-effect؛ توسطِ organism در گام ۴ صدا زده می‌شود) ─
    def tick(self) -> dict:
        """یک beatِ سبک: فقط status برمی‌گرداند. خودش چیزی emit/mutate نمی‌کند."""
        s = self.status_snapshot()
        return {"ok": True, **s}
