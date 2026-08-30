#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dual_brain.py — حاکمیتِ دوگانه ۵۰/۵۰ (فاز ۶ دستورالعمل ۲۰۲۶-۰۸-۱۶، D1/D2/D3).

دو مغز: 4d_system (تحقیق/تحلیل — ایده‌یاب) + NBB-CP (عملیات/فرمانداری).
  · وتوی متقابل (D2): وتوی هر مغز → توقفِ فوری + رأیِ مالک (fail-closed).
  · consensus halt (D3): ارگانیسم فقط با موافقتِ هر دو مغز halt می‌شود.
  · دامنه‌ها بر اساسِ نوعِ تصمیم (نه مالکیتِ پا) — سندِ DUAL-BRAIN-CONSTITUTION §۲.

چرا مسیرِ مالک از صفِ مستقیم نمی‌گذرد
──────────────────────────────────────
منشورِ MCP (CONSTITUTION §۲): تنها نویسندهٔ `_octopus/queue/pending/` ابزارِ
`propose_action` است — این ماژول هم به همان صف دست نمی‌زند. مسیرِ OWNER_DECISION:
ثبت در spine (canonical decision-recorded، دامنهٔ governance) + رویدادِ
approval.required در events.jsonl + اعلانِ مالک از مسیرِ alert→event_bridge
(واژگانِ critical شامل «denied» است). رأیِ مالک از همان کانالِ تأییدِ موجود
برمی‌گردد؛ این‌جا فقط درِ fail-closed را نگه می‌داریم.

supervisor.py عمداً دست‌نخورده ماند: منشورِ خودش نوشتنش را به فضای‌نامِ
انحصاریِ snapshot محدود کرده و تستِ test_control_plane پاس می‌کند (واقعیتِ
فایل بر طرحِ دستورالعمل برنده است — AGENT-INVENTORY §۶).

توابعِ محض همیشه در دسترس‌اند؛ side-effectها (spine/alert/events) پشتِ
OCTOPUS_WIRE_DUAL_VETO (W4 — رأیِ tracked، env برنده). total · fail-soft.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "spine"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_DUAL_VETO"
_TRUTHY = ("1", "true", "yes", "on")


class BrainID(str, Enum):
    FOURD = "fourd_system"
    NBB = "nbb_cp"


class VetoResult(str, Enum):
    APPROVED = "approved"
    VETOED = "vetoed"
    PENDING = "pending"              # منتظرِ رایِ مغزِ دیگر
    OWNER_DECISION = "owner_decision"  # تعارض/وتو → رأیِ مالک


@dataclass
class DualVeto:
    """رکوردِ یک ارزیابیِ وتوی دوگانه (R8 — trace_id اجباری)."""
    proposal_id: str
    trace_id: str
    fourd_verdict: VetoResult
    nbb_verdict: VetoResult
    final: VetoResult
    owner_notified: bool = False
    domain: str = ""
    ts: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))

    def as_dict(self) -> dict:
        return {"proposal_id": self.proposal_id, "trace_id": self.trace_id,
                "fourd_verdict": self.fourd_verdict.value,
                "nbb_verdict": self.nbb_verdict.value,
                "final": self.final.value, "owner_notified": self.owner_notified,
                "domain": self.domain, "ts": self.ts}


def evaluate_veto(fourd_verdict: VetoResult, nbb_verdict: VetoResult) -> VetoResult:
    """منطقِ وتوی متقابل (D2): هر دو تأیید → تأیید؛ هر وتو → مالک؛ وگرنه منتظر."""
    if fourd_verdict == VetoResult.APPROVED and nbb_verdict == VetoResult.APPROVED:
        return VetoResult.APPROVED
    if fourd_verdict == VetoResult.VETOED or nbb_verdict == VetoResult.VETOED:
        return VetoResult.OWNER_DECISION   # وتو → مالک رأی می‌دهد
    return VetoResult.PENDING


def consensus_halt(fourd_agrees: bool, nbb_agrees: bool) -> bool:
    """halt فقط با موافقتِ هر دو مغز (D3) — هیچ مغزی تنهایی halt نمی‌کند."""
    return bool(fourd_agrees) and bool(nbb_agrees)


# دامنه‌های تصمیم (دسترسی مشترک به پاها — تقسیم بر اساسِ نوع، D7/سند §۲)
DECISION_DOMAINS = {
    "research": BrainID.FOURD,        # hypothesis, analysis
    "analysis": BrainID.FOURD,
    "operations": BrainID.NBB,         # budget, execution
    "budget": BrainID.NBB,
    "safety": None,                    # هر دو (وتوی متقابل)
    "halt": None,                      # consensus (هر دو)
    "architecture": None,              # هر دو + مالک
}


def domain_brain(domain: str) -> "BrainID | None":
    """مغزِ مسئولِ دامنه؛ None = هر دو (وتوی متقابل/consensus). ناشناخته = هر دو
    (محافظه‌کارانه — دامنهٔ جدید بدون رأی، خودش به مالک می‌رود)."""
    return DECISION_DOMAINS.get(str(domain or "").strip().lower(), None)


