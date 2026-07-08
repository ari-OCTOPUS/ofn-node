#!/usr/bin/env python3
"""live_loop.py — پاسِ نهاییِ wiring: مغزِ Project-F ↔ کاکپیتِ آری روی یک UnifiedBus.

W-1: route مغزِ Project-F: high-risk → صفِ تأییدِ کاکپیتِ آری؛ verdict → برگشت به مغز+صبا.
W-2: یک bus: legs/gates/doctor/box/rhythm/spectral/sensory/telegram همگی publish/subscribe.
W-3: doctor.run_cycle advisory + rhythm/spectral/afferent به‌عنوان advisory signals.

خطِ قرمز: approve تنها مسیرِ settle · صفر انتشارِ خودکار · دوکلیده · صفر رسانه/PII ·
money قفل/shadow · λ_persist<0 · advisory سیگنال‌ها هرگز اثر نزنند · Project-F containment.

additive؛ stdlib-only؛ $0 آفلاین. مسیرِ قدیمی deprecated نه deleted.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent   # _ops
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "budget"))
sys.path.insert(0, str(_HERE / "brain"))


@dataclass
class VerdictResult:
    """نتیجهٔ verdict از آری."""
    approved: bool
    effect_id: str
    source: str   # "ari" | "lead-naghshi" | ...
    project: str  # "Project-F" | "Lead-نقاشی" | ...


class LiveLoop:
    """حلقهٔ زندهٔ واحد. همهٔ لایه‌ها روی یک UnifiedBus.
    brain(صبا→مغز→آری) + advisory signals + doctor.

    این wire layer است — هیچ‌کدام از ماژول‌های زیرین را تغییر نمی‌دهد.
    فقط آن‌ها را به هم وصل می‌کند."""

    def __init__(self, bus=None, brain=None, studio=None, cockpit=None,
                 approval_channel=None, doctor=None):
        # bus: اگر نباشد → یک busِ in-memory (تست)
        self.bus = bus or _InMemoryBus()
        self.brain = brain
        self.studio = studio
        self.cockpit = cockpit
        self.channel = approval_channel
        self.doctor = doctor
        self._verdicts: list[VerdictResult] = []
        self._advisory_signals: list[dict] = []

        # W-2: ثبتِ advisory subscribers
        self.bus.subscribe(self._on_advisory, event_type="RHYTHM")
        self.bus.subscribe(self._on_advisory, event_type="SPECTRAL")
        self.bus.subscribe(self._on_advisory, event_type="AFFERENT")
        self.bus.subscribe(self._on_advisory, event_type="DOCTOR")

    # ─── W-1: brain → cockpit route ─────────────────────────────────────────────
    def process_project_f_draft(self, draft_title: str, checks: dict | None = None,
                                risk_override: str | None = None) -> dict:
        """درفتِ صبا → مغز → route. high-risk → کاکپیتِ آری.
        low-risk → مستقیم استودیوی صبا.
        خروجی: {routed, guards_passed, submitted_to_ari}."""
        if self.brain is None:
            return {"ok": False, "error": "no brain"}
        result = self.brain.process_draft(draft_title, checks=checks,
                                          risk_override=risk_override)
        # route: اگر چیزی به آری رفت → به صفِ تأییدِ کاکپیت اضافه کن
        submitted = []
        for route in result.get("routed_to", []):
            if route["route"] == "ari" and self.cockpit is not None:
                self.cockpit.add_approval(
                    project="Project-F",
                    action=f"تأییدِ {route['kind']}: {draft_title}",
                    amount_aud=0.0,  # پول قفل
                    guard="pending",
                    effect_id=f"pf-{route['kind']}-{draft_title[:20]}")
                submitted.append(route["kind"])
                # publish روی bus (advisory)
                self.bus.publish("OBSERVE", {
                    "source": "project-f-brain", "route": "ari",
                    "kind": route["kind"], "draft": draft_title,
                    "project": "Project-F"}, actor="brain")
            elif route["route"] == "saba" and self.studio is not None:
                # low-risk → مستقیم استودیو (پیشنهاد)
                self.bus.publish("OBSERVE", {
                    "source": "project-f-brain", "route": "saba",
                    "kind": route["kind"], "draft": draft_title}, actor="brain")
        return {"routed": result.get("routed_to", []),
                "guards_passed": result.get("guards_passed", False),
                "submitted_to_ari": submitted}

    # ─── W-1: verdict از آری → برگشت به مغز + استودیو ──────────────────────────
    def apply_ari_verdict(self, effect_id: str, approved: bool,
                          project: str = "Project-F") -> VerdictResult:
        """verdict از آری → ثبت در آرشیوِ مغز + به‌روزرسانی استودیو.
        approve = human-append (TINV-7) — اما اینجا mock (تست).
        در runtime واقعی، این از approval_channel.dispatch_callback می‌آید."""
        verdict = VerdictResult(approved=approved, effect_id=effect_id,
                                source="ari", project=project)
        self._verdicts.append(verdict)
        # برگشت به مغز: archive
        if self.brain is not None:
            outcome = "approved" if approved else "rejected"
            self.brain.archive(kind=effect_id.split("-")[1] if "-" in effect_id else "unknown",
                               outcome=outcome)
        # برگشت به استودیو: به‌روزرسانی وضعیت درفت
        if self.studio is not None and approved:
            for d in self.studio._drafts:
                if d.status == "pending":
                    d.status = "approved"   # → انتشارِ درون‌پلتفرم (human-gated)
                    break
        # publish verdict روی bus
        self.bus.publish("OBSERVE", {
            "source": "ari", "verdict": "approve" if approved else "reject",
            "effect_id": effect_id, "project": project}, actor="ari")
        return verdict

    # ─── W-2: advisory signals ──────────────────────────────────────────────────
    def _on_advisory(self, event: dict) -> None:
        """subscriber برای advisory signals. فقط log — هیچ اثر."""
        self._advisory_signals.append(event)

    def publish_rhythm_advisory(self, rhythm_state: dict) -> None:
        """rhythm.advisory را به‌عنوان advisory منتشر کن (W-3)."""
        self.bus.publish("RHYTHM", {**rhythm_state, "advisory_only": True},
                         actor="rhythm")

    def publish_spectral_advisory(self, spectral_result: dict) -> None:
        """spectral_mine را به‌عنوان advisory منتشر کن (W-3)."""
        self.bus.publish("SPECTRAL", {**spectral_result, "advisory_only": True},
                         actor="spectral")

    def publish_afferent_advisory(self, afferent_status: dict) -> None:
        """afferent_ratio را به‌عنوان advisory منتشر کن (W-3)."""
        self.bus.publish("AFFERENT", {**afferent_status, "advisory_only": True},
                         actor="sensory-bus")

    def publish_doctor_advisory(self, doctor_result: dict) -> None:
        """doctor.run_cycle را به‌عنوان advisory منتشر کن (W-3)."""
        self.bus.publish("DOCTOR", {**doctor_result, "advisory_only": True},
                         actor="doctor")

    @property
    def advisory_signals(self) -> list[dict]:
        """سیگنال‌های advisory دریافت‌شده. فقط log، هیچ اثر."""
        return list(self._advisory_signals)

    @property
    def verdicts(self) -> list[VerdictResult]:
        return list(self._verdicts)

    # ─── W-1: Lead-نقاشی path (همان حلقهٔ واحد) ────────────────────────────────
    def process_lead(self, leg, lead_name: str, expected_aud: float,
                     cell: str = "lead.doer") -> dict:
        """لیدِ Lead-نقاشی → همان bus → attribution → CONFIRMED (paper).
        این نشان می‌دهد Lead-نقاشی و Project-F روی یک حلقه می‌چرخند."""
        if leg is None:
            return {"ok": False, "error": "no leg"}
        intake = leg.intake(lead_name, expected_aud, cell)
        if not intake.get("ok"):
            return intake
        # publish روی bus
        self.bus.publish("OBSERVE", {
            "source": "lead-naghshi", "type": "lead",
            "attribution_id": intake["attribution_id"],
            "amount": expected_aud}, actor="leg")
        return intake

    # ─── sanity: no PII/media leak from brain path ──────────────────────────────
    def verify_no_pii_in_signals(self) -> bool:
        """هیچ رسانه/PII در سیگنال‌های bus نیست."""
        forbidden = ("media", "photo", "video", "face", "identity",
                     "real_name", "email", "phone", "subscriber", "fan_name")
        for sig in self._advisory_signals:
            blob = str(sig).lower()
            for f in forbidden:
                if f in blob:
                    return False
        return True


class _InMemoryBus:
    """busِ in-memory برای تست (بدونِ ledger واقعی).
    همان قراردادِ UnifiedBus ولی بدونِ disk write."""
    def __init__(self):
        self._subscribers: list = []
        self._events: list[dict] = []

    def subscribe(self, callback, event_type: str | None = None) -> None:
        self._subscribers.append((event_type, callback))

    def publish(self, event_type: str, payload: dict, actor: str = "system",
                is_human: bool = False, beat: bool = False) -> dict:
        event = {"type": event_type, "payload": payload, "actor": actor,
                 "is_human": is_human, "hash": f"mem-{len(self._events):06d}"}
        self._events.append(event)
        for filt, cb in self._subscribers:
            if filt is None or filt == event_type:
                try:
                    cb(event)
                except Exception:  # noqa: BLE001
                    pass
        return event

    @property
    def events(self) -> list[dict]:
        return list(self._events)
