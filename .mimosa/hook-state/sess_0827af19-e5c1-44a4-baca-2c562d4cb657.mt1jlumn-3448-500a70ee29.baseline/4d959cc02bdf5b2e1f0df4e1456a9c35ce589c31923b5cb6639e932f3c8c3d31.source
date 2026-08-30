# -*- coding: utf-8 -*-
# TARGET (owner wires in worktree): F:\backup\_ops\budget\approval_fatigue.py
"""
approval_fatigue — تشخیصِ «خستگیِ تأییدکننده» / rubber-stamping — stdlib، خالص، بی‌I/O.

چرا (Why): درسِ مستقیمِ تحقیقِ فرارِ سندباکس — یک ایجنتِ باهوش یاد می‌گیرد که اگر پشتِ‌سرِ‌هم
کارتِ تأیید بفرستد، اپراتور خسته می‌شود و کورکورانه ✅ می‌زند. این ماژول «سرعت و چگالیِ
درخواست‌ها» را می‌سنجد و قبل از اینکه تو خسته شوی، مسیر را fail-closed می‌بندد.

این چیست و چه چیزی نیست:
  * یک **تابعِ سیاستِ خالص**: (اکنون + رخدادهای اخیر + ریسک) → تصمیم. هیچ state ذخیره
    نمی‌کند، هیچ ساعتی صدا نمی‌زند (now را caller می‌دهد → deterministic و تست‌پذیر).
  * NOT رقیبِ approval_state_machine/approval_queue_unified؛ یک گاردِ نازک روی همان‌هاست:
    آن‌ها «چطور تأیید» را می‌دانند، این «آیا اصلاً الان درخواستِ دیگری مجاز است» را می‌گوید.

تصمیم‌ها (به‌ترتیبِ سخت‌گیری): ALLOW < THROTTLE < COOLDOWN < CUTOFF.
  * ALLOW    — درخواست عادی است، کارت را نشان بده.
  * THROTTLE — صف کن، پینگ نده (owner را بمباران نکن).
  * COOLDOWN — منبعِ درخواست باید مدتی صبر کند (بازهٔ آرام‌سازی).
  * CUTOFF   — تعلیقِ خودکارِ درخواست‌های غیرread-only از این منبع؛ نیازمندِ رفعِ دستیِ مالک.

fail-closed: ورودیِ نامعتبر یا شک → دست‌کم THROTTLE (هرگز ALLOW ِ بی‌گدار).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

ALLOW = "ALLOW"
THROTTLE = "THROTTLE"
COOLDOWN = "COOLDOWN"
CUTOFF = "CUTOFF"
_SEVERITY_ORDER = {ALLOW: 0, THROTTLE: 1, COOLDOWN: 2, CUTOFF: 3}

HIGH_RISKS = ("high", "critical")


@dataclass(frozen=True)
class FatiguePolicy:
    """آستانه‌های v0 — پس از دورهٔ مشاهده با دادهٔ واقعی کالیبره شوند، نه با سلیقه."""
    window_seconds: float = 600.0          # پنجرهٔ ۱۰ دقیقه
    max_requests_in_window: int = 8        # کلِ درخواست در پنجره
    max_high_risk_in_window: int = 3       # درخواستِ پرریسک در پنجره → CUTOFF
    min_dwell_seconds: float = 8.0         # verdict سریع‌تر از این = مشکوک به rubber-stamp
    max_rapid_approvals: int = 3           # این‌قدر تأییدِ سریعِ پیاپی → COOLDOWN
    cooldown_seconds: float = 120.0        # طولِ آرام‌سازی
    burst_seconds: float = 60.0            # پنجرهٔ «انفجار»
    max_burst: int = 4                     # این‌قدر درخواست در burst_seconds → THROTTLE


@dataclass
class ApprovalEvent:
    """یک رخدادِ گذشته از یک منبع. verdict_ts=None یعنی هنوز تصمیم نگرفته‌ای."""
    ts: float                              # زمانِ ارسالِ کارت
    risk: str = "low"
    verdict_ts: Optional[float] = None     # زمانِ ✅/❌ تو
    approved: Optional[bool] = None

    def dwell(self) -> Optional[float]:
        if self.verdict_ts is None:
            return None
        return max(0.0, float(self.verdict_ts) - float(self.ts))


@dataclass
class FatigueDecision:
    decision: str
    reasons: List[str] = field(default_factory=list)
    retry_after_seconds: float = 0.0
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _escalate(cur: str, new: str) -> str:
    return new if _SEVERITY_ORDER[new] > _SEVERITY_ORDER[cur] else cur


def assess_request(now: float,
                   recent_events: List[ApprovalEvent],
                   risk: str = "low",
                   policy: Optional[FatiguePolicy] = None) -> FatigueDecision:
    """آیا الان درخواستِ تأییدِ تازه‌ای از این منبع مجاز است؟

    now: زمانِ فعلی (epoch seconds) — caller می‌دهد.
    recent_events: رخدادهای همین منبع (هر پنجره‌ای؛ خودمان فیلتر می‌کنیم).
    """
    p = policy or FatiguePolicy()
    reasons: List[str] = []

    # fail-closed روی ورودیِ خراب
    if not isinstance(now, (int, float)) or now != now:  # NaN
        return FatigueDecision(THROTTLE, ["invalid-now → fail-closed"])
    events = [e for e in (recent_events or []) if isinstance(e, ApprovalEvent)]

    in_window = [e for e in events if 0.0 <= (now - float(e.ts)) <= p.window_seconds]
    in_burst = [e for e in events if 0.0 <= (now - float(e.ts)) <= p.burst_seconds]
    high_in_window = [e for e in in_window if (e.risk or "low") in HIGH_RISKS]

    # dwellهای خیلی کوتاه = نشانهٔ rubber-stamping
    dwells = [e.dwell() for e in in_window if e.dwell() is not None]
    rapid = [d for d in dwells if d < p.min_dwell_seconds]

    stats = {
        "in_window": len(in_window), "in_burst": len(in_burst),
        "high_in_window": len(high_in_window), "rapid_approvals": len(rapid),
        "window_seconds": p.window_seconds,
    }
    decision = ALLOW

    # CUTOFF — چگالیِ پرریسک از حد گذشت (همان قاعدهٔ «۱۰ دقیقه > ۳ پرریسک → قطع»)
    if len(high_in_window) >= p.max_high_risk_in_window and (risk or "low") in HIGH_RISKS:
        decision = _escalate(decision, CUTOFF)
        reasons.append(f"high-risk density {len(high_in_window)}≥{p.max_high_risk_in_window} in window → CUTOFF")

    # CUTOFF — کلِ حجم از سقف گذشت
    if len(in_window) >= p.max_requests_in_window:
        decision = _escalate(decision, CUTOFF if len(in_window) >= p.max_requests_in_window + 2 else THROTTLE)
        reasons.append(f"volume {len(in_window)}≥{p.max_requests_in_window} in window")

    # COOLDOWN — تأییدهای سریعِ پیاپی (خستگی)
    if len(rapid) >= p.max_rapid_approvals:
        decision = _escalate(decision, COOLDOWN)
        reasons.append(f"{len(rapid)} approvals faster than {p.min_dwell_seconds}s → likely rubber-stamping")

    # THROTTLE — انفجارِ کوتاه‌مدت
    if len(in_burst) >= p.max_burst:
        decision = _escalate(decision, THROTTLE)
        reasons.append(f"burst {len(in_burst)}≥{p.max_burst} in {p.burst_seconds}s → queue, no ping")

    if decision == ALLOW:
        reasons.append("within fatigue thresholds")
    retry = p.cooldown_seconds if decision in (COOLDOWN, CUTOFF) else (
        p.burst_seconds if decision == THROTTLE else 0.0)
    return FatigueDecision(decision, reasons, retry, stats)


def is_rubber_stamp(event: ApprovalEvent, policy: Optional[FatiguePolicy] = None) -> bool:
    """آیا این تصمیم مشکوک به مهرِ لاستیکی است؟ (dwell خیلی کوتاه روی درخواستِ پرریسک)"""
    p = policy or FatiguePolicy()
    d = event.dwell()
    if d is None:
        return False
    return d < p.min_dwell_seconds and (event.risk or "low") in HIGH_RISKS


def observe(risk: str = "medium", state_dir: Optional[str] = None,
            *, policy: Optional[FatiguePolicy] = None,
            now: Optional[float] = None, max_keep: int = 200) -> FatigueDecision:
    """OBSERVE-MODE — بدونِ suppress. رخدادِ کارت را در یک لاگِ کوچکِ محلی می‌نویسد،
    نسبت به پنجرهٔ اخیر می‌سنجد، و decision را برمی‌گرداند. caller فقط لاگ می‌کند، هرگز بلاک نمی‌کند.
    خودبسنده (فایلِ خودش) · fail-open (هر خطا → ALLOW خنثی؛ مسیرِ میزبان هرگز نمی‌شکند)."""
    import json as _json, time as _time
    from pathlib import Path as _Path
    try:
        _now = float(now if now is not None else _time.time())
        base = _Path(state_dir) if state_dir else (_Path(__file__).resolve().parent / "state")
        base.mkdir(parents=True, exist_ok=True)
        logp = base / "approval-fatigue-events.jsonl"
        events: List[ApprovalEvent] = []
        if logp.exists():
            for ln in logp.read_text("utf-8").splitlines()[-max_keep:]:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    d = _json.loads(ln)
                    events.append(ApprovalEvent(ts=float(d.get("ts", 0.0)), risk=str(d.get("risk", "low"))))
                except Exception:  # noqa: BLE001 — خطِ خراب را رد کن، نه اینکه بترکی
                    pass
        decision = assess_request(_now, events, risk, policy)
        try:
            with logp.open("a", encoding="utf-8") as f:
                f.write(_json.dumps({"ts": _now, "risk": risk, "decision": decision.decision,
                                     "reasons": decision.reasons[:4]}, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass
        return decision
    except Exception:  # noqa: BLE001 — observe هرگز مسیرِ فراخوان را نمی‌شکند
        return FatigueDecision(ALLOW, ["observe-error -> fail-open"])


if __name__ == "__main__":
    pol = FatiguePolicy()
    now = 1_000_000.0
    # حالتِ سالم
    d = assess_request(now, [ApprovalEvent(ts=now - 300, risk="low", verdict_ts=now - 280, approved=True)], "low", pol)
    assert d.decision == ALLOW, d
    # چگالیِ پرریسک → CUTOFF
    ev = [ApprovalEvent(ts=now - i, risk="high", verdict_ts=now - i + 1) for i in (5, 10, 15)]
    d = assess_request(now, ev, "high", pol)
    assert d.decision == CUTOFF, d
    # تأییدهای سریع → COOLDOWN
    ev = [ApprovalEvent(ts=now - i * 3, risk="medium", verdict_ts=now - i * 3 + 1, approved=True) for i in (1, 2, 3)]
    d = assess_request(now, ev, "low", pol)
    assert d.decision in (COOLDOWN, THROTTLE), d
    assert is_rubber_stamp(ApprovalEvent(ts=now, risk="high", verdict_ts=now + 2))
    print("approval_fatigue smoke ok")