def enabled() -> bool:
    if FLAG in os.environ:
        return str(os.environ[FLAG]).strip().lower() in _TRUTHY
    try:
        import owner_verdicts as _ov   # noqa: WPS433 — lazy
        return str(_ov.get(FLAG) or "0").strip().lower() in _TRUTHY
    except Exception:  # noqa: BLE001
        return False


def evaluate(proposal_id: str, fourd_verdict: VetoResult, nbb_verdict: VetoResult,
             *, domain: str = "") -> DualVeto:
    """ارزیابیٔ کاملِ یک proposal: منطقِ محض + (پشتِ فلگ) ثبت و اعلان.

    هرگز raise نمی‌کند؛ خروجی DualVeto است. OWNER_DECISION یعنی:
    اقدام متوقف (fail-closed) و منتظرِ رأیِ مالک — این تابع اجرا نمی‌کند،
    فقط درِ veto را نگه می‌دارد (اجرا در action_bridge، فاز ۸e)."""
    pid = str(proposal_id or "")[:64] or f"prop_{uuid.uuid4().hex[:8]}"
    final = evaluate_veto(fourd_verdict, nbb_verdict)
    rec = DualVeto(proposal_id=pid, trace_id=f"veto-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
                   fourd_verdict=fourd_verdict, nbb_verdict=nbb_verdict,
                   final=final, domain=str(domain or "")[:32])
    if final == VetoResult.OWNER_DECISION:
        rec.owner_notified = _notify_owner(rec)
    _record(rec)
    return rec


def _record(rec: DualVeto) -> None:
    """ثبتِ هر نتیجهٔ veto در events.jsonl (همیشه) + spine (پشتِ فلگ‌های خودشان)."""
    try:
        import events as _ev   # noqa: WPS433
        _ev.emit(
            "approval.required" if rec.final == VetoResult.OWNER_DECISION
            else "task.completed",
            "dual_brain", status="ok" if rec.final == VetoResult.APPROVED else "veto",
            summary=f"dual-brain {rec.final.value}: {rec.proposal_id} "
                    f"(4d={rec.fourd_verdict.value} nbb={rec.nbb_verdict.value})",
            next_action="owner vote: ok / no / later" if rec.owner_notified else "",
            trace_id=rec.trace_id, correlation_id=rec.trace_id,
            approval_state="required" if rec.final == VetoResult.OWNER_DECISION
            else ("none" if rec.final == VetoResult.APPROVED else "unknown"))
    except Exception:  # noqa: BLE001
        pass
    try:   # فاز ۶: ثبتِ canonical در spine — پشتِ فلگِ OCTOPUS_WIRE_SPINE خودش
        import spine_adapters as _sa   # noqa: WPS433
        _sa.dual_veto_recorded(
            proposal_id=rec.proposal_id,
            fourd_verdict=rec.fourd_verdict.value, nbb_verdict=rec.nbb_verdict.value,
            final=rec.final.value, correlation_id=rec.trace_id)
    except Exception:  # noqa: BLE001
        pass


def _notify_owner(rec: DualVeto) -> bool:
    """اعلانِ مالک دربارهٔ وتو — فقط پشتِ فلگ (W4). مسیر: alert→event_bridge
    (واژگانِ critical: «denied»). صفر کانالِ جدید، صفر نوشتن در صف."""
    if not enabled():
        return False
    try:
        import opslib   # noqa: WPS433
        opslib.alert([
            f"⚠️ dual-brain VETO — proposal denied pending owner vote: "
            f"{rec.proposal_id} (4d={rec.fourd_verdict.value} · "
            f"nbb={rec.nbb_verdict.value} · domain={rec.domain or '?'}) — "
            f"trace {rec.trace_id}. رأی: ok / no / later"])
        return True
    except Exception:  # noqa: BLE001
        return False


def halt_organism(fourd_agrees: bool, nbb_agrees: bool) -> dict:
    """درخواستِ halt با consensus (D3). هیچ فایلی لمس نمی‌شود — فقط رویداد و
    اعلان؛ خودِ halt از مسیرِ مجازِ مالک (STOP-ORGANISM) می‌آید، نه از مغزها."""
    ok = consensus_halt(fourd_agrees, nbb_agrees)
    out = {"consensus": ok, "fourd_agrees": bool(fourd_agrees),
           "nbb_agrees": bool(nbb_agrees),
           "action": "halt-request-recorded" if ok else "no-halt-single-brain",
           "trace_id": f"halt-{time.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"}
    try:
        import events as _ev   # noqa: WPS433
        _ev.emit("system.heartbeat", "dual_brain", status="ok",
                 summary=f"consensus halt vote: {out['action']}",
                 trace_id=out["trace_id"], correlation_id=out["trace_id"],
                 approval_state="required" if ok else "none")
    except Exception:  # noqa: BLE001
        pass
    return out


if __name__ == "__main__":   # pragma: no cover
    import json
    print(json.dumps(evaluate("demo-1", VetoResult.APPROVED, VetoResult.VETOED,
                              domain="safety").as_dict(), ensure_ascii=False, indent=1))
